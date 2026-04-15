"""Skill implementations for the research agent."""

# New enhanced skills (using SKILL_META convention)
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

