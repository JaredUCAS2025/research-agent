from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .base import BaseSkill
from .context import AgentContext
from .graph import WorkflowGraph
from .harness import AwaitConfirmation, Harness
from .llm import LLMClient
from .registry import SkillMeta, SkillRegistry
from .skills.contradiction_detector import ContradictionDetectorSkill, CONTRADICTION_DETECTOR_META
from .skills.ingest_paper import IngestPaperSkill, INGEST_PAPER_META
from .skills.paper_comparator import PaperComparatorSkill, PAPER_COMPARATOR_META
from .skills.paper_digest import PaperDigestSkill, PAPER_DIGEST_META
from .skills.repo_skills import (
    ASTAnalyzerSkill, AST_ANALYZER_META,
    EnvResolverSkill, ENV_RESOLVER_META,
    RepoIngestorSkill, REPO_INGESTOR_META,
)
from .skills.survey_writer import SurveyWriterSkill, SURVEY_WRITER_META
# New enhanced skills
from .skills.github_search import GitHubSearchSkill, SKILL_META as GITHUB_SEARCH_META
from .skills.github_clone import GitHubCloneSkill, SKILL_META as GITHUB_CLONE_META
from .skills.enhanced_code_analyzer import EnhancedCodeAnalyzerSkill, SKILL_META as ENHANCED_CODE_ANALYZER_META
from .skills.gap_analyzer import GapAnalyzerSkill, SKILL_META as GAP_ANALYZER_META
from .skills.innovation_proposer import InnovationProposerSkill, SKILL_META as INNOVATION_PROPOSER_META
from .skills.experiment_designer import ExperimentDesignerSkill, SKILL_META as EXPERIMENT_DESIGNER_META
from .skills.environment_setup import EnvironmentSetupSkill, SKILL_META as ENVIRONMENT_SETUP_META
from .skills.experiment_runner import ExperimentRunnerSkill, SKILL_META as EXPERIMENT_RUNNER_META
from .skills.ablation_study import AblationStudySkill, SKILL_META as ABLATION_STUDY_META
from .skills.comprehensive_report import ComprehensiveReportSkill, SKILL_META as COMPREHENSIVE_REPORT_META
from .skills.diagram_generator import DiagramGeneratorSkill, SKILL_META as DIAGRAM_GENERATOR_META
from .skills.ai_image_generator import AIImageGeneratorSkill, SKILL_META as AI_IMAGE_GENERATOR_META
from .workflows import BUILTIN_GRAPHS


