from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "summarize.txt"


class SummarizePaperSkill(BaseSkill):
    name = "summarize_paper"
    description = "Generate a structured summary of the paper."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.paper_text:
            raise ValueError("paper_text is empty")

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_prompt = f"论文标题/项目：{context.project_name}\n\n论文内容：\n{context.paper_text[:18000]}"
        context.summary = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        context.save_text("summary.md", context.summary)
        return SkillResult(self.name, "Structured summary generated.")
