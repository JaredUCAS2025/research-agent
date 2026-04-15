from __future__ import annotations

from pathlib import Path

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient
from ..registry import SkillMeta

INGEST_PAPER_META = SkillMeta(
    name="ingest_paper",
    description="读取论文原文（支持 txt/md/pdf）",
    inputs_required=["paper_path"],
    outputs_produced=["paper_text"],
    artifacts=["paper_preview.txt"],
    modes=["single", "survey"],
)


class IngestPaperSkill(BaseSkill):
    name = "ingest_paper"
    description = "Load paper text from a local txt, markdown, or PDF file."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        if context.paper_path is None:
            raise ValueError("paper_path is required")

        suffix = context.paper_path.suffix.lower()
        if suffix == ".pdf":
            context.paper_text = self._extract_pdf(context.paper_path)
        elif suffix in {".txt", ".md"}:
            context.paper_text = context.paper_path.read_text(encoding="utf-8")
        else:
            raise ValueError("Only .txt, .md, and .pdf are supported")

        preview = context.paper_text[:500]
        context.save_text("paper_preview.txt", preview)
        return SkillResult(self.name, f"Loaded paper with {len(context.paper_text)} characters.")

    @staticmethod
    def _extract_pdf(pdf_path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("pypdf is required for PDF support. Install with: pip install pypdf")

        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
