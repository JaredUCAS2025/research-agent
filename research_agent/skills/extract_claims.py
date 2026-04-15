from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "extract_claims.txt"


class ExtractClaimsSkill(BaseSkill):
    name = "extract_claims"
    description = "Extract contributions, assumptions, experiments, and weaknesses."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.paper_text:
            raise ValueError("paper_text is empty")

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_prompt = f"论文标题/项目：{context.project_name}\n\n论文内容：\n{context.paper_text[:18000]}"
        context.claims = llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
        context.save_text("claims.md", context.claims)
        return SkillResult(self.name, "Claims extracted.")
