"""Skill implementations for the research agent."""

# Import all skill modules to register them
from research_agent.skills.ingest_paper import SKILL_META as ingest_paper_meta
from research_agent.skills.paper_digest import SKILL_META as paper_digest_meta
from research_agent.skills.paper_metadata import SKILL_META as paper_metadata_meta
from research_agent.skills.summarize_paper import SKILL_META as summarize_paper_meta
from research_agent.skills.extract_claims import SKILL_META as extract_claims_meta
from research_agent.skills.paper_structure import SKILL_META as paper_structure_meta
from research_agent.skills.method_card import SKILL_META as method_card_meta
from research_agent.skills.paper_comparator import SKILL_META as paper_comparator_meta
from research_agent.skills.contradiction_detector import SKILL_META as contradiction_detector_meta
from research_agent.skills.survey_writer import SKILL_META as survey_writer_meta
from research_agent.skills.repo_skills import (
    REPO_INGESTOR_META,
    AST_ANALYZER_META,
    ENV_RESOLVER_META
)

# New enhanced skills
from research_agent.skills.github_search import SKILL_META as github_search_meta
from research_agent.skills.github_clone import SKILL_META as github_clone_meta
from research_agent.skills.enhanced_code_analyzer import SKILL_META as enhanced_code_analyzer_meta
from research_agent.skills.gap_analyzer import SKILL_META as gap_analyzer_meta
from research_agent.skills.innovation_proposer import SKILL_META as innovation_proposer_meta
from research_agent.skills.experiment_designer import SKILL_META as experiment_designer_meta
from research_agent.skills.environment_setup import SKILL_META as environment_setup_meta
from research_agent.skills.experiment_runner import SKILL_META as experiment_runner_meta
from research_agent.skills.ablation_study import SKILL_META as ablation_study_meta
from research_agent.skills.comprehensive_report import SKILL_META as comprehensive_report_meta

__all__ = [
    "ingest_paper_meta",
    "paper_digest_meta",
    "paper_metadata_meta",
    "summarize_paper_meta",
    "extract_claims_meta",
    "paper_structure_meta",
    "method_card_meta",
    "paper_comparator_meta",
    "contradiction_detector_meta",
    "survey_writer_meta",
    "REPO_INGESTOR_META",
    "AST_ANALYZER_META",
    "ENV_RESOLVER_META",
    "github_search_meta",
    "github_clone_meta",
    "enhanced_code_analyzer_meta",
    "gap_analyzer_meta",
    "innovation_proposer_meta",
    "experiment_designer_meta",
    "environment_setup_meta",
    "experiment_runner_meta",
    "ablation_study_meta",
    "comprehensive_report_meta",
]
