from __future__ import annotations

from typing import Any
import json
import time

from openai import OpenAI

from .config import load_settings
from .prompt_stack import build_system_prompt


class LLMClient:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.enabled = bool(self.settings.openai_api_key)
        self._client = None
        self.retry_delays = (0.8, 1.6)
        self._skills: list | None = None  # set by ResearchAgent for prompt stack
        if self.enabled:
            kwargs: dict[str, Any] = {"api_key": self.settings.openai_api_key}
            if self.settings.openai_base_url:
                kwargs["base_url"] = self.settings.openai_base_url
            self._client = OpenAI(**kwargs)

    def set_skills(self, skills: list) -> None:
        """Register available skills so the prompt stack can include their descriptions."""
        self._skills = skills

    @property
    def model(self) -> str:
        return self.settings.openai_model

    @property
    def fast_model(self) -> str:
        """Return the fast model name. Falls back to the main model if not configured."""
        return self.settings.openai_fast_model or self.settings.openai_model

    def _resolve_model(self, prefer_fast: bool = False) -> str:
        """Pick the model to use for the current call."""
        if prefer_fast:
            return self.fast_model
        return self.model

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: float = 120.0,
        use_prompt_stack: bool = True,
        prefer_fast: bool = False,
    ) -> str:
        """Call the model with optional prompt-stack wrapping.

        When *use_prompt_stack* is ``True`` (default), the *system_prompt*
        is automatically wrapped with soul + skill descriptions + memory
        before being sent to the model.

        When *prefer_fast* is ``True``, uses the fast model (if configured)
        for lower-latency responses (e.g. chat, translation).
        """
        if use_prompt_stack:
            system_prompt = build_system_prompt(
                task_prompt=system_prompt,
                skills=self._skills,
            )

        active_model = self._resolve_model(prefer_fast)

        if not self.enabled or self._client is None:
            return self._offline_response(system_prompt=system_prompt, user_prompt=user_prompt)

        last_error = ""
        for attempt in range(len(self.retry_delays) + 1):
            try:
                response = self._client.chat.completions.create(
                    model=active_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=timeout,
                )
                content = response.choices[0].message.content or ""
                return content.strip()
            except Exception as e:
                last_error = str(e)
                if attempt < len(self.retry_delays):
                    time.sleep(self.retry_delays[attempt])

        return f"[API Error] {last_error}"

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: float = 120.0,
        use_prompt_stack: bool = True,
        prefer_fast: bool = False,
    ) -> dict[str, Any]:
        raw = self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            timeout=timeout,
            use_prompt_stack=use_prompt_stack,
            prefer_fast=prefer_fast,
        )
        if raw.startswith("[API Error]"):
            return {"error": raw}

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 3:
                cleaned = "\n".join(lines[1:-1]).strip()

        try:
            parsed = json.loads(cleaned)
            return parsed if isinstance(parsed, dict) else {"data": parsed}
        except json.JSONDecodeError:
            return {"raw": raw}

    def complete_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: float = 120.0,
        use_prompt_stack: bool = True,
        prefer_fast: bool = False,
    ):
        """Streaming variant of :meth:`complete`.

        Yields text chunks as they arrive from the model.  Falls back to a
        single-chunk yield when the client is offline or streaming fails.
        """
        if use_prompt_stack:
            system_prompt = build_system_prompt(
                task_prompt=system_prompt,
                skills=self._skills,
            )

        active_model = self._resolve_model(prefer_fast)

        if not self.enabled or self._client is None:
            yield self._offline_response(system_prompt=system_prompt, user_prompt=user_prompt)
            return

        try:
            stream = self._client.chat.completions.create(
                model=active_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=timeout,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception:
            # Fallback to non-streaming
            result = self.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                timeout=timeout,
                use_prompt_stack=use_prompt_stack,
                prefer_fast=prefer_fast,
            )
            yield result

    def estimate_seconds(self, stage: str, paper_count: int = 1) -> int:
        base = {
            "ingest_paper": 2,
            "paper_digest": 18,
            "outline_writer": 8,
            "draft_writer": 12,
            "paper_comparator": 16,
            "contradiction_detector": 14,
            "survey_writer": 20,
            "repo_ingestor": 6,
            "ast_analyzer": 10,
            "env_resolver": 6,
        }
        value = base.get(stage, 10)
        return value * max(paper_count, 1)

    def estimate_stage_breakdown(self, mode: str, paper_count: int = 1) -> list[dict]:
        """Return a list of ``{stage, label, seconds}`` for each step of the given mode.

        This is used by the frontend to display per-stage ETA.
        """
        if mode == "single":
            stages = [
                ("ingest_paper", "读取论文"),
                ("paper_digest", "快速理解"),
            ]
        elif mode == "survey":
            stages = [
                ("paper_digest", f"逐篇分析 ×{paper_count}"),
                ("paper_comparator", "对比矩阵"),
                ("contradiction_detector", "冲突识别"),
                ("survey_writer", "综述生成"),
            ]
        elif mode == "repo":
            stages = [
                ("repo_ingestor", "仓库扫描"),
                ("ast_analyzer", "AST 分析"),
                ("env_resolver", "依赖建议"),
            ]
        else:
            return []

        result = []
        for stage_key, label in stages:
            pc = paper_count if stage_key == "paper_digest" and mode == "survey" else 1
            result.append({
                "stage": stage_key,
                "label": label,
                "seconds": self.estimate_seconds(stage_key, pc),
            })
        return result

    def _offline_response(self, system_prompt: str, user_prompt: str) -> str:
        return (
            "[offline mode] 未检测到 OPENAI_API_KEY，因此返回本地占位结果。\n\n"
            f"System prompt:\n{system_prompt[:600]}\n\n"
            f"User prompt:\n{user_prompt[:2000]}"
        )
