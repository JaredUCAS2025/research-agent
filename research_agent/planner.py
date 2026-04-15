"""LLM-based planner for decision nodes in the workflow graph.

The planner is invoked only at ``decision`` nodes.  It receives a condensed
snapshot of the current execution state and the allowed transitions, then
asks the LLM to pick one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .context import AgentContext
from .graph import StateNode
from .llm import LLMClient
from .registry import SkillRegistry

PLANNER_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "planner.txt"


def _list_nonempty_fields(context: AgentContext) -> list[str]:
    """Return names of AgentContext fields that have meaningful content."""
    fields = [
        "paper_text", "paper_texts", "paper_summaries", "paper_profiles",
        "summary", "claims", "outline", "draft", "survey",
        "metadata", "paper_structure", "method_card", "paper_digest",
        "compare_matrix", "comparison_report",
        "repo_profile", "ast_analysis", "env_resolution",
    ]
    result = []
    for name in fields:
        value = getattr(context, name, None)
        if value:
            result.append(name)
    # Also check notes for repo_path
    if context.notes.get("repo_path"):
        result.append("repo_path")
    return result


def build_planner_context(
    context: AgentContext,
    node: StateNode,
    registry: SkillRegistry,
) -> str:
    """Build the user prompt for the planner LLM call."""
    completed = [t.get("skill", "?") for t in context.trace]
    nonempty = _list_nonempty_fields(context)
    transitions_json = json.dumps(node.transitions, ensure_ascii=False)

    has_paper = bool(context.paper_path)
    has_papers = bool(context.paper_paths)
    has_repo = bool(context.notes.get("repo_path"))

    return (
        f"当前任务：{context.project_name}\n"
        f"当前决策节点：{node.name}\n"
        f"已完成步骤：{completed}\n"
        f"已有产物：{nonempty}\n"
        f"输入情况：paper_path={'有' if has_paper else '无'}, "
        f"paper_paths={len(context.paper_paths)}篇, "
        f"repo_path={'有' if has_repo else '无'}\n"
        f"可选转移：{transitions_json}\n"
    )


def plan_decision(
    node: StateNode,
    context: AgentContext,
    registry: SkillRegistry,
    llm: LLMClient,
) -> str:
    """Ask the LLM to choose a transition at a decision node.

    Returns the chosen transition label (a key in ``node.transitions``).
    Falls back to the first available transition if the LLM response
    cannot be parsed.
    """
    system_prompt = PLANNER_PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = build_planner_context(context, node, registry)

    result = llm.complete_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        prefer_fast=True,
        timeout=30.0,
    )

    choice = result.get("choice", "")
    if choice in node.transitions:
        return choice

    # Fallback: pick the first valid transition
    return next(iter(node.transitions))
