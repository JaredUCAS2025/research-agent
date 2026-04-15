from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient
from ..registry import SkillMeta

SURVEY_WRITER_META = SkillMeta(
    name="survey_writer",
    description="多阶段生成高质量学术综述（分类法→演进→对比表→挑战→正文整合）",
    inputs_required=["paper_summaries"],
    outputs_produced=["survey"],
    artifacts=["survey.md", "survey_taxonomy.md", "survey_evolution.md",
               "survey_comparison_table.md", "survey_challenges.md"],
    modes=["survey"],
)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class SurveyWriterSkill(BaseSkill):
    name = "survey_writer"
    description = "Generate a high-quality multi-stage academic survey."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.paper_summaries:
            raise ValueError("paper_summaries is empty")

        # Build shared input material (with length control)
        profiles_text = self._build_profiles_text(context)
        matrix_text = str(context.compare_matrix) if context.compare_matrix else ""
        comparison_report = context.comparison_report or ""

        # Truncate to avoid exceeding model context window
        max_profiles = 12000  # ~12k chars for profiles
        max_matrix = 4000
        max_report = 4000
        if len(profiles_text) > max_profiles:
            profiles_text = profiles_text[:max_profiles] + "\n\n[... 部分内容因长度限制被截断 ...]"
        if len(matrix_text) > max_matrix:
            matrix_text = matrix_text[:max_matrix] + "\n\n[... 截断 ...]"
        if len(comparison_report) > max_report:
            comparison_report = comparison_report[:max_report] + "\n\n[... 截断 ...]"

        material_block = (
            f"项目：{context.project_name}\n"
            f"论文数量：{len(context.paper_summaries)}\n\n"
            f"论文结构化卡片：\n{profiles_text}\n\n"
            f"对比矩阵：\n{matrix_text}\n\n"
            f"冲突报告：\n{comparison_report}"
        )

        timeout = max(180.0, len(context.paper_summaries) * 30.0)  # scale with paper count

        # --- Step 1: Taxonomy ---
        context.report_progress("survey_taxonomy", "正在生成技术分类法", 0.60)
        taxonomy_prompt = self._load_prompt("survey_taxonomy.txt")
        taxonomy = llm.complete(
            system_prompt=taxonomy_prompt,
            user_prompt=material_block,
            timeout=timeout,
        )
        context.save_text("survey_taxonomy.md", taxonomy)

        # --- Step 2: Evolution timeline ---
        context.report_progress("survey_evolution", "正在梳理技术演进脉络", 0.68)
        evolution_prompt = self._load_prompt("survey_evolution.txt")
        evolution = llm.complete(
            system_prompt=evolution_prompt,
            user_prompt=f"{material_block}\n\n已生成的技术分类法：\n{taxonomy[:3000]}",
            timeout=timeout,
        )
        context.save_text("survey_evolution.md", evolution)

        # --- Step 3: Comparison table ---
        context.report_progress("survey_comparison", "正在生成核心对比表", 0.76)
        comparison_prompt = self._load_prompt("survey_comparison_table.txt")
        comparison_table = llm.complete(
            system_prompt=comparison_prompt,
            user_prompt=material_block,
            timeout=timeout,
        )
        context.save_text("survey_comparison_table.md", comparison_table)

        # --- Step 4: Open challenges ---
        context.report_progress("survey_challenges", "正在分析开放挑战与未来方向", 0.84)
        challenges_prompt = self._load_prompt("survey_challenges.txt")
        challenges = llm.complete(
            system_prompt=challenges_prompt,
            user_prompt=material_block,
            timeout=timeout,
        )
        context.save_text("survey_challenges.md", challenges)

        # --- Step 5: Integrate into full survey ---
        context.report_progress("survey_integrate", "正在整合为完整综述", 0.92)
        integrate_prompt = self._load_prompt("survey_integrate.txt")
        # For integration, use the generated sub-products (not raw material) to stay within limits
        integrate_input = (
            f"项目：{context.project_name}\n"
            f"论文数量：{len(context.paper_summaries)}\n\n"
            f"## 技术分类法\n{taxonomy[:4000]}\n\n"
            f"## 技术演进时间轴\n{evolution[:4000]}\n\n"
            f"## 核心对比表\n{comparison_table[:4000]}\n\n"
            f"## 开放挑战与未来方向\n{challenges[:4000]}"
        )
        survey = llm.complete(
            system_prompt=integrate_prompt,
            user_prompt=integrate_input,
            timeout=timeout,
        )
        context.survey = survey
        context.save_text("survey.md", survey)

        return SkillResult(self.name, "Multi-stage survey generated.")

    @staticmethod
    def _load_prompt(filename: str) -> str:
        path = _PROMPTS_DIR / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        # Fallback to legacy prompt
        fallback = _PROMPTS_DIR / "survey.txt"
        return fallback.read_text(encoding="utf-8")

    @staticmethod
    def _build_profiles_text(context: AgentContext) -> str:
        if context.paper_profiles:
            return "\n\n".join(
                f"论文 {i + 1}:\n{p.get('profile_markdown', '')}"
                for i, p in enumerate(context.paper_profiles)
            )
        # Fallback to paper_summaries
        return "\n\n".join(
            f"论文: {title}\n{summary}"
            for title, summary in context.paper_summaries
        )