class ResearchAgent:
    def __init__(self) -> None:
        self.llm = LLMClient()
        self.single_paper_skills: list[BaseSkill] = [
            IngestPaperSkill(),
            PaperDigestSkill(),
            DiagramGeneratorSkill(),
        ]
        self.multi_paper_skills: list[BaseSkill] = [
            PaperComparatorSkill(),
            ContradictionDetectorSkill(),
            SurveyWriterSkill(),
            DiagramGeneratorSkill(),
        ]
        self.repo_skills: list[BaseSkill] = [
            RepoIngestorSkill(),
            ASTAnalyzerSkill(),
            EnvResolverSkill(),
        ]
        # Register all skills with the LLM so the prompt stack can list them
        all_skills = self.single_paper_skills + self.multi_paper_skills + self.repo_skills
        self.llm.set_skills(all_skills)

        # --- Skill Registry for harness mode ---
        self.registry = SkillRegistry()
        _skill_meta_pairs = [
            # Original skills
            (IngestPaperSkill(), INGEST_PAPER_META),
            (PaperDigestSkill(), PAPER_DIGEST_META),
            (PaperComparatorSkill(), PAPER_COMPARATOR_META),
            (ContradictionDetectorSkill(), CONTRADICTION_DETECTOR_META),
            (SurveyWriterSkill(), SURVEY_WRITER_META),
            (RepoIngestorSkill(), REPO_INGESTOR_META),
            (ASTAnalyzerSkill(), AST_ANALYZER_META),
            (EnvResolverSkill(), ENV_RESOLVER_META),
            # New enhanced skills
            (GitHubSearchSkill(), GITHUB_SEARCH_META),
            (GitHubCloneSkill(), GITHUB_CLONE_META),
            (EnhancedCodeAnalyzerSkill(), ENHANCED_CODE_ANALYZER_META),
            (GapAnalyzerSkill(), GAP_ANALYZER_META),
            (InnovationProposerSkill(), INNOVATION_PROPOSER_META),
            (ExperimentDesignerSkill(), EXPERIMENT_DESIGNER_META),
            (EnvironmentSetupSkill(), ENVIRONMENT_SETUP_META),
            (ExperimentRunnerSkill(), EXPERIMENT_RUNNER_META),
            (AblationStudySkill(), ABLATION_STUDY_META),
            (ComprehensiveReportSkill(), COMPREHENSIVE_REPORT_META),
            # Visualization skills
            (DiagramGeneratorSkill(), DIAGRAM_GENERATOR_META),
            (AIImageGeneratorSkill(), AI_IMAGE_GENERATOR_META),
        ]
        for skill_inst, meta in _skill_meta_pairs:
            self.registry.register(skill_inst, meta)

    # ------------------------------------------------------------------
    # Harness mode
    # ------------------------------------------------------------------

    def run_with_harness(self, mode: str, context: AgentContext) -> Harness:
        """Create and start a harness for the given workflow mode.

        Returns the :class:`Harness` instance.  If the harness reaches a
        ``confirm`` node, it raises :class:`AwaitConfirmation` — the caller
        should catch it, wait for user input, then call ``harness.resume()``.

        Parameters
        ----------
        mode:
            One of ``"single"``, ``"survey"``, ``"repo"``, ``"auto"``.
        context:
            The :class:`AgentContext` to operate on.
        """
        graph_factory = BUILTIN_GRAPHS.get(mode)
        if graph_factory is None:
            raise ValueError(f"Unknown workflow mode: {mode}")
        graph = graph_factory()
        harness = Harness(graph=graph, registry=self.registry, context=context, llm=self.llm)
        harness.run()  # may raise AwaitConfirmation
        return harness

    def run_single(self, context: AgentContext) -> AgentContext:
        total_steps = len(self.single_paper_skills)
        for index, skill in enumerate(self.single_paper_skills, start=1):
            context.report_progress(skill.name, f"正在执行 {skill.name}", index / (total_steps + 1))
            result = skill.run(context=context, llm=self.llm)
            context.add_trace(skill=result.name, message=result.message, step=index, total_steps=total_steps)

        manifest = {
            "mode": "single",
            "project_name": context.project_name,
            "paper_path": str(context.paper_path) if context.paper_path else None,
            "run_id": context.run_id,
            "trace": context.trace,
            "artifacts": self._artifact_payload(context),
        }
        context.save_json("run_manifest.json", manifest)
        context.report_progress("completed", "单论文分析完成", 1.0)
        return context

    def run_survey(self, context: AgentContext) -> AgentContext:
        paper_count = max(len(context.paper_paths), 1)

        # --- Phase 1: Concurrent per-paper ingest + digest ---
        def _process_one_paper(paper_index: int, paper_path: Path) -> dict[str, Any]:
            """Process a single paper in its own AgentContext (thread-safe)."""
            # Create an isolated context for this paper
            sub_ctx = AgentContext(
                project_name=context.project_name,
                paper_path=paper_path,
                run_id=context.run_id,  # share run_dir so artifacts land together
            )
            for skill in self.single_paper_skills:
                result = skill.run(context=sub_ctx, llm=self.llm)
                context.add_trace(
                    skill=result.name,
                    paper=str(paper_path),
                    message=result.message,
                    paper_index=paper_index,
                    paper_count=paper_count,
                )
            profile = self._paper_profile(sub_ctx)
            return {
                "paper_index": paper_index,
                "paper_path": paper_path,
                "profile": profile,
                "summary_tuple": (paper_path.stem, profile["profile_markdown"]),
                "sub_ctx": sub_ctx,
            }

        max_workers = min(paper_count, 4)
        results_by_index: dict[int, dict[str, Any]] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(_process_one_paper, idx, p_path): idx
                for idx, p_path in enumerate(context.paper_paths, start=1)
            }
            done_count = 0
            for future in as_completed(futures):
                done_count += 1
                paper_result = future.result()
                pidx = paper_result["paper_index"]
                results_by_index[pidx] = paper_result
                progress = done_count / (paper_count + 1)
                context.report_progress(
                    "paper_digest",
                    f"已完成第 {done_count}/{paper_count} 篇论文快速分析",
                    progress,
                )

        # Assemble results in original order
        for idx in sorted(results_by_index.keys()):
            res = results_by_index[idx]
            context.paper_summaries.append(res["summary_tuple"])
            context.paper_profiles.append(res["profile"])
            context.save_text(f"paper_{idx}_profile.md", res["profile"]["profile_markdown"])
            context.save_json(f"paper_{idx}_profile.json", res["profile"])

        # --- Phase 2: Multi-paper aggregation (sequential) ---
        multi_steps = len(self.multi_paper_skills)
        for index, skill in enumerate(self.multi_paper_skills, start=1):
            progress = (paper_count + index / multi_steps) / (paper_count + 1)
            context.report_progress(skill.name, f"正在执行多论文阶段：{skill.name}", min(progress, 0.98))
            result = skill.run(context=context, llm=self.llm)
            context.add_trace(skill=result.name, message=result.message, step=index, total_steps=multi_steps, phase="multi")

        manifest = {
            "mode": "survey",
            "project_name": context.project_name,
            "paper_paths": [str(p) for p in context.paper_paths],
            "run_id": context.run_id,
            "trace": context.trace,
            "artifacts": self._artifact_payload(context),
        }
        context.save_json("run_manifest.json", manifest)
        context.report_progress("completed", "多论文综述完成", 1.0)
        return context

    def inspect_repo(self, context: AgentContext) -> AgentContext:
        total_steps = len(self.repo_skills)
        for index, skill in enumerate(self.repo_skills, start=1):
            context.report_progress(skill.name, f"正在执行仓库分析：{skill.name}", index / (total_steps + 1))
            result = skill.run(context=context, llm=self.llm)
            context.add_trace(skill=result.name, message=result.message, step=index, total_steps=total_steps, phase="repo")

        manifest = {
            "mode": "repo",
            "project_name": context.project_name,
            "run_id": context.run_id,
            "trace": context.trace,
            "artifacts": self._artifact_payload(context),
        }
        context.save_json("run_manifest.json", manifest)
        context.report_progress("completed", "仓库分析完成", 1.0)
        return context

    def answer_question(
        self,
        question: str,
        artifacts: dict[str, str],
        scope: list[str] | None = None,
        timeout: float = 120.0,
    ) -> str:
        prompt_path = Path(__file__).resolve().parent / "prompts" / "chat_scoped.txt"
        system_prompt = prompt_path.read_text(encoding="utf-8")
        selected_artifacts = self._select_artifacts(artifacts, scope)
        context_blob = "\n\n".join(
            f"[{name}]\n{content}" for name, content in selected_artifacts.items() if content
        )
        scope_text = ", ".join(scope or [])
        user_prompt = f"scope：{scope_text or '全部材料'}\n\n当前材料：\n{context_blob}\n\n用户问题：{question}"
        return self.llm.complete(system_prompt=system_prompt, user_prompt=user_prompt, timeout=timeout, prefer_fast=True)

    def answer_question_stream(
        self,
        question: str,
        artifacts: dict[str, str],
        scope: list[str] | None = None,
        timeout: float = 120.0,
    ):
        """Streaming variant of :meth:`answer_question`. Yields text chunks."""
        prompt_path = Path(__file__).resolve().parent / "prompts" / "chat_scoped.txt"
        system_prompt = prompt_path.read_text(encoding="utf-8")
        selected_artifacts = self._select_artifacts(artifacts, scope)
        context_blob = "\n\n".join(
            f"[{name}]\n{content}" for name, content in selected_artifacts.items() if content
        )
        scope_text = ", ".join(scope or [])
        user_prompt = f"scope：{scope_text or '全部材料'}\n\n当前材料：\n{context_blob}\n\n用户问题：{question}"
        yield from self.llm.complete_stream(system_prompt=system_prompt, user_prompt=user_prompt, timeout=timeout, prefer_fast=True)

    @staticmethod
    def _select_artifacts(artifacts: dict[str, str], scope: list[str] | None) -> dict[str, str]:
        if not scope:
            return artifacts
        selected: dict[str, str] = {}
        for key, value in artifacts.items():
            if any(token in key for token in scope):
                selected[key] = value
        return selected or artifacts

    @staticmethod
    def _paper_profile(context: AgentContext) -> dict[str, Any]:
        title = context.metadata.get("title") or context.project_name
        profile = {
            "title": title,
            "metadata": context.metadata,
            "summary": context.summary,
            "claims": context.claims,
            "paper_structure": context.paper_structure,
            "method_card": context.method_card,
            "paper_digest": context.paper_digest,
        }
        profile["profile_markdown"] = (
            f"# {title}\n\n"
            f"## 元信息\n{context.metadata}\n\n"
            f"## 摘要\n{context.summary}\n\n"
            f"## 关键信息\n{context.claims}\n\n"
            f"## 论文结构\n{context.paper_structure}\n\n"
            f"## 方法卡片\n{context.method_card}"
        )
        return profile

    @staticmethod
    def _artifact_payload(context: AgentContext) -> dict[str, Any]:
        return {
            "summary": bool(context.summary),
            "claims": bool(context.claims),
            "outline": bool(context.outline),
            "draft": bool(context.draft),
            "survey": bool(context.survey),
            "metadata": bool(context.metadata),
            "paper_structure": bool(context.paper_structure),
            "method_card": bool(context.method_card),
            "paper_digest": bool(context.paper_digest),
            "compare_matrix": bool(context.compare_matrix),
            "comparison_report": bool(context.comparison_report),
            "repo_profile": bool(context.repo_profile),
            "ast_analysis": bool(context.ast_analysis),
            "env_resolution": bool(context.env_resolution),
            "summary_translated": bool(context.summary),
            "paper_count": len(context.paper_summaries),
        }
