from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "translate.txt"


class TranslateSkill(BaseSkill):
    name = "translate"
    description = "Translate content to Chinese if needed."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.summary:
            return SkillResult(self.name, "No content to translate.")

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_prompt = f"内容：\n{context.summary}"
        
        context.summary = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        context.save_text("summary_translated.md", context.summary)
        return SkillResult(self.name, "Content translated to Chinese.")
