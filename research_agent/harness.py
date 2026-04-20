"""Harness: LLM-driven workflow executor.

The :class:`Harness` walks a :class:`WorkflowGraph`, executing skills at
``skill`` nodes, asking the LLM planner at ``decision`` nodes, and pausing
for user confirmation at ``confirm`` nodes.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .context import AgentContext
from .graph import StateNode, WorkflowGraph
from .llm import LLMClient
from .planner import plan_decision
from .registry import SkillRegistry


class AwaitConfirmation(Exception):
    """Raised when the harness reaches a confirm node and needs user input."""

    def __init__(self, node_name: str, message: str) -> None:
        self.node_name = node_name
        self.message = message
        super().__init__(message)


@dataclass
class HarnessState:
    """Mutable execution state tracked across the harness run."""

    current_node: str = ""
    status: str = "idle"  # idle | running | awaiting_confirmation | completed | failed | cancelled
    decisions: list[dict[str, Any]] = field(default_factory=list)
    step_count: int = 0
    max_steps: int = 50  # safety limit


class Harness:
    """Walk a workflow graph, dispatching skills and LLM decisions."""

    def __init__(
        self,
        graph: WorkflowGraph,
        registry: SkillRegistry,
        context: AgentContext,
        llm: LLMClient,
    ) -> None:
        self.graph = graph
        self.registry = registry
        self.context = context
        self.llm = llm
        self.state = HarnessState(current_node=graph.entry, status="running")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> AgentContext:
        """Execute the graph from the current node.

        Raises :class:`AwaitConfirmation` when a ``confirm`` node is reached.
        The caller should later invoke :meth:`resume` to continue.
        """
        self.state.status = "running"
        print(f"\n{'='*80}")
        print(f"🚀 Harness starting workflow: {self.graph.name}")
        print(f"{'='*80}")

        while True:
            if self.state.step_count >= self.state.max_steps:
                self.state.status = "failed"
                raise RuntimeError(f"Harness exceeded max steps ({self.state.max_steps})")

            node = self.graph.nodes[self.state.current_node]
            print(f"\n➡️  Step {self.state.step_count}: Node '{self.state.current_node}' (type: {node.node_type})")

            # --- terminal ---
            if node.node_type == "end":
                print(f"🏁 Reached end node, finalizing...")
                self._finalize()
                break

            # --- start: just follow default transition ---
            if node.node_type == "start":
                next_node = node.transitions["default"]
                print(f"   Start node → {next_node}")
                self.state.current_node = next_node
                self.state.step_count += 1
                continue

            # --- confirm: pause for user ---
            if node.node_type == "confirm":
                print(f"⏸️  Confirm node reached: {node.confirm_message}")
                self.state.status = "awaiting_confirmation"
                self.context.add_trace(
                    harness="confirm", node=node.name, message=node.confirm_message,
                )
                raise AwaitConfirmation(node.name, node.confirm_message)

            # --- skill: execute one skill ---
            if node.node_type == "skill":
                self._execute_skill(node)
                next_node = node.transitions["default"]
                print(f"   Skill completed → {next_node}")
                self.state.current_node = next_node

            # --- batch: execute skills for each item in a list ---
            elif node.node_type == "batch":
                self._execute_batch(node)
                next_node = node.transitions["default"]
                print(f"   Batch completed → {next_node}")
                self.state.current_node = next_node

            # --- decision: ask LLM planner ---
            elif node.node_type == "decision":
                choice = plan_decision(node, self.context, self.registry, self.llm)
                self.state.decisions.append({
                    "node": node.name,
                    "choice": choice,
                    "step": self.state.step_count,
                })
                self.context.add_trace(
                    harness="decision", node=node.name, choice=choice,
                )
                next_node = node.transitions[choice]
                print(f"   Decision: {choice} → {next_node}")
                self.state.current_node = next_node

            self.state.step_count += 1
            self._check_cancelled()

        return self.context

    def resume(self, user_choice: str | None = None) -> AgentContext:
        """Continue execution after a confirm node.

        Parameters
        ----------
        user_choice:
            The user's selection — typically ``"continue"`` or ``"cancel"``.
            Defaults to ``"continue"`` if *None*.
        """
        node = self.graph.nodes[self.state.current_node]
        if node.node_type != "confirm":
            raise RuntimeError(f"Cannot resume: current node '{node.name}' is not a confirm node")

        choice = user_choice or "continue"
        if choice == "cancel":
            self.state.status = "cancelled"
            self.context.add_trace(harness="cancelled", node=node.name)
            return self.context

        target = node.transitions.get(choice)
        if not target:
            target = node.transitions.get("continue", next(iter(node.transitions.values())))

        self.context.add_trace(harness="confirmed", node=node.name, choice=choice)
        self.state.current_node = target
        self.state.step_count += 1
        return self.run()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _execute_skill(self, node: StateNode) -> None:
        """Run a single skill node."""
        skill, meta = self.registry.get(node.skill_name)
        print(f"\n🔧 Harness executing skill: {node.skill_name}")
        total = self._count_skill_nodes()
        progress = min(self.state.step_count / max(total, 1), 0.98)
        self.context.report_progress(skill.name, f"正在执行 {skill.name}", progress)
        result = skill.run(context=self.context, llm=self.llm)
        print(f"✅ Skill {node.skill_name} completed: {result.message}")
        self.context.add_trace(
            harness="skill", skill=result.name, message=result.message,
            step=self.state.step_count,
        )

    def _execute_batch(self, node: StateNode) -> None:
        """Run a batch node: execute skill chain for each item concurrently."""
        items = getattr(self.context, node.batch_items_field, [])
        if not items:
            return

        item_count = len(items)

        def _process_one(index: int, item: Any) -> dict[str, Any]:
            sub_ctx = AgentContext(
                project_name=self.context.project_name,
                paper_path=item if isinstance(item, Path) else Path(str(item)),
                run_id=self.context.run_id,
            )
            for skill_name in node.batch_skill_names:
                skill, _ = self.registry.get(skill_name)
                result = skill.run(context=sub_ctx, llm=self.llm)
                self.context.add_trace(
                    harness="batch_skill", skill=result.name,
                    message=result.message, batch_index=index, batch_total=item_count,
                )
            return {
                "index": index,
                "item": item,
                "sub_ctx": sub_ctx,
            }

        max_workers = min(item_count, 4)
        results_by_index: dict[int, dict] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(_process_one, idx, item): idx
                for idx, item in enumerate(items, start=1)
            }
            done_count = 0
            for future in as_completed(futures):
                done_count += 1
                res = future.result()
                results_by_index[res["index"]] = res
                progress = done_count / (item_count + 1)
                self.context.report_progress(
                    "batch", f"已完成第 {done_count}/{item_count} 项", progress,
                )

        # Assemble results in order
        for idx in sorted(results_by_index.keys()):
            res = results_by_index[idx]
            sub_ctx = res["sub_ctx"]
            profile = self._paper_profile(sub_ctx)
            self.context.paper_summaries.append(
                (res["item"].stem if isinstance(res["item"], Path) else str(res["item"]), profile["profile_markdown"])
            )
            self.context.paper_profiles.append(profile)
            self.context.save_text(f"paper_{idx}_profile.md", profile["profile_markdown"])
            self.context.save_json(f"paper_{idx}_profile.json", profile)

    def _finalize(self) -> None:
        """Write run manifest and mark completed."""
        manifest = {
            "mode": self.graph.name,
            "project_name": self.context.project_name,
            "run_id": self.context.run_id,
            "trace": self.context.trace,
            "harness_decisions": self.state.decisions,
            "harness_steps": self.state.step_count,
        }
        self.context.save_json("run_manifest.json", manifest)
        self.state.status = "completed"
        self.context.report_progress("completed", "任务完成", 1.0)

    def _check_cancelled(self) -> None:
        if self.state.status == "cancelled":
            raise InterruptedError("Harness cancelled")

    def _count_skill_nodes(self) -> int:
        return sum(1 for n in self.graph.nodes.values() if n.node_type in ("skill", "batch"))

    @staticmethod
    def _paper_profile(ctx: AgentContext) -> dict[str, Any]:
        title = ctx.metadata.get("title") or ctx.project_name
        profile = {
            "title": title,
            "metadata": ctx.metadata,
            "summary": ctx.summary,
            "claims": ctx.claims,
            "paper_structure": ctx.paper_structure,
            "method_card": ctx.method_card,
            "paper_digest": ctx.paper_digest,
        }
        profile["profile_markdown"] = (
            f"# {title}\n\n"
            f"## 元信息\n{ctx.metadata}\n\n"
            f"## 摘要\n{ctx.summary}\n\n"
            f"## 关键信息\n{ctx.claims}\n\n"
            f"## 论文结构\n{ctx.paper_structure}\n\n"
            f"## 方法卡片\n{ctx.method_card}"
        )
        return profile
