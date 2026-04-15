from __future__ import annotations

from dataclasses import dataclass

from .context import AgentContext
from .llm import LLMClient


@dataclass
class SkillResult:
    name: str
    message: str


class BaseSkill:
    name = "base"
    description = ""

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        raise NotImplementedError
