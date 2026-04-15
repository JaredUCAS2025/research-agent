from __future__ import annotations

from pathlib import Path
from typing import Any

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient
from ..registry import SkillMeta

PAPER_DIGEST_META = SkillMeta(
    name="paper_digest",
    description="一次性提取论文核心信息（元信息、摘要、关键结论、结构、方法卡片）",
    inputs_required=["paper_text"],
    outputs_produced=["metadata", "summary", "claims", "paper_structure", "method_card", "paper_digest"],
    artifacts=["paper_digest.json", "paper_metadata.json", "summary.md", "claims.md", "paper_structure.md", "method_card.md"],
    modes=["single", "survey"],
)


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "paper_digest.txt"


class PaperDigestSkill(BaseSkill):
    name = "paper_digest"
    description = "Generate a compact structured reading digest in one model call."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.paper_text:
            raise ValueError("paper_text is empty")

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_prompt = f"项目：{context.project_name}\n\n论文内容：\n{context.paper_text[:20000]}"
        payload = llm.complete_json(system_prompt=system_prompt, user_prompt=user_prompt, timeout=150.0)

        metadata = payload.get("metadata")
        context.metadata = metadata if isinstance(metadata, dict) else {}
        context.summary = self._get_text(payload, "summary_markdown")
        context.claims = self._get_text(payload, "claims_markdown")
        context.paper_structure = self._get_text(payload, "structure_markdown")
        context.method_card = self._get_text(payload, "method_card_markdown")
        context.paper_digest = payload

        context.save_json("paper_digest.json", payload)
        context.save_json("paper_metadata.json", context.metadata)
        context.save_text("summary.md", context.summary)
        context.save_text("summary_translated.md", context.summary)
        context.save_text("claims.md", context.claims)
        context.save_text("paper_structure.md", context.paper_structure)
        context.save_text("method_card.md", context.method_card)
        return SkillResult(self.name, "Paper digest generated.")

    @staticmethod
    def _get_text(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key, "")
        return value if isinstance(value, str) else ""
