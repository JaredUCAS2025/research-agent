from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient
from ..registry import SkillMeta

PAPER_COMPARATOR_META = SkillMeta(
    name="paper_comparator",
    description="构建多篇论文结构化对比矩阵",
    inputs_required=["paper_profiles"],
    outputs_produced=["compare_matrix"],
    artifacts=["compare_matrix.json"],
    modes=["survey"],
)


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "compare_matrix.txt"


class PaperComparatorSkill(BaseSkill):
    name = "paper_comparator"
    description = "Build a structured comparison matrix across papers."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.paper_profiles:
            raise ValueError("paper_profiles is empty")

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        profiles_text = self._build_truncated_profiles(context.paper_profiles)
        user_prompt = f"项目：{context.project_name}\n论文数量：{len(context.paper_profiles)}\n\n论文结构化卡片：\n{profiles_text}"
        timeout = max(180.0, len(context.paper_profiles) * 20.0)
        context.compare_matrix = llm.complete_json(system_prompt=system_prompt, user_prompt=user_prompt, timeout=timeout)
        context.save_json("compare_matrix.json", context.compare_matrix)
        return SkillResult(self.name, "Comparison matrix generated.")

    @staticmethod
    def _build_truncated_profiles(profiles: list, max_per_paper: int = 1500) -> str:
        parts = []
        for i, profile in enumerate(profiles):
            text = profile.get("profile_markdown", "")
            if len(text) > max_per_paper:
                text = text[:max_per_paper] + "\n[... 截断 ...]"
            parts.append(f"论文 {i + 1}:\n{text}")
        return "\n\n".join(parts)
