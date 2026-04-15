from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "paper_structure.txt"


class PaperStructureSkill(BaseSkill):
    name = "paper_structure"
    description = "Extract the paper's logical structure."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.paper_text:
            raise ValueError("paper_text is empty")

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_prompt = f"项目：{context.project_name}\n\n论文内容：\n{context.paper_text[:18000]}"
        context.paper_structure = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        context.save_text("paper_structure.md", context.paper_structure)
        return SkillResult(self.name, "Paper structure extracted.")
