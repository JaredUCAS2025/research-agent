from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient


PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "paper_metadata.txt"


class PaperMetadataSkill(BaseSkill):
    name = "paper_metadata"
    description = "Extract structured metadata from the paper."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if not context.paper_text:
            raise ValueError("paper_text is empty")

        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
        user_prompt = f"项目：{context.project_name}\n\n论文内容：\n{context.paper_text[:16000]}"
        context.metadata = llm.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
        context.save_json("paper_metadata.json", context.metadata)
        return SkillResult(self.name, "Paper metadata extracted.")
