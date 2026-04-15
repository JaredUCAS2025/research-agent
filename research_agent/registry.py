"""Skill registry with metadata for harness-driven orchestration.

Each skill can declare a :class:`SkillMeta` describing its inputs, outputs,
and applicable modes.  The :class:`SkillRegistry` collects these and provides
lookup / filtering helpers used by the planner and harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseSkill
from .context import AgentContext


@dataclass
class SkillMeta:
    """Declarative metadata for a single skill."""

    name: str
    description: str
    inputs_required: list[str] = field(default_factory=list)
    outputs_produced: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    modes: list[str] = field(default_factory=list)


class SkillRegistry:
    """Central registry mapping skill names to instances + metadata."""

    def __init__(self) -> None:
        self._skills: dict[str, tuple[BaseSkill, SkillMeta]] = {}

    def register(self, skill: BaseSkill, meta: SkillMeta) -> None:
        self._skills[meta.name] = (skill, meta)

    def get(self, name: str) -> tuple[BaseSkill, SkillMeta]:
        if name not in self._skills:
            raise KeyError(f"Skill '{name}' not registered")
        return self._skills[name]

    def has(self, name: str) -> bool:
        return name in self._skills

    def all_meta(self) -> list[SkillMeta]:
        return [meta for _, meta in self._skills.values()]

    def list_available(self, context: AgentContext) -> list[SkillMeta]:
        """Return skills whose input requirements are satisfied by *context*."""
        available: list[SkillMeta] = []
        for _, meta in self._skills.values():
            if self._inputs_satisfied(meta, context):
                available.append(meta)
        return available

    def describe_for_planner(self) -> str:
        """Build a concise skill list for the LLM planner prompt."""
        lines = []
        for _, meta in self._skills.values():
            inputs = ", ".join(meta.inputs_required) or "无"
            outputs = ", ".join(meta.outputs_produced) or "无"
            lines.append(
                f"- {meta.name}：{meta.description}\n"
                f"  输入：{inputs} | 输出：{outputs}"
            )
        return "\n".join(lines)

    @staticmethod
    def _inputs_satisfied(meta: SkillMeta, context: AgentContext) -> bool:
        for field_name in meta.inputs_required:
            value = getattr(context, field_name, None)
            if value is None:
                # Check notes dict as fallback
                if field_name not in context.notes:
                    return False
            elif isinstance(value, str) and not value:
                return False
            elif isinstance(value, (dict, list)) and not value:
                return False
        return True
