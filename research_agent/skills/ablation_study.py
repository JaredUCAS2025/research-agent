"""
Ablation Study Skill - 系统性地执行消融实验
"""
import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta
from research_agent.llm import LLMClient


class AblationStudySkill(BaseSkill):
    """系统性地规划、执行和分析消融实验"""

    def __init__(self):
        super().__init__()
        self.llm = LLMClient()

    def execute(self, context: AgentContext) -> SkillResult:
        """
        执行消融实验分析

        Args:
            context: 需要包含 experiment_results
        """
        experiment_results = context.get("experiment_results")

        if not experiment_results:
            return SkillResult(
                success=False,
                message="Missing experiment_results in context",
                artifacts={}
            )

        try:
            # 提取消融实验结果
            ablation_results = self._extract_ablation_results(experiment_results)

            if not ablation_results:
                return SkillResult(
                    success=False,
                    message="No ablation experiments found in results",
                    artifacts={}
                )

            # 分析消融实验
            analysis = self._analyze_ablations(ablation_results)

            # 生成可视化
            visualizations = self._generate_visualizations(
                ablation_results,
                context.run_dir
            )

            # 生成报告
            report = self._generate_ablation_report(
                ablation_results,
                analysis,
                visualizations
            )

            report_path = context.run_dir / "ablation_study.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # 保存分析结果
            analysis_path = context.run_dir / "ablation_analysis.json"
            with open(analysis_path, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)

            # 更新 context
            context.set("ablation_analysis", analysis)

            return SkillResult(
                success=True,
                message=f"Analyzed {len(ablation_results)} ablation experiments",
                artifacts={
                    "ablation_analysis": analysis,
                    "analysis_json": str(analysis_path),
                    "report": str(report_path),
                    "visualizations": visualizations
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Ablation study failed: {str(e)}",
                artifacts={}
            )

    def _extract_ablation_results(
        self,
        experiment_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """提取消融实验结果"""

        ablation_results = []
        results = experiment_results.get("results", [])

        for result in results:
            if result.get("type") == "ablation" or "w/o" in result.get("name", "").lower():
                ablation_results.append(result)

        return ablation_results

    def _analyze_ablations(
        self,
        ablation_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析消融实验结果"""

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_ablations": len(ablation_results),
            "component_contributions": [],
            "ranking": [],
            "insights": []
        }

        # 找到全模型（baseline）
        full_model = None
        for result in ablation_results:
            if "full" in result.get("name", "").lower():
                full_model = result
                break

        if not full_model:
            # 如果没有明确的全模型，使用第一个
            full_model = ablation_results[0] if ablation_results else None

        if not full_model:
            return analysis

        full_metrics = full_model.get("metrics", {})

        # 分析每个组件的贡献
        for result in ablation_results:
            if result == full_model:
                continue

            name = result.get("name", "")
            metrics = result.get("metrics", {})

            # 计算性能下降
            contribution = {
                "component": name,
                "removed_component": self._extract_removed_component(name),
                "performance_drop": {},
                "relative_drop_percent": {}
            }

            for metric_name, full_value in full_metrics.items():
                if metric_name in metrics:
                    ablation_value = metrics[metric_name]

                    # 计算绝对下降
                    drop = full_value - ablation_value

                    # 计算相对下降百分比
                    if full_value != 0:
                        relative_drop = (drop / full_value) * 100
                    else:
                        relative_drop = 0

                    contribution["performance_drop"][metric_name] = round(drop, 4)
                    contribution["relative_drop_percent"][metric_name] = round(relative_drop, 2)

            analysis["component_contributions"].append(contribution)

        # 排名组件（按主要指标）
        if analysis["component_contributions"]:
            # 使用第一个指标作为主要指标
            primary_metric = list(full_metrics.keys())[0] if full_metrics else None

            if primary_metric:
                sorted_components = sorted(
                    analysis["component_contributions"],
                    key=lambda x: abs(x["performance_drop"].get(primary_metric, 0)),
                    reverse=True
                )

                analysis["ranking"] = [
                    {
                        "rank": i + 1,
                        "component": comp["removed_component"],
                        "impact": comp["performance_drop"].get(primary_metric, 0)
                    }
                    for i, comp in enumerate(sorted_components)
                ]

        # 生成洞察
        analysis["insights"] = self._generate_insights(analysis)

        return analysis

    def _extract_removed_component(self, name: str) -> str:
        """从实验名称中提取被移除的组件"""

        # 常见模式: "w/o Component", "without Component", "no Component"
        patterns = ["w/o ", "without ", "no ", "remove "]

        for pattern in patterns:
            if pattern in name.lower():
                idx = name.lower().index(pattern)
                component = name[idx + len(pattern):].strip()
                return component

        return name

    def _generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """生成洞察"""

        insights = []

        ranking = analysis.get("ranking", [])
        if ranking:
            # 最重要的组件
            most_important = ranking[0]
            insights.append(
                f"The most critical component is '{most_important['component']}' "
                f"with an impact of {most_important['impact']:.4f}"
            )

            # 最不重要的组件
            if len(ranking) > 1:
                least_important = ranking[-1]
                insights.append(
                    f"The least critical component is '{least_important['component']}' "
                    f"with an impact of {least_important['impact']:.4f}"
                )

        # 分析贡献分布
        contributions = analysis.get("component_contributions", [])
        if contributions:
            drops = [
                abs(c["performance_drop"].get(list(c["performance_drop"].keys())[0], 0))
                for c in contributions
                if c["performance_drop"]
            ]

            if drops:
                avg_drop = sum(drops) / len(drops)
                max_drop = max(drops)
                min_drop = min(drops)

                insights.append(
                    f"Performance drops range from {min_drop:.4f} to {max_drop:.4f}, "
                    f"with an average of {avg_drop:.4f}"
                )

        return insights

    def _generate_visualizations(
        self,
        ablation_results: List[Dict[str, Any]],
        output_dir: Path
    ) -> Dict[str, str]:
        """生成可视化图表"""

        visualizations = {}

        try:
            import matplotlib.pyplot as plt
            import numpy as np

            # 提取数据
            names = []
            metrics_data = {}

            for result in ablation_results:
                name = result.get("name", "")
                names.append(name)

                metrics = result.get("metrics", {})
                for metric_name, value in metrics.items():
                    if metric_name not in metrics_data:
                        metrics_data[metric_name] = []
                    metrics_data[metric_name].append(value)

            if not names or not metrics_data:
                return visualizations

            # 为每个指标生成条形图
            for metric_name, values in metrics_data.items():
                fig, ax = plt.subplots(figsize=(10, 6))

                x = np.arange(len(names))
                bars = ax.bar(x, values, color='steelblue', alpha=0.8)

                # 高亮最高值
                max_idx = values.index(max(values))
                bars[max_idx].set_color('green')
                bars[max_idx].set_alpha(1.0)

                ax.set_xlabel('Experiment')
                ax.set_ylabel(metric_name)
                ax.set_title(f'Ablation Study: {metric_name}')
                ax.set_xticks(x)
                ax.set_xticklabels(names, rotation=45, ha='right')
                ax.grid(axis='y', alpha=0.3)

                plt.tight_layout()

                # 保存图表
                chart_path = output_dir / f"ablation_{metric_name}.png"
                plt.savefig(chart_path, dpi=150, bbox_inches='tight')
                plt.close()

                visualizations[metric_name] = str(chart_path)

        except ImportError:
            # matplotlib 未安装
            pass
        except Exception as e:
            print(f"Visualization error: {str(e)}")

        return visualizations

    def _generate_ablation_report(
        self,
        ablation_results: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        visualizations: Dict[str, str]
    ) -> str:
        """生成消融实验报告"""

        report = "# Ablation Study Report\n\n"
        report += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"**Total Ablation Experiments**: {len(ablation_results)}\n\n"
        report += "---\n\n"

        # 组件贡献
        report += "## Component Contributions\n\n"

        contributions = analysis.get("component_contributions", [])
        if contributions:
            report += "| Component | Performance Drop | Relative Drop (%) |\n"
            report += "|-----------|------------------|-------------------|\n"

            for contrib in contributions:
                component = contrib["removed_component"]
                drops = contrib["performance_drop"]
                relative_drops = contrib["relative_drop_percent"]

                # 使用第一个指标
                if drops:
                    metric_name = list(drops.keys())[0]
                    drop_value = drops[metric_name]
                    relative_value = relative_drops[metric_name]

                    report += f"| {component} | {drop_value:.4f} | {relative_value:.2f}% |\n"

            report += "\n"

        # 组件排名
        report += "## Component Importance Ranking\n\n"

        ranking = analysis.get("ranking", [])
        if ranking:
            for item in ranking:
                report += f"{item['rank']}. **{item['component']}** (Impact: {item['impact']:.4f})\n"

            report += "\n"

        # 洞察
        report += "## Key Insights\n\n"

        insights = analysis.get("insights", [])
        for insight in insights:
            report += f"- {insight}\n"

        report += "\n---\n\n"

        # 详细结果
        report += "## Detailed Results\n\n"

        for result in ablation_results:
            report += f"### {result.get('name', 'Unnamed')}\n\n"

            metrics = result.get("metrics", {})
            if metrics:
                report += "**Metrics**:\n\n"
                for metric_name, value in metrics.items():
                    report += f"- {metric_name}: {value:.4f}\n"

            report += f"\n**Duration**: {result.get('duration_seconds', 0):.2f}s\n"
            report += f"**Status**: {'✓ Success' if result.get('success') else '✗ Failed'}\n\n"

        # 可视化
        if visualizations:
            report += "---\n\n"
            report += "## Visualizations\n\n"

            for metric_name, path in visualizations.items():
                report += f"### {metric_name}\n\n"
                report += f"![{metric_name}]({Path(path).name})\n\n"

        return report


# 注册技能
SKILL_META = SkillMeta(
    name="ablation_study",
    description="Systematically analyze ablation experiments and component contributions",
    inputs_required=["experiment_results"],
    outputs_produced=["ablation_analysis", "analysis_json", "report", "visualizations"]
)
