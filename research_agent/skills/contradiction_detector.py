from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient
from ..registry import SkillMeta

CONTRADICTION_DETECTOR_META = SkillMeta(
    name="contradiction_detector",
    description="生成多篇论文的冲突与差异分析报告",
    inputs_required=["paper_profiles", "compare_matrix"],
    outputs_produced=["comparison_report"],
    artifacts=["comparison_report.md"],
    modes=["survey"],
)


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "paper_compare.txt"


class ContradictionDetectorSkill(BaseSkill):
    name = "contradiction_detector"
    description = "Generate a contradiction and comparison report across papers."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.paper_profiles:
            raise ValueError("paper_profiles is empty")

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        profiles_text = self._build_truncated_profiles(context.paper_profiles)
        matrix_text = str(context.compare_matrix)
        if len(matrix_text) > 4000:
            matrix_text = matrix_text[:4000] + "\n[... 截断 ...]"
        user_prompt = (
            f"项目：{context.project_name}\n"
            f"论文数量：{len(context.paper_profiles)}\n\n"
            f"对比矩阵：\n{matrix_text}\n\n"
            f"论文结构化卡片：\n{profiles_text}"
        )
        timeout = max(180.0, len(context.paper_profiles) * 20.0)
        context.comparison_report = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt, timeout=timeout)
        context.save_text("comparison_report.md", context.comparison_report)
        return SkillResult(self.name, "Comparison report generated.")

    @staticmethod
    def _build_truncated_profiles(profiles: list, max_per_paper: int = 1500) -> str:
        parts = []
        for i, profile in enumerate(profiles):
            text = profile.get("profile_markdown", "")
            if len(text) > max_per_paper:
                text = text[:max_per_paper] + "\n[... 截断 ...]"
            parts.append(f"论文 {i + 1}:\n{text}")
        return "\n\n".join(parts)
