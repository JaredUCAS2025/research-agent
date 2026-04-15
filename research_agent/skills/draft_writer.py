from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "draft.txt"


class DraftWriterSkill(BaseSkill):
    name = "draft_writer"
    description = "Draft a first-pass research writing artifact."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_prompt = (
            f"项目：{context.project_name}\n\n"
            f"摘要：\n{context.summary}\n\n"
            f"关键信息：\n{context.claims}\n\n"
            f"大纲：\n{context.outline}"
        )
        context.draft = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        context.save_text("draft.md", context.draft)
        return SkillResult(self.name, "Draft generated.")
