"""
Comprehensive Report Generator Skill - 生成完整的研究报告
"""
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta
from research_agent.llm import LLMClient


class ComprehensiveReportSkill(BaseSkill):
    """生成包含综述、实验报告和消融分析的完整研究报告"""

    def __init__(self):
        super().__init__()
        self.llm = LLMClient()

    def run(self, context: AgentContext, llm) -> SkillResult:
        """
        生成完整报告

        Args:
            context: 需要包含各种分析结果
        """
        try:
            # 收集所有可用的分析结果
            components = {
                "paper_digests": context.get("paper_digests", []),
                "code_analysis": context.get("code_analysis", {}),
                "gap_analysis": context.get("gap_analysis", {}),
                "innovation_proposals": context.get("innovation_proposals", {}),
                "experiment_design": context.get("experiment_design", {}),
                "experiment_results": context.get("experiment_results", {}),
                "ablation_analysis": context.get("ablation_analysis", {})
            }

            # 生成各个部分
            report_sections = {
                "abstract": self._generate_abstract(components),
                "literature_review": self._generate_literature_review(components),
                "methodology": self._generate_methodology(components),
                "experiments": self._generate_experiments_section(components),
                "ablation_study": self._generate_ablation_section(components),
                "results_discussion": self._generate_results_discussion(components),
                "conclusion": self._generate_conclusion(components)
            }

            # 组装完整报告
            full_report = self._assemble_report(report_sections, components)

            # 保存报告
            report_path = context.run_dir / "comprehensive_report.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(full_report)

            # 生成 LaTeX 版本（可选）
            latex_report = self._generate_latex_version(report_sections)
            latex_path = context.run_dir / "comprehensive_report.tex"
            with open(latex_path, "w", encoding="utf-8") as f:
                f.write(latex_report)

            # 生成演示文稿
            presentation = self._generate_presentation(report_sections, components)
            pres_path = context.run_dir / "presentation.md"
            with open(pres_path, "w", encoding="utf-8") as f:
                f.write(presentation)

            # 更新 context
            context.set("comprehensive_report", report_sections)

            return SkillResult(
                success=True,
                message="Successfully generated comprehensive research report",
                artifacts={
                    "report_markdown": str(report_path),
                    "report_latex": str(latex_path),
                    "presentation": str(pres_path),
                    "report_sections": report_sections
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Report generation failed: {str(e)}",
                artifacts={}
            )

    def _generate_abstract(self, components: Dict[str, Any]) -> str:
        """生成摘要"""

        gap_analysis = components.get("gap_analysis", {})
        innovation = components.get("innovation_proposals", {})
        results = components.get("experiment_results", {})

        prompt = f"""Write a concise abstract (150-200 words) for a research paper based on:

Gap Analysis Summary: {gap_analysis.get('summary', 'N/A')}

Innovation: {innovation.get('summary', 'N/A')}

Experiment Results: {results.get('successful', 0)} successful experiments out of {results.get('total_experiments', 0)}

The abstract should cover: background, problem, proposed method, experiments, and key results.
"""

        try:
            abstract = self.llm.complete("", prompt, max_tokens=300)
            return abstract
        except:
            return "Abstract generation failed. Please review the detailed sections below."

    def _generate_literature_review(self, components: Dict[str, Any]) -> str:
        """生成文献综述"""

        paper_digests = components.get("paper_digests", [])
        gap_analysis = components.get("gap_analysis", {})

        review = "## Literature Review\n\n"

        if paper_digests:
            review += "### Related Work\n\n"

            for i, digest in enumerate(paper_digests[:5], 1):
                metadata = digest.get("metadata", {})
                title = metadata.get("title", "Untitled")
                summary = digest.get("summary", "No summary available")

                review += f"#### {i}. {title}\n\n"
                review += f"{summary[:500]}...\n\n"

        # 添加 gap 分析
        if gap_analysis:
            review += "### Research Gaps\n\n"

            limitations = gap_analysis.get("limitations", [])
            if limitations:
                review += "**Limitations of Existing Methods**:\n\n"
                for lim in limitations[:3]:
                    review += f"- {lim.get('description', 'N/A')[:200]}\n"
                review += "\n"

            problems = gap_analysis.get("unsolved_problems", [])
            if problems:
                review += "**Unsolved Problems**:\n\n"
                for prob in problems[:3]:
                    review += f"- {prob.get('description', 'N/A')[:200]}\n"
                review += "\n"

        return review

    def _generate_methodology(self, components: Dict[str, Any]) -> str:
        """生成方法论部分"""

        innovation = components.get("innovation_proposals", {})
        exp_design = components.get("experiment_design", {})

        methodology = "## Methodology\n\n"

        # 提出的方法
        proposals = innovation.get("proposals", [])
        if proposals:
            selected = proposals[0]  # 使用第一个提案

            methodology += "### Proposed Method\n\n"
            methodology += f"**{selected.get('title', 'Untitled')}**\n\n"
            methodology += f"{selected.get('core_idea', 'N/A')}\n\n"

            methodology += "**Theoretical Foundation**:\n\n"
            methodology += f"{selected.get('theoretical_foundation', 'N/A')}\n\n"

        # 实验设计
        if exp_design:
            proposed_method = exp_design.get("proposed_method", {})
            components_list = proposed_method.get("components", [])

            if components_list:
                methodology += "### Key Components\n\n"
                for comp in components_list:
                    methodology += f"- {comp}\n"
                methodology += "\n"

        return methodology

    def _generate_experiments_section(self, components: Dict[str, Any]) -> str:
        """生成实验部分"""

        exp_design = components.get("experiment_design", {})
        exp_results = components.get("experiment_results", {})

        experiments = "## Experiments\n\n"

        # 实验设置
        experiments += "### Experimental Setup\n\n"

        datasets = exp_design.get("datasets", [])
        if datasets:
            experiments += "**Datasets**:\n\n"
            for dataset in datasets:
                experiments += f"- **{dataset.get('name', 'N/A')}**: {dataset.get('description', 'N/A')[:150]}\n"
            experiments += "\n"

        metrics = exp_design.get("metrics", [])
        if metrics:
            experiments += "**Evaluation Metrics**:\n\n"
            for metric in metrics:
                experiments += f"- **{metric.get('name', 'N/A')}**: {metric.get('description', 'N/A')[:150]}\n"
            experiments += "\n"

        baselines = exp_design.get("baseline_methods", [])
        if baselines:
            experiments += "**Baseline Methods**:\n\n"
            for baseline in baselines:
                experiments += f"- **{baseline.get('name', 'N/A')}**: {baseline.get('description', 'N/A')[:150]}\n"
            experiments += "\n"

        # 实验结果
        if exp_results:
            experiments += "### Results\n\n"

            results_list = exp_results.get("results", [])
            if results_list:
                experiments += "| Method | Metrics | Status |\n"
                experiments += "|--------|---------|--------|\n"

                for result in results_list:
                    name = result.get("name", "N/A")
                    metrics_dict = result.get("metrics", {})
                    status = "✓" if result.get("success") else "✗"

                    metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in list(metrics_dict.items())[:3]])

                    experiments += f"| {name} | {metrics_str} | {status} |\n"

                experiments += "\n"

        return experiments

    def _generate_ablation_section(self, components: Dict[str, Any]) -> str:
        """生成消融实验部分"""

        ablation = components.get("ablation_analysis", {})

        section = "## Ablation Study\n\n"

        if not ablation:
            section += "No ablation study conducted.\n\n"
            return section

        # 组件贡献
        contributions = ablation.get("component_contributions", [])
        if contributions:
            section += "### Component Contributions\n\n"

            section += "| Component | Performance Drop | Relative Impact |\n"
            section += "|-----------|------------------|------------------|\n"

            for contrib in contributions:
                component = contrib.get("removed_component", "N/A")
                drops = contrib.get("performance_drop", {})
                relative = contrib.get("relative_drop_percent", {})

                if drops:
                    metric_name = list(drops.keys())[0]
                    drop_val = drops[metric_name]
                    rel_val = relative.get(metric_name, 0)

                    section += f"| {component} | {drop_val:.4f} | {rel_val:.2f}% |\n"

            section += "\n"

        # 排名
        ranking = ablation.get("ranking", [])
        if ranking:
            section += "### Component Importance Ranking\n\n"

            for item in ranking:
                section += f"{item['rank']}. **{item['component']}** (Impact: {item['impact']:.4f})\n"

            section += "\n"

        # 洞察
        insights = ablation.get("insights", [])
        if insights:
            section += "### Key Findings\n\n"

            for insight in insights:
                section += f"- {insight}\n"

            section += "\n"

        return section

    def _generate_results_discussion(self, components: Dict[str, Any]) -> str:
        """生成结果讨论"""

        exp_results = components.get("experiment_results", {})
        ablation = components.get("ablation_analysis", {})

        discussion = "## Discussion\n\n"

        # 主要发现
        discussion += "### Main Findings\n\n"

        if exp_results:
            total = exp_results.get("total_experiments", 0)
            successful = exp_results.get("successful", 0)

            discussion += f"We conducted {total} experiments, of which {successful} completed successfully. "

        # 消融实验洞察
        if ablation:
            insights = ablation.get("insights", [])
            if insights:
                discussion += "The ablation study revealed:\n\n"
                for insight in insights:
                    discussion += f"- {insight}\n"
                discussion += "\n"

        discussion += "### Limitations\n\n"
        discussion += "- Limited computational resources\n"
        discussion += "- Dataset size constraints\n"
        discussion += "- Time constraints for extensive hyperparameter tuning\n\n"

        return discussion

    def _generate_conclusion(self, components: Dict[str, Any]) -> str:
        """生成结论"""

        conclusion = "## Conclusion\n\n"

        innovation = components.get("innovation_proposals", {})
        exp_results = components.get("experiment_results", {})

        if innovation:
            proposals = innovation.get("proposals", [])
            if proposals:
                selected = proposals[0]
                conclusion += f"We proposed {selected.get('title', 'a novel method')} to address "
                conclusion += f"the identified research gaps. "

        if exp_results:
            successful = exp_results.get("successful", 0)
            if successful > 0:
                conclusion += f"Our experiments demonstrated the effectiveness of the proposed approach. "

        conclusion += "\n\n### Future Work\n\n"
        conclusion += "- Extend experiments to larger datasets\n"
        conclusion += "- Explore additional architectural variations\n"
        conclusion += "- Conduct more comprehensive ablation studies\n"
        conclusion += "- Apply the method to related tasks\n\n"

        return conclusion

    def _assemble_report(
        self,
        sections: Dict[str, str],
        components: Dict[str, Any]
    ) -> str:
        """组装完整报告"""

        report = "# Comprehensive Research Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "---\n\n"

        # 摘要
        report += "## Abstract\n\n"
        report += sections.get("abstract", "")
        report += "\n\n---\n\n"

        # 其他部分
        report += sections.get("literature_review", "")
        report += "\n---\n\n"

        report += sections.get("methodology", "")
        report += "\n---\n\n"

        report += sections.get("experiments", "")
        report += "\n---\n\n"

        report += sections.get("ablation_study", "")
        report += "\n---\n\n"

        report += sections.get("results_discussion", "")
        report += "\n---\n\n"

        report += sections.get("conclusion", "")

        return report

    def _generate_latex_version(self, sections: Dict[str, str]) -> str:
        """生成 LaTeX 版本（简化）"""

        latex = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{booktabs}

