"""State graph data structures for workflow orchestration.

A workflow is defined as a directed graph of :class:`StateNode` objects.
Each node has a type that determines how the harness processes it:

- ``start``   — entry point, immediately transitions
- ``skill``   — executes a registered skill, then follows the default transition
- ``batch``   — executes a skill for each item in a list (e.g. per-paper digest)
- ``decision``— asks the LLM planner to choose among allowed transitions
- ``confirm`` — pauses execution and waits for user confirmation
- ``end``     — terminal node, finalises the run
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StateNode:
    """A single node in a workflow graph."""

    name: str
    node_type: str  # "start" | "skill" | "batch" | "decision" | "confirm" | "end"
    skill_name: str | None = None
    transitions: dict[str, str] = field(default_factory=dict)
    confirm_message: str = ""
    # batch node config
    batch_items_field: str = ""  # AgentContext field holding the list to iterate
    batch_skill_names: list[str] = field(default_factory=list)  # skills to run per item

    def __post_init__(self) -> None:
        if self.node_type == "skill" and not self.skill_name:
            raise ValueError(f"Skill node '{self.name}' must specify skill_name")
        if self.node_type == "batch" and not self.batch_skill_names:
            raise ValueError(f"Batch node '{self.name}' must specify batch_skill_names")


@dataclass
class WorkflowGraph:
    """A complete workflow definition."""

    name: str
    nodes: dict[str, StateNode] = field(default_factory=dict)
    entry: str = "start"

    def add(self, node: StateNode) -> None:
        self.nodes[node.name] = node

    def validate(self) -> list[str]:
        """Return a list of validation errors (empty means valid)."""
        errors: list[str] = []
        if self.entry not in self.nodes:
            errors.append(f"Entry node '{self.entry}' not found in graph")
        for node in self.nodes.values():
            for label, target in node.transitions.items():
                if target not in self.nodes:
                    errors.append(
                        f"Node '{node.name}' transition '{label}' -> "
                        f"'{target}' references missing node"
                    )
        return errors
