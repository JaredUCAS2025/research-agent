"""Built-in workflow graph definitions.

Each function returns a :class:`WorkflowGraph` that the harness can execute.
"""

from __future__ import annotations

from .graph import StateNode, WorkflowGraph


def single_paper_graph() -> WorkflowGraph:
    """Single-paper fast analysis: ingest → digest → confirm → end."""
    g = WorkflowGraph(name="single", entry="start")
    g.add(StateNode(name="start", node_type="start", transitions={"default": "ingest"}))
    g.add(StateNode(
        name="ingest", node_type="skill", skill_name="ingest_paper",
        transitions={"default": "digest"},
    ))
    g.add(StateNode(
        name="digest", node_type="skill", skill_name="paper_digest",
        transitions={"default": "confirm_done"},
    ))
    g.add(StateNode(
        name="confirm_done", node_type="confirm",
        confirm_message="单论文分析已完成，是否继续？",
        transitions={"continue": "end", "cancel": "end"},
    ))
    g.add(StateNode(name="end", node_type="end"))
    return g


def survey_graph() -> WorkflowGraph:
    """Multi-paper survey: batch digest → confirm → compare → contradiction → survey → confirm → end."""
    g = WorkflowGraph(name="survey", entry="start")
    g.add(StateNode(name="start", node_type="start", transitions={"default": "per_paper_digest"}))
    g.add(StateNode(
        name="per_paper_digest", node_type="batch",
        batch_items_field="paper_paths",
        batch_skill_names=["ingest_paper", "paper_digest"],
        transitions={"default": "confirm_aggregation"},
    ))
    g.add(StateNode(
        name="confirm_aggregation", node_type="confirm",
        confirm_message="所有论文已完成快速分析，即将进入多论文聚合阶段（对比矩阵、冲突识别、综述生成）。是否继续？",
        transitions={"continue": "comparator", "cancel": "end"},
    ))
    g.add(StateNode(
        name="comparator", node_type="skill", skill_name="paper_comparator",
        transitions={"default": "contradiction"},
    ))
    g.add(StateNode(
        name="contradiction", node_type="skill", skill_name="contradiction_detector",
        transitions={"default": "survey_writer"},
    ))
    g.add(StateNode(
        name="survey_writer", node_type="skill", skill_name="survey_writer",
        transitions={"default": "confirm_done"},
    ))
    g.add(StateNode(
        name="confirm_done", node_type="confirm",
        confirm_message="多论文综述已完成，是否继续？",
        transitions={"continue": "end", "cancel": "end"},
    ))
    g.add(StateNode(name="end", node_type="end"))
    return g


def repo_graph() -> WorkflowGraph:
    """Repository analysis: repo_ingest → ast_analyze → env_resolve → confirm → end."""
    g = WorkflowGraph(name="repo", entry="start")
    g.add(StateNode(name="start", node_type="start", transitions={"default": "repo_ingest"}))
    g.add(StateNode(
        name="repo_ingest", node_type="skill", skill_name="repo_ingestor",
        transitions={"default": "ast_analyze"},
    ))
    g.add(StateNode(
        name="ast_analyze", node_type="skill", skill_name="ast_analyzer",
        transitions={"default": "env_resolve"},
    ))
    g.add(StateNode(
        name="env_resolve", node_type="skill", skill_name="env_resolver",
        transitions={"default": "confirm_done"},
    ))
    g.add(StateNode(
        name="confirm_done", node_type="confirm",
        confirm_message="仓库分析已完成，是否继续？",
        transitions={"continue": "end", "cancel": "end"},
    ))
    g.add(StateNode(name="end", node_type="end"))
    return g


def auto_graph() -> WorkflowGraph:
    """Auto-routing graph: LLM decides the workflow based on user input."""
    g = WorkflowGraph(name="auto", entry="start")
    g.add(StateNode(name="start", node_type="start", transitions={"default": "decide_mode"}))

    # Decision: what mode?
    g.add(StateNode(
        name="decide_mode", node_type="decision",
        transitions={"single": "ingest", "survey": "batch_digest", "repo": "repo_ingest"},
    ))

    # Single paper branch
    g.add(StateNode(name="ingest", node_type="skill", skill_name="ingest_paper", transitions={"default": "digest"}))
    g.add(StateNode(name="digest", node_type="skill", skill_name="paper_digest", transitions={"default": "confirm_done"}))

    # Survey branch
    g.add(StateNode(
        name="batch_digest", node_type="batch",
        batch_items_field="paper_paths", batch_skill_names=["ingest_paper", "paper_digest"],
        transitions={"default": "confirm_agg"},
    ))
    g.add(StateNode(
        name="confirm_agg", node_type="confirm",
        confirm_message="逐篇分析完成，即将进入聚合阶段。是否继续？",
        transitions={"continue": "comparator", "cancel": "end"},
    ))
    g.add(StateNode(name="comparator", node_type="skill", skill_name="paper_comparator", transitions={"default": "contradiction"}))
    g.add(StateNode(name="contradiction", node_type="skill", skill_name="contradiction_detector", transitions={"default": "survey_w"}))
    g.add(StateNode(name="survey_w", node_type="skill", skill_name="survey_writer", transitions={"default": "confirm_done"}))

    # Repo branch
    g.add(StateNode(name="repo_ingest", node_type="skill", skill_name="repo_ingestor", transitions={"default": "ast_analyze"}))
    g.add(StateNode(name="ast_analyze", node_type="skill", skill_name="ast_analyzer", transitions={"default": "env_resolve"}))
    g.add(StateNode(name="env_resolve", node_type="skill", skill_name="env_resolver", transitions={"default": "confirm_done"}))

    # Shared terminal
    g.add(StateNode(
        name="confirm_done", node_type="confirm",
        confirm_message="分析已完成，是否继续？",
        transitions={"continue": "end", "cancel": "end"},
    ))
    g.add(StateNode(name="end", node_type="end"))
    return g


BUILTIN_GRAPHS = {
    "single": single_paper_graph,
    "survey": survey_graph,
    "repo": repo_graph,
    "auto": auto_graph,
}