\title{Comprehensive Research Report}
\author{Research Agent}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
""" + sections.get("abstract", "") + r"""
\end{abstract}

""" + sections.get("literature_review", "").replace("#", "\\section") + r"""

""" + sections.get("methodology", "").replace("#", "\\section") + r"""

\end{document}
"""

        return latex

    def _generate_presentation(
        self,
        sections: Dict[str, str],
        components: Dict[str, Any]
    ) -> str:
        """生成演示文稿（Markdown slides）"""

        presentation = "---\n"
        presentation += "marp: true\n"
        presentation += "theme: default\n"
        presentation += "---\n\n"

        presentation += "# Research Presentation\n\n"
        presentation += f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        presentation += "---\n\n"

        presentation += "## Problem & Motivation\n\n"
        gap = components.get("gap_analysis", {})
        if gap:
            presentation += f"{gap.get('summary', 'N/A')}\n\n"
        presentation += "---\n\n"

        presentation += "## Proposed Method\n\n"
        innovation = components.get("innovation_proposals", {})
        if innovation:
            proposals = innovation.get("proposals", [])
            if proposals:
                selected = proposals[0]
                presentation += f"### {selected.get('title', 'N/A')}\n\n"
                presentation += f"{selected.get('core_idea', 'N/A')}\n\n"
        presentation += "---\n\n"

        presentation += "## Experimental Results\n\n"
        exp_results = components.get("experiment_results", {})
        if exp_results:
            presentation += f"- Total Experiments: {exp_results.get('total_experiments', 0)}\n"
            presentation += f"- Successful: {exp_results.get('successful', 0)}\n\n"
        presentation += "---\n\n"

        presentation += "## Ablation Study\n\n"
        ablation = components.get("ablation_analysis", {})
        if ablation:
            ranking = ablation.get("ranking", [])
            if ranking:
                presentation += "**Component Importance**:\n\n"
                for item in ranking[:3]:
                    presentation += f"{item['rank']}. {item['component']}\n"
        presentation += "\n---\n\n"

        presentation += "## Conclusion\n\n"
        presentation += "- Successfully addressed research gaps\n"
        presentation += "- Demonstrated effectiveness through experiments\n"
        presentation += "- Identified key components through ablation\n\n"
        presentation += "---\n\n"

        presentation += "# Thank You!\n\n"
        presentation += "Questions?\n"

        return presentation


# 注册技能
SKILL_META = SkillMeta(
    name="comprehensive_report",
    description="Generate comprehensive research report including survey, experiments, and ablation analysis",
    inputs_required=[],
    outputs_produced=["report_markdown", "report_latex", "presentation", "report_sections"]
)
