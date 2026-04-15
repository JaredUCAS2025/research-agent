from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "method_card.txt"


class MethodCardSkill(BaseSkill):
    name = "method_card"
    description = "Build a structured method card for the current paper."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.paper_text:
            raise ValueError("paper_text is empty")

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_prompt = (
            f"项目：{context.project_name}\n\n"
            f"论文元信息：\n{context.metadata}\n\n"
            f"摘要：\n{context.summary}\n\n"
            f"关键信息：\n{context.claims}\n\n"
            f"论文内容：\n{context.paper_text[:12000]}"
        )
        context.method_card = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        context.save_text("method_card.md", context.method_card)
        return SkillResult(self.name, "Method card generated.")
