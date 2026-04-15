from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
import json
import uuid

from .config import RUNS_DIR


ProgressCallback = Callable[[str, str, float], None]


@dataclass
class AgentContext:
    project_name: str
    paper_path: Path | None = None
    paper_paths: list[Path] = field(default_factory=list)
    paper_text: str = ""
    paper_texts: list[str] = field(default_factory=list)
    paper_summaries: list[tuple[str, str]] = field(default_factory=list)
    paper_profiles: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    claims: str = ""
    outline: str = ""
    draft: str = ""
    survey: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    paper_structure: str = ""
    method_card: str = ""
    paper_digest: dict[str, Any] = field(default_factory=dict)
    compare_matrix: dict[str, Any] = field(default_factory=dict)
    comparison_report: str = ""
    repo_profile: dict[str, Any] = field(default_factory=dict)
    ast_analysis: dict[str, Any] = field(default_factory=dict)
    env_resolution: dict[str, Any] = field(default_factory=dict)
    notes: dict[str, Any] = field(default_factory=dict)
    trace: list[dict[str, Any]] = field(default_factory=list)
    progress_callback: ProgressCallback | None = None
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])

    @property
    def run_dir(self) -> Path:
        path = RUNS_DIR / self.run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_json(self, name: str, payload: dict[str, Any]) -> Path:
        output_path = self.run_dir / name
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def save_text(self, name: str, content: str) -> Path:
        output_path = self.run_dir / name
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def report_progress(self, stage: str, message: str, progress: float) -> None:
        if self.progress_callback is not None:
            self.progress_callback(stage, message, progress)

    def add_trace(self, **payload: Any) -> None:
        self.trace.append(payload)
