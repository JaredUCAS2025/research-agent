#!/usr/bin/env python
"""
Quick start example: Run multi-paper survey on sample papers.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_agent.agent import ResearchAgent
from research_agent.context import AgentContext

if __name__ == "__main__":
    workspace = ROOT / "workspace" / "inputs"
    paper_paths = [
        workspace / "sample_paper.md",
        workspace / "sample_paper_2.md",
    ]

    context = AgentContext(
        project_name="quick-start-survey",
        paper_paths=paper_paths
    )

    agent = ResearchAgent()
    result = agent.run_survey(context)

    print(f"\nSurvey completed: {result.run_id}")
    print(f"Artifacts saved to: {result.run_dir}")
    print("\nGenerated files:")
    for artifact in ["paper_1_profile.md", "paper_2_profile.md", "compare_matrix.json", "comparison_report.md", "survey.md"]:
        path = result.run_dir / artifact
        if path.exists():
            print(f"  - {artifact}")
