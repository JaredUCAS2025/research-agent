"""System prompt stack loader.

Assembles the runtime system prompt from soul.md, skill descriptions,
and memory.md — similar to the OpenClaw-style prompt stack pattern.
"""

from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent

SOUL_PATH = _PACKAGE_DIR / "soul.md"
MEMORY_PATH = _PACKAGE_DIR / "memory.md"


def _read_if_exists(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def load_soul() -> str:
    """Load the soul (identity/persona) definition."""
    return _read_if_exists(SOUL_PATH)


def load_memory() -> str:
    """Load the persistent memory (user preferences & rules)."""
    return _read_if_exists(MEMORY_PATH)


def load_skill_descriptions(skills: list | None = None) -> str:
    """Build a summary of available skills for context.

    If *skills* is provided, each item should have `name` and `description`
    attributes (i.e. :class:`BaseSkill` instances).
    """
    if not skills:
        return ""
    lines = ["## 当前可用 Skills"]
    for skill in skills:
        lines.append(f"- **{skill.name}**：{skill.description}")
    return "\n".join(lines)


def build_system_prompt(
    task_prompt: str,
    skills: list | None = None,
    include_soul: bool = True,
    include_memory: bool = True,
) -> str:
    """Assemble the full system prompt stack.

    Stack order (top → bottom):
      1. Soul  — identity, tone, behaviour boundaries
      2. Skills — available skill descriptions
      3. Memory — user preferences and persistent rules
      4. Task prompt — the specific skill/task system prompt

    Parameters
    ----------
    task_prompt:
        The skill-specific system prompt text.
    skills:
        Optional list of :class:`BaseSkill` instances (used for skill
        description summary).
    include_soul:
        Whether to prepend the soul block.
    include_memory:
        Whether to append the memory block.
    """
    sections: list[str] = []

    if include_soul:
        soul = load_soul()
        if soul:
            sections.append(soul)

    skill_desc = load_skill_descriptions(skills)
    if skill_desc:
        sections.append(skill_desc)

    if include_memory:
        memory = load_memory()
        if memory:
            sections.append(memory)

    if task_prompt:
        sections.append(task_prompt)

    return "\n\n---\n\n".join(sections)
