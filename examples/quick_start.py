#!/usr/bin/env python
"""
Quick start example: Run single-paper analysis on sample paper.
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
    paper_path = workspace / "sample_paper.md"
    
    context = AgentContext(
        project_name="quick-start-example",
        paper_path=paper_path
    )
    
    agent = ResearchAgent()
    result = agent.run_single(context)
    
    print(f"\nRun completed: {result.run_id}")
    print(f"Artifacts saved to: {result.run_dir}")
    print("\nGenerated files:")
    for artifact in [
        "paper_digest.json",
        "paper_metadata.json",
        "summary.md",
        "claims.md",
        "paper_structure.md",
        "method_card.md",
    ]:
        path = result.run_dir / artifact
        if path.exists():
            print(f"  - {artifact}")
