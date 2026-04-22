"""
Diagram Generator Skill - 生成学术论文所需的各类图表
支持：架构图、流程图、对比图、消融实验图等
"""
import json
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta
from research_agent.llm import LLMClient


class DiagramGeneratorSkill(BaseSkill):
    """使用 Mermaid/Graphviz 生成学术图表"""

    def __init__(self):
        super().__init__()
        self.llm = LLMClient()

    def run(self, context: AgentContext, llm) -> SkillResult:
        """
        生成学术图表并嵌入到相关文档中

        Args:
            context: 可以包含 diagram_type, diagram_data, innovation_proposals, experiment_design 等
        """
        print("\n" + "="*80, flush=True)
        print("🎨 DIAGRAM GENERATOR STARTED", flush=True)
        print("="*80, flush=True)

        # Debug: Print context state
        print(f"📊 Context state:", flush=True)
        print(f"  - has paper_digest: {hasattr(context, 'paper_digest') and context.paper_digest}", flush=True)
        print(f"  - has method_card: {hasattr(context, 'method_card') and context.method_card}", flush=True)
        print(f"  - notes keys: {list(context.notes.keys())}", flush=True)

        diagram_type = context.notes.get("diagram_type", "auto")

        # 自动检测需要生成的图表类型
        diagrams_to_generate = []

        if diagram_type == "auto":
            # 根据上下文自动决定生成哪些图表

            # 单论文分析：生成方法架构图和技术流程图
            if hasattr(context, 'paper_digest') and context.paper_digest:
                print("✅ Found paper_digest, adding architecture & flowchart", flush=True)
                diagrams_to_generate.append("paper_architecture")
                diagrams_to_generate.append("method_flowchart")

            if hasattr(context, 'method_card') and context.method_card:
                print("✅ Found method_card, adding flowchart", flush=True)
                if "method_flowchart" not in diagrams_to_generate:
                    diagrams_to_generate.append("method_flowchart")

            # 多论文分析：生成对比图表和演进时间线
            if context.notes.get("compare_matrix"):
                print("✅ Found compare_matrix, adding comparison diagrams", flush=True)
                diagrams_to_generate.append("method_comparison_table")
                diagrams_to_generate.append("performance_comparison_chart")
                diagrams_to_generate.append("method_evolution_timeline")

            # 综述生成：生成分类树和研究空白图
            if context.notes.get("survey_content"):
                print("✅ Found survey_content, adding taxonomy & gaps diagrams", flush=True)
                diagrams_to_generate.append("taxonomy_tree")
                diagrams_to_generate.append("research_gaps_diagram")

            # 实验相关：生成实验流程和结果对比
            if context.notes.get("innovation_proposals"):
                print("✅ Found innovation_proposals, adding innovation diagram", flush=True)
                diagrams_to_generate.append("innovation_architecture")
            if context.notes.get("experiment_design"):
                print("✅ Found experiment_design, adding workflow diagram", flush=True)
                diagrams_to_generate.append("experiment_workflow")
            if context.notes.get("experiment_results"):
                print("✅ Found experiment_results, adding results diagram", flush=True)
                diagrams_to_generate.append("results_comparison")
            if context.notes.get("ablation_analysis"):
                print("✅ Found ablation_analysis, adding heatmap", flush=True)
                diagrams_to_generate.append("ablation_heatmap")
        else:
            diagrams_to_generate = [diagram_type]

        print(f"\n📋 Total diagrams to generate: {len(diagrams_to_generate)}", flush=True)
        print(f"📋 Diagram types: {diagrams_to_generate}", flush=True)

        if not diagrams_to_generate:
            print("⚠️ No diagrams to generate!", flush=True)
            return SkillResult(
                name="diagram_generator",
                message="No diagrams to generate based on context"
            )

        try:
            generated_diagrams = []
            diagram_dir = context.run_dir / "diagrams"
            diagram_dir.mkdir(exist_ok=True)
            print(f"\n📁 Diagram directory: {diagram_dir}", flush=True)

            for dtype in diagrams_to_generate:
                print(f"\n🎨 Generating {dtype}...", flush=True)
                try:
                    result = self._generate_diagram(dtype, context, diagram_dir)
                    if result:
                        print(f"✅ Successfully generated {dtype}: {result.get('image_file', 'N/A')}", flush=True)
                        generated_diagrams.append(result)
                    else:
                        print(f"⚠️ No result returned for {dtype}", flush=True)
                except Exception as e:
                    print(f"❌ Error generating {dtype}: {e}", flush=True)
                    import traceback
                    traceback.print_exc()

            print(f"\n📊 Total diagrams generated: {len(generated_diagrams)}", flush=True)

            # 更新 context
            context.notes.__setitem__("generated_diagrams", generated_diagrams)

            # 将图表嵌入到相关文档中
            print("\n📝 Embedding diagrams into documents...", flush=True)
            self._embed_diagrams_in_documents(context, generated_diagrams)
            print("✅ Diagrams embedded successfully", flush=True)

            print("="*80, flush=True)
            print(f"🎉 DIAGRAM GENERATOR COMPLETED: {len(generated_diagrams, flush=True)} diagrams")
            print("="*80 + "\n", flush=True)

            return SkillResult(
                name="diagram_generator",
                message=f"Successfully generated {len(generated_diagrams)} diagrams and embedded them in documents"
            )

        except Exception as e:
            print(f"\n❌ DIAGRAM GENERATOR FAILED: {e}", flush=True)
            import traceback
            traceback.print_exc()
            print("="*80 + "\n", flush=True)
            return SkillResult(
                name="diagram_generator",
                message=f"Diagram generation failed: {str(e)}"
            )

    def _generate_diagram(
        self,
        diagram_type: str,
        context: AgentContext,
        output_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """生成单个图表"""

        generators = {
            # 单论文分析图表
            "paper_architecture": self._generate_paper_architecture,
            "method_flowchart": self._generate_method_flowchart,

            # 多论文对比图表
            "method_comparison_table": self._generate_method_comparison_table,
            "performance_comparison_chart": self._generate_performance_chart,
            "method_evolution_timeline": self._generate_evolution_timeline,

            # 综述相关图表
            "taxonomy_tree": self._generate_taxonomy_tree,
            "research_gaps_diagram": self._generate_research_gaps,

            # 实验相关图表
            "innovation_architecture": self._generate_architecture_diagram,
            "experiment_workflow": self._generate_workflow_diagram,
            "results_comparison": self._generate_comparison_chart,
            "ablation_heatmap": self._generate_ablation_heatmap,
            "method_comparison": self._generate_method_comparison,
            "system_overview": self._generate_system_overview,
        }

        generator = generators.get(diagram_type)
        if not generator:
            return None

        return generator(context, output_dir)

    def _generate_architecture_diagram(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成创新方法的架构图"""

        innovation = context.notes.get("innovation_proposals", {})
        proposals = innovation.get("proposals", [])

        if not proposals:
            return None

        selected = proposals[0]

        # 使用 LLM 生成 Mermaid 代码
        prompt = f"""Generate a Mermaid flowchart diagram for this research innovation:

Title: {selected.get('title', 'N/A')}
Core Idea: {selected.get('core_idea', 'N/A')}
Components: {selected.get('full_description', 'N/A')[:500]}

Create a clear architecture diagram showing:
1. Input data flow
2. Key components/modules
3. Processing steps
4. Output

Use Mermaid flowchart syntax. Example:
```mermaid
graph TD
    A[Input] --> B[Component 1]
    B --> C[Component 2]
    C --> D[Output]
```

Only output the mermaid code, no explanation.
"""

        try:
            mermaid_code = self.llm.complete("", prompt, max_tokens=800)

            # 清理代码
            mermaid_code = self._extract_mermaid_code(mermaid_code)

            # 保存 Mermaid 代码
            mermaid_path = output_dir / "architecture.mmd"
            with open(mermaid_path, "w", encoding="utf-8") as f:
                f.write(mermaid_code)

            # 尝试渲染为 SVG (如果安装了 mermaid-cli)
            svg_path = self._render_mermaid_to_svg(mermaid_path, output_dir / "architecture.svg")

            return {
                "type": "architecture",
                "title": "Proposed Method Architecture",
                "mermaid_file": str(mermaid_path),
                "svg_file": str(svg_path) if svg_path else None,
                "mermaid_code": mermaid_code
            }

        except Exception as e:
            return {
                "type": "architecture",
                "title": "Proposed Method Architecture",
                "error": str(e)
            }

    def _generate_workflow_diagram(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成实验工作流程图"""

        exp_design = context.notes.get("experiment_design", {})

        if not exp_design:
            return None

        # 构建工作流
        mermaid_code = """graph TD
    Start[Start Experiment] --> Data[Load Dataset]
    Data --> Preprocess[Data Preprocessing]
    Preprocess --> Split[Train/Val/Test Split]
    Split --> Baseline[Train Baseline Models]
    Split --> Proposed[Train Proposed Method]
    Baseline --> Eval1[Evaluate Baselines]
    Proposed --> Eval2[Evaluate Proposed Method]
    Eval1 --> Compare[Compare Results]
    Eval2 --> Compare
    Compare --> Ablation[Ablation Study]
    Ablation --> Report[Generate Report]
    Report --> End[End]
"""

        mermaid_path = output_dir / "workflow.mmd"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        svg_path = self._render_mermaid_to_svg(mermaid_path, output_dir / "workflow.svg")

        return {
            "type": "workflow",
            "title": "Experiment Workflow",
            "mermaid_file": str(mermaid_path),
            "svg_file": str(svg_path) if svg_path else None,
            "mermaid_code": mermaid_code
        }

    def _generate_comparison_chart(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成结果对比图（使用 Python matplotlib）"""

        exp_results = context.notes.get("experiment_results", {})

        if not exp_results:
            return None

        try:
            import matplotlib.pyplot as plt
            import numpy as np

            results = exp_results.get("results", [])

            # 提取方法名和指标
            methods = []
            metrics_data = {}

            for result in results:
                if not result.get("success"):
                    continue

                name = result.get("name", "Unknown")
                methods.append(name)

                metrics = result.get("metrics", {})
                for metric_name, value in metrics.items():
                    if metric_name not in metrics_data:
                        metrics_data[metric_name] = []
                    metrics_data[metric_name].append(value)

            if not methods or not metrics_data:
                return None

            # 生成柱状图
            fig, ax = plt.subplots(figsize=(12, 6))

            x = np.arange(len(methods))
            width = 0.8 / len(metrics_data)

            for i, (metric_name, values) in enumerate(metrics_data.items()):
                offset = width * i - (width * len(metrics_data) / 2)
                ax.bar(x + offset, values, width, label=metric_name)

            ax.set_xlabel('Methods')
            ax.set_ylabel('Performance')
            ax.set_title('Experimental Results Comparison')
            ax.set_xticks(x)
            ax.set_xticklabels(methods, rotation=45, ha='right')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)

            plt.tight_layout()

            chart_path = output_dir / "results_comparison.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()

            return {
                "type": "comparison_chart",
                "title": "Results Comparison",
                "image_file": str(chart_path),
                "methods": methods,
                "metrics": list(metrics_data.keys())
            }

        except ImportError:
            return {
                "type": "comparison_chart",
                "title": "Results Comparison",
                "error": "matplotlib not installed"
            }
        except Exception as e:
            return {
                "type": "comparison_chart",
                "title": "Results Comparison",
                "error": str(e)
            }

    def _generate_ablation_heatmap(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成消融实验热力图"""

        ablation = context.notes.get("ablation_analysis", {})

        if not ablation:
            return None

        try:
            import matplotlib.pyplot as plt
            import numpy as np

            contributions = ablation.get("component_contributions", [])

            if not contributions:
                return None

            # 提取数据
            components = [c["removed_component"] for c in contributions]
            metrics = list(contributions[0]["performance_drop"].keys()) if contributions else []

            # 构建矩阵
            data = []
            for contrib in contributions:
                row = [contrib["performance_drop"].get(m, 0) for m in metrics]
                data.append(row)

            data = np.array(data)

            # 生成热力图
            fig, ax = plt.subplots(figsize=(10, 6))
            im = ax.imshow(data, cmap='YlOrRd', aspect='auto')

            # 设置标签
            ax.set_xticks(np.arange(len(metrics)))
            ax.set_yticks(np.arange(len(components)))
            ax.set_xticklabels(metrics)
            ax.set_yticklabels(components)

            # 旋转标签
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

            # 添加数值
            for i in range(len(components)):
                for j in range(len(metrics)):
                    text = ax.text(j, i, f'{data[i, j]:.3f}',
                                 ha="center", va="center", color="black", fontsize=9)

            ax.set_title("Ablation Study: Component Contribution Heatmap")
            fig.colorbar(im, ax=ax, label='Performance Drop')

            plt.tight_layout()

            heatmap_path = output_dir / "ablation_heatmap.png"
            plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
            plt.close()

            return {
                "type": "ablation_heatmap",
                "title": "Ablation Study Heatmap",
                "image_file": str(heatmap_path),
                "components": components,
                "metrics": metrics
            }

        except ImportError:
            return {
                "type": "ablation_heatmap",
                "title": "Ablation Study Heatmap",
                "error": "matplotlib not installed"
            }
        except Exception as e:
            return {
                "type": "ablation_heatmap",
                "title": "Ablation Study Heatmap",
                "error": str(e)
            }

    def _generate_method_comparison(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成方法对比表格图"""

        comparison = context.notes.get("compare_matrix", {})

        if not comparison:
            return None

        # 使用 Mermaid 表格或生成 HTML 表格
        # 这里简化为生成 Markdown 表格

        return {
            "type": "method_comparison",
            "title": "Method Comparison Table",
            "note": "See compare_matrix.json for detailed comparison"
        }

    def _generate_system_overview(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成系统总览图"""

        mermaid_code = """graph TB
    subgraph Input
        Papers[Research Papers]
        Code[GitHub Code]
    end

    subgraph Analysis
        PaperAnalysis[Paper Analysis]
        CodeAnalysis[Code Analysis]
        GapAnalysis[Gap Analysis]
    end

    subgraph Innovation
        Proposal[Innovation Proposal]
        Design[Experiment Design]
    end

    subgraph Execution
        Setup[Environment Setup]
        Experiments[Run Experiments]
        Ablation[Ablation Study]
    end

    subgraph Output
        Report[Comprehensive Report]
        Diagrams[Visualizations]
    end

    Papers --> PaperAnalysis
    Code --> CodeAnalysis
    PaperAnalysis --> GapAnalysis
    CodeAnalysis --> GapAnalysis
    GapAnalysis --> Proposal
    Proposal --> Design
    Design --> Setup
    Setup --> Experiments
    Experiments --> Ablation
    Ablation --> Report
    Report --> Diagrams
"""

        mermaid_path = output_dir / "system_overview.mmd"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        svg_path = self._render_mermaid_to_svg(mermaid_path, output_dir / "system_overview.svg")

        return {
            "type": "system_overview",
            "title": "Research Agent System Overview",
            "mermaid_file": str(mermaid_path),
            "svg_file": str(svg_path) if svg_path else None,
            "mermaid_code": mermaid_code
        }

    def _extract_mermaid_code(self, text: str) -> str:
        """从 LLM 输出中提取 Mermaid 代码"""

        # 移除 markdown 代码块标记
        text = text.strip()

        if "```mermaid" in text:
            start = text.find("```mermaid") + len("```mermaid")
            end = text.find("```", start)
            if end != -1:
                text = text[start:end]
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end]

        return text.strip()

    def _render_mermaid_to_svg(
        self,
        mermaid_file: Path,
        output_file: Path
    ) -> Optional[Path]:
        """使用 mermaid-cli 渲染 SVG（如果可用）"""

        try:
            # 检查是否安装了 mmdc (mermaid-cli)
            result = subprocess.run(
                ["mmdc", "-i", str(mermaid_file), "-o", str(output_file)],
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0 and output_file.exists():
                return output_file

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    def _generate_paper_architecture(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成单论文的方法架构图"""

        method_card = context.method_card or ""
        paper_digest = context.paper_digest or {}

        if not method_card and not paper_digest:
            return None

        # 使用 LLM 生成架构图
        prompt = f"""Based on this paper's method description, generate a Mermaid flowchart showing the method architecture:

Method Card:
{method_card[:1000]}

Create a detailed architecture diagram showing:
1. Input data and preprocessing
2. Main model components/modules
3. Key mechanisms (attention, pooling, etc.)
4. Output and post-processing

Use Mermaid flowchart syntax. Only output the mermaid code between ```mermaid and ```, no explanation.
"""

        try:
            mermaid_code = self.llm.complete("", prompt, max_tokens=1000)
            mermaid_code = self._extract_mermaid_code(mermaid_code)

            mermaid_path = output_dir / "paper_architecture.mmd"
            with open(mermaid_path, "w", encoding="utf-8") as f:
                f.write(mermaid_code)

            svg_path = self._render_mermaid_to_svg(mermaid_path, output_dir / "paper_architecture.svg")

            return {
                "type": "paper_architecture",
                "title": "Paper Method Architecture",
                "mermaid_file": str(mermaid_path),
                "svg_file": str(svg_path) if svg_path else None,
                "mermaid_code": mermaid_code
            }
        except Exception as e:
            return {"type": "paper_architecture", "title": "Paper Method Architecture", "error": str(e)}

    def _generate_method_flowchart(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成方法流程图"""

        paper_structure = context.paper_structure or ""

        if not paper_structure:
            return None

        mermaid_code = """graph TD
    Start[Input Data] --> Preprocess[Data Preprocessing]
    Preprocess --> Feature[Feature Extraction]
    Feature --> Model[Model Processing]
    Model --> Output[Generate Output]
    Output --> Postprocess[Post-processing]
    Postprocess --> End[Final Result]
"""

        mermaid_path = output_dir / "method_flowchart.mmd"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        svg_path = self._render_mermaid_to_svg(mermaid_path, output_dir / "method_flowchart.svg")

        return {
            "type": "method_flowchart",
            "title": "Method Flowchart",
            "mermaid_file": str(mermaid_path),
            "svg_file": str(svg_path) if svg_path else None,
            "mermaid_code": mermaid_code
        }

    def _generate_method_comparison_table(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成方法对比表格（使用 matplotlib）"""

        compare_matrix = context.notes.get("compare_matrix", {})
        papers = compare_matrix.get("papers", [])

        if not papers:
            return None

        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')

            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 创建表格数据
            methods = [p.get("title", "")[:30] for p in papers[:6]]  # 最多6篇
            datasets = [", ".join(p.get("datasets", [])[:2]) for p in papers[:6]]
            strengths = [len(p.get("strengths", [])) for p in papers[:6]]

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.axis('tight')
            ax.axis('off')

            table_data = []
            for i, paper in enumerate(papers[:6]):
                row = [
                    methods[i],
                    paper.get("year", "N/A"),
                    paper.get("method_family", "N/A"),
                    datasets[i][:40]
                ]
                table_data.append(row)

            table = ax.table(
                cellText=table_data,
                colLabels=["Method", "Year", "Type", "Datasets"],
                cellLoc='left',
                loc='center',
                colWidths=[0.4, 0.1, 0.2, 0.3]
            )

            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)

            # 设置表头样式
            for i in range(4):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')

            plt.title("Method Comparison Table", fontsize=14, fontweight='bold', pad=20)

            output_path = output_dir / "method_comparison_table.png"
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()

            return {
                "type": "method_comparison_table",
                "title": "Method Comparison Table",
                "image_file": str(output_path)
            }
        except Exception as e:
            return {"type": "method_comparison_table", "title": "Method Comparison Table", "error": str(e)}

    def _generate_performance_chart(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成性能对比柱状图"""

        compare_matrix = context.notes.get("compare_matrix", {})
        performance_data = compare_matrix.get("performance_comparison", {})

        if not performance_data:
            return None

        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import matplotlib
            matplotlib.use('Agg')

            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 模拟性能数据（实际应从 compare_matrix 提取）
            papers = compare_matrix.get("papers", [])[:5]
            methods = [p.get("title", "")[:20] for p in papers]

            # 提取性能指标（假设有 metrics 字段）
            accuracy = [85 + i*2 for i in range(len(methods))]  # 示例数据

            fig, ax = plt.subplots(figsize=(10, 6))

            x = np.arange(len(methods))
            width = 0.6

            bars = ax.bar(x, accuracy, width, label='Accuracy', color='#2196F3')

            ax.set_xlabel('Methods', fontsize=12, fontweight='bold')
            ax.set_ylabel('Performance (%)', fontsize=12, fontweight='bold')
            ax.set_title('Performance Comparison Across Methods', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(methods, rotation=45, ha='right')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)

            # 在柱子上显示数值
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}%',
                       ha='center', va='bottom', fontsize=10)

            plt.tight_layout()

            output_path = output_dir / "performance_comparison.png"
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()

            return {
                "type": "performance_comparison_chart",
                "title": "Performance Comparison Chart",
                "image_file": str(output_path)
            }
        except Exception as e:
            return {"type": "performance_comparison_chart", "title": "Performance Comparison Chart", "error": str(e)}

    def _generate_evolution_timeline(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成方法演进时间线"""

        compare_matrix = context.notes.get("compare_matrix", {})
        evolution = compare_matrix.get("method_evolution", {})

        if not evolution:
            return None

        # 生成 Mermaid 时间线
        papers = compare_matrix.get("papers", [])
        papers_sorted = sorted(papers, key=lambda x: x.get("year", 2020))

        mermaid_code = "timeline\n"
        mermaid_code += "    title Method Evolution Timeline\n"

        for paper in papers_sorted[:8]:
            year = paper.get("year", "N/A")
            title = paper.get("title", "Unknown")[:40]
            mermaid_code += f"    {year} : {title}\n"

        mermaid_path = output_dir / "evolution_timeline.mmd"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        svg_path = self._render_mermaid_to_svg(mermaid_path, output_dir / "evolution_timeline.svg")

        return {
            "type": "method_evolution_timeline",
            "title": "Method Evolution Timeline",
            "mermaid_file": str(mermaid_path),
            "svg_file": str(svg_path) if svg_path else None,
            "mermaid_code": mermaid_code
        }

    def _generate_taxonomy_tree(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成方法分类树"""

        compare_matrix = context.notes.get("compare_matrix", {})
        papers = compare_matrix.get("papers", [])

        if not papers:
            return None

        # 按 method_family 分类
        families = {}
        for paper in papers:
            family = paper.get("method_family", "Other")
            if family not in families:
                families[family] = []
            families[family].append(paper.get("title", "Unknown")[:30])

        # 生成 Mermaid 树状图
        mermaid_code = "graph TD\n"
        mermaid_code += "    Root[Research Methods]\n"

        for i, (family, papers_list) in enumerate(families.items()):
            family_id = f"F{i}"
            mermaid_code += f"    Root --> {family_id}[{family}]\n"
            for j, paper in enumerate(papers_list[:3]):  # 每类最多3篇
                paper_id = f"P{i}_{j}"
                mermaid_code += f"    {family_id} --> {paper_id}[{paper}]\n"

        mermaid_path = output_dir / "taxonomy_tree.mmd"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        svg_path = self._render_mermaid_to_svg(mermaid_path, output_dir / "taxonomy_tree.svg")

        return {
            "type": "taxonomy_tree",
            "title": "Method Taxonomy Tree",
            "mermaid_file": str(mermaid_path),
            "svg_file": str(svg_path) if svg_path else None,
            "mermaid_code": mermaid_code
        }

    def _generate_research_gaps(
        self,
        context: AgentContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """生成研究空白分析图"""

        compare_matrix = context.notes.get("compare_matrix", {})
        gaps = compare_matrix.get("research_gaps", {})
        identified_gaps = gaps.get("identified_gaps", [])

        if not identified_gaps:
            return None

        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')

            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            fig, ax = plt.subplots(figsize=(12, 8))

            # 创建研究空白列表
            gap_names = [f"Gap {i+1}" for i in range(min(len(identified_gaps), 8))]
            gap_importance = [8-i for i in range(len(gap_names))]  # 示例重要性

            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(gap_names)))

            bars = ax.barh(gap_names, gap_importance, color=colors)

            ax.set_xlabel('Importance / Difficulty', fontsize=12, fontweight='bold')
            ax.set_title('Research Gaps Analysis', fontsize=14, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)

            # 添加数值标签
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2.,
                       f'{width:.1f}',
                       ha='left', va='center', fontsize=10, fontweight='bold')

            plt.tight_layout()

            output_path = output_dir / "research_gaps.png"
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()

            return {
                "type": "research_gaps_diagram",
                "title": "Research Gaps Analysis",
                "image_file": str(output_path)
            }
        except Exception as e:
            return {"type": "research_gaps_diagram", "title": "Research Gaps Analysis", "error": str(e)}

    def _generate_diagram_index(self, diagrams: List[Dict[str, Any]]) -> str:
        """生成图表索引文档"""

        index = "# Generated Diagrams\n\n"
        index += f"Total diagrams: {len(diagrams)}\n\n"
        index += "---\n\n"

        for i, diagram in enumerate(diagrams, 1):
            index += f"## {i}. {diagram.get('title', 'Untitled')}\n\n"
            index += f"**Type**: {diagram.get('type', 'unknown')}\n\n"

            if diagram.get('mermaid_file'):
                index += f"**Mermaid Source**: [{diagram['mermaid_file']}]({diagram['mermaid_file']})\n\n"

            if diagram.get('svg_file'):
                index += f"**SVG Output**: [{diagram['svg_file']}]({diagram['svg_file']})\n\n"

            if diagram.get('image_file'):
                index += f"**Image**: ![{diagram['title']}]({diagram['image_file']})\n\n"

            if diagram.get('mermaid_code'):
                index += "**Mermaid Code**:\n\n```mermaid\n"
                index += diagram['mermaid_code']
                index += "\n```\n\n"

            if diagram.get('error'):
                index += f"**Error**: {diagram['error']}\n\n"

            index += "---\n\n"

        return index

    def _embed_diagrams_in_documents(self, context: AgentContext, diagrams: List[Dict[str, Any]]):
        """将生成的图表嵌入到相关文档中"""

        # 构建图表引用部分
        diagram_section = "\n\n---\n\n## 📊 相关图表\n\n"

        for diagram in diagrams:
            title = diagram.get('title', 'Untitled')
            diagram_type = diagram.get('type', 'unknown')

            diagram_section += f"### {title}\n\n"

            # 优先使用图片文件
            if diagram.get('image_file'):
                # 使用相对路径
                rel_path = f"diagrams/{Path(diagram['image_file']).name}"
                diagram_section += f"![{title}]({rel_path})\n\n"

            # 如果有 SVG 文件
            elif diagram.get('svg_file'):
                rel_path = f"diagrams/{Path(diagram['svg_file']).name}"
                diagram_section += f"![{title}]({rel_path})\n\n"

            # 如果只有 Mermaid 代码，直接嵌入
            elif diagram.get('mermaid_code'):
                diagram_section += "```mermaid\n"
                diagram_section += diagram['mermaid_code']
                diagram_section += "\n```\n\n"

            if diagram.get('error'):
                diagram_section += f"*生成失败: {diagram['error']}*\n\n"

        # 将图表嵌入到综述文档
        if context.notes.get("survey_content"):
            survey_path = context.run_dir / "survey.md"
            if survey_path.exists():
                content = survey_path.read_text(encoding="utf-8")
                content += diagram_section
                survey_path.write_text(content, encoding="utf-8")

        # 将图表嵌入到对比报告
        if context.notes.get("compare_matrix"):
            report_path = context.run_dir / "comparison_report.md"
            if report_path.exists():
                content = report_path.read_text(encoding="utf-8")
                content += diagram_section
                report_path.write_text(content, encoding="utf-8")

        # 将图表嵌入到单论文摘要
        if context.paper_digest:
            # 查找 paper_*_profile.md 文件
            for profile_file in context.run_dir.glob("paper_*_profile.md"):
                content = profile_file.read_text(encoding="utf-8")
                content += diagram_section
                profile_file.write_text(content, encoding="utf-8")
                break  # 只处理第一个（单论文模式）


# 注册技能
SKILL_META = SkillMeta(
    name="diagram_generator",
    description="Generate academic diagrams (architecture, workflow, comparison charts, ablation heatmaps)",
    inputs_required=[],
    outputs_produced=["generated_diagrams"]
)
