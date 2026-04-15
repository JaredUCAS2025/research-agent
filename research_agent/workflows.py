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


def research_full_graph() -> WorkflowGraph:
    """
    Complete research workflow that integrates all capabilities:
    1. GitHub search and code analysis
    2. Gap analysis and innovation proposal
    3. Experiment design and execution
    4. Ablation study
    5. Comprehensive report generation
    """
    g = WorkflowGraph(name="research_full", entry="start")

    # Start
    g.add(StateNode(name="start", node_type="start", transitions={"default": "github_search"}))

    # Phase 1: GitHub Integration
    g.add(StateNode(
        name="github_search", node_type="skill", skill_name="github_search",
        transitions={"default": "github_clone"}
    ))
    g.add(StateNode(
        name="github_clone", node_type="skill", skill_name="github_clone",
        transitions={"default": "code_analyzer"}
    ))
    g.add(StateNode(
        name="code_analyzer", node_type="skill", skill_name="enhanced_code_analyzer",
        transitions={"default": "confirm_phase1"}
    ))
    g.add(StateNode(
        name="confirm_phase1", node_type="confirm",
        confirm_message="GitHub 集成和代码分析已完成，是否继续进行创新分析？",
        transitions={"continue": "gap_analyzer", "cancel": "end"}
    ))

    # Phase 2: Innovation Design
    g.add(StateNode(
        name="gap_analyzer", node_type="skill", skill_name="gap_analyzer",
        transitions={"default": "innovation_proposer"}
    ))
    g.add(StateNode(
        name="innovation_proposer", node_type="skill", skill_name="innovation_proposer",
        transitions={"default": "confirm_phase2"}
    ))
    g.add(StateNode(
        name="confirm_phase2", node_type="confirm",
        confirm_message="创新点分析已完成，是否继续进行实验设计？",
        transitions={"continue": "experiment_designer", "cancel": "end"}
    ))

    # Phase 3: Experiment Execution
    g.add(StateNode(
        name="experiment_designer", node_type="skill", skill_name="experiment_designer",
        transitions={"default": "environment_setup"}
    ))
    g.add(StateNode(
        name="environment_setup", node_type="skill", skill_name="environment_setup",
        transitions={"default": "experiment_runner"}
    ))
    g.add(StateNode(
        name="experiment_runner", node_type="skill", skill_name="experiment_runner",
        transitions={"default": "confirm_phase3"}
    ))
    g.add(StateNode(
        name="confirm_phase3", node_type="confirm",
        confirm_message="实验执行已完成，是否继续进行消融实验？",
        transitions={"continue": "ablation_study", "cancel": "end"}
    ))

    # Phase 4: Ablation Study
    g.add(StateNode(
        name="ablation_study", node_type="skill", skill_name="ablation_study",
        transitions={"default": "confirm_phase4"}
    ))
    g.add(StateNode(
        name="confirm_phase4", node_type="confirm",
        confirm_message="消融实验已完成，是否生成综合报告？",
        transitions={"continue": "comprehensive_report", "cancel": "end"}
    ))

    # Phase 5: Report Generation
    g.add(StateNode(
        name="comprehensive_report", node_type="skill", skill_name="comprehensive_report",
        transitions={"default": "confirm_done"}
    ))
    g.add(StateNode(
        name="confirm_done", node_type="confirm",
        confirm_message="完整研究流程已完成！",
        transitions={"continue": "end", "cancel": "end"}
    ))

    # End
    g.add(StateNode(name="end", node_type="end"))

    return g


BUILTIN_GRAPHS = {
    "single": single_paper_graph,
    "survey": survey_graph,
    "repo": repo_graph,
    "auto": auto_graph,
    "research_full": research_full_graph,
}
