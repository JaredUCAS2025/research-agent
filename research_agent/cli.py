from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from .agent import ResearchAgent
from .context import AgentContext


console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Skill-based research reading and writing agent")
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")

    single_parser = subparsers.add_parser("single", help="Single paper analysis")
    single_parser.add_argument("--project", required=True, help="Project or paper name")
    single_parser.add_argument("--paper", required=True, help="Path to a .txt, .md, or .pdf paper file")

    survey_parser = subparsers.add_parser("survey", help="Multi-paper survey")
    survey_parser.add_argument("--project", required=True, help="Project or survey name")
    survey_parser.add_argument("--papers", required=True, nargs="+", help="Paths to paper files")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.mode == "single":
        paper_path = Path(args.paper).resolve()
        if not paper_path.exists():
            raise FileNotFoundError(f"Paper file not found: {paper_path}")

        context = AgentContext(project_name=args.project, paper_path=paper_path)
        agent = ResearchAgent()
        result = agent.run_single(context)

    elif args.mode == "survey":
        paper_paths = [Path(p).resolve() for p in args.papers]
        for p in paper_paths:
            if not p.exists():
                raise FileNotFoundError(f"Paper file not found: {p}")

        context = AgentContext(project_name=args.project, paper_paths=paper_paths)
        agent = ResearchAgent()
        result = agent.run_survey(context)

    else:
        build_parser().print_help()
        return

    console.print(Panel.fit(f"Run completed: {result.run_id}", title="Research Agent"))
    console.print(f"Artifacts saved to: {result.run_dir}")
    console.print("Generated files:")
    for name in ["paper_preview.txt", "summary.md", "claims.md", "outline.md", "draft.md", "survey.md", "run_manifest.json"]:
        path = result.run_dir / name
        if path.exists():
            console.print(f"- {path.name}")


if __name__ == "__main__":
    main()
