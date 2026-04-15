"""
Experiment Designer Skill - 设计实验方案（包括消融实验）
"""
import json
from typing import Dict, Any, List
from pathlib import Path
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta
from research_agent.llm import LLMClient


class ExperimentDesignerSkill(BaseSkill):
    """设计完整的实验方案，包括基线对比和消融实验"""

    def __init__(self):
        super().__init__()
        self.llm = LLMClient()

    def execute(self, context: AgentContext) -> SkillResult:
        """
        设计实验方案

        Args:
            context: 需要包含 innovation_proposals（或选定的创新点）
        """
        innovation_proposals = context.get("innovation_proposals")
        selected_innovation = context.get("selected_innovation")

        if not innovation_proposals and not selected_innovation:
            return SkillResult(
                success=False,
                message="Missing innovation_proposals or selected_innovation in context",
                artifacts={}
            )

        # 如果没有选定的创新点，使用第一个高优先级的
        if not selected_innovation and innovation_proposals:
            proposals = innovation_proposals.get("proposals", [])
            high_priority = [p for p in proposals if p.get("priority") == "High"]
            if high_priority:
                selected_innovation = high_priority[0]
            elif proposals:
                selected_innovation = proposals[0]

        if not selected_innovation:
            return SkillResult(
                success=False,
                message="No innovation to design experiments for",
                artifacts={}
            )

        try:
            # 设计实验方案
            experiment_design = self._design_experiments(
                selected_innovation,
                context
            )

            # 保存结果
            output_path = context.run_dir / "experiment_design.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(experiment_design, f, indent=2, ensure_ascii=False)

            # 生成报告
            report = self._generate_report(experiment_design)
            report_path = context.run_dir / "experiment_design.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # 更新 context
            context.set("experiment_design", experiment_design)

            return SkillResult(
                success=True,
                message="Successfully designed experiment plan",
                artifacts={
                    "experiment_design": experiment_design,
                    "design_json": str(output_path),
                    "design_report": str(report_path)
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Experiment design failed: {str(e)}",
                artifacts={}
            )

    def _design_experiments(
        self,
        innovation: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """使用 LLM 设计实验方案"""

        prompt = self._build_design_prompt(innovation, context)

        try:
            response = self.llm.generate(prompt, max_tokens=3000)

            # 解析实验设计
            design = {
                "innovation": innovation,
                "raw_response": response,
                "baseline_methods": self._extract_baselines(response),
                "proposed_method": self._extract_proposed_method(response),
                "datasets": self._extract_datasets(response),
                "metrics": self._extract_metrics(response),
                "ablation_components": self._extract_ablation_components(response),
                "ablation_experiments": self._generate_ablation_matrix(response),
                "implementation_steps": self._extract_implementation_steps(response)
            }

            return design

        except Exception as e:
            return {
                "error": str(e),
                "innovation": innovation,
                "baseline_methods": [],
                "datasets": [],
                "metrics": []
            }

    def _build_design_prompt(
        self,
        innovation: Dict[str, Any],
        context: AgentContext
    ) -> str:
        """构建实验设计提示"""

        prompt = f"""You are an expert research scientist designing a comprehensive experimental evaluation plan.

## Innovation to Evaluate

**Title**: {innovation.get('title', 'N/A')}

**Core Idea**: {innovation.get('core_idea', 'N/A')}

**Theoretical Foundation**: {innovation.get('theoretical_foundation', 'N/A')}

**Expected Benefits**: {innovation.get('expected_benefits', 'N/A')}

## Task

Design a complete experimental evaluation plan including baseline comparisons and ablation studies.

Provide the following sections:

### 1. BASELINE METHODS
List 3-5 baseline methods to compare against. For each:
- Method name
- Brief description
- Why it's a good baseline
- Expected performance level

### 2. PROPOSED METHOD
Describe the proposed method (implementing the innovation):
- Method name
- Key components/modules
- How it differs from baselines
- Implementation complexity

### 3. DATASETS
Suggest 2-4 appropriate datasets. For each:
- Dataset name
- Size and characteristics
- Why it's suitable for this evaluation
- Availability (public/private)

### 4. EVALUATION METRICS
List 3-6 evaluation metrics. For each:
- Metric name
- What it measures
- Why it's important for this task
- How to compute it

### 5. ABLATION COMPONENTS
Identify the key components of the proposed method that should be ablated:
- Component name
- What it does
- Expected impact if removed

### 6. ABLATION EXPERIMENTS
Design a matrix of ablation experiments:
- Full model (all components)
- Ablation 1: Remove component A
- Ablation 2: Remove component B
- Ablation 3: Remove component A+B
- etc.

### 7. IMPLEMENTATION STEPS
Outline the implementation steps:
1. Step 1
2. Step 2
3. ...

Be specific and technical. Format clearly with section headers.
"""

        return prompt

    def _extract_baselines(self, response: str) -> List[Dict[str, str]]:
        """提取基线方法"""
        baselines = []
        section = self._extract_section(response, "BASELINE METHODS")

        if section:
            items = self._parse_numbered_list(section)
            for item in items[:5]:
                baselines.append({
                    "name": self._extract_first_line(item),
                    "description": item,
                    "type": "baseline"
                })

        return baselines

    def _extract_proposed_method(self, response: str) -> Dict[str, Any]:
        """提取提出的方法"""
        section = self._extract_section(response, "PROPOSED METHOD")

        return {
            "name": "Proposed Method",
            "description": section if section else "See innovation description",
            "components": self._extract_components(section)
        }

    def _extract_components(self, text: str) -> List[str]:
        """提取方法组件"""
        components = []
        if "component" in text.lower():
            lines = text.split('\n')
            for line in lines:
                if "component" in line.lower() or line.strip().startswith('-'):
                    components.append(line.strip())
        return components[:10]

    def _extract_datasets(self, response: str) -> List[Dict[str, str]]:
        """提取数据集"""
        datasets = []
        section = self._extract_section(response, "DATASETS")

        if section:
            items = self._parse_numbered_list(section)
            for item in items[:4]:
                datasets.append({
                    "name": self._extract_first_line(item),
                    "description": item,
                    "availability": "public"  # 默认
                })

        return datasets

    def _extract_metrics(self, response: str) -> List[Dict[str, str]]:
        """提取评估指标"""
        metrics = []
        section = self._extract_section(response, "EVALUATION METRICS")

        if section:
            items = self._parse_numbered_list(section)
            for item in items[:6]:
                metrics.append({
                    "name": self._extract_first_line(item),
                    "description": item,
                    "type": "performance"
                })

        return metrics

    def _extract_ablation_components(self, response: str) -> List[Dict[str, str]]:
        """提取消融组件"""
        components = []
        section = self._extract_section(response, "ABLATION COMPONENTS")

        if section:
            items = self._parse_numbered_list(section)
            for item in items:
                components.append({
                    "name": self._extract_first_line(item),
                    "description": item,
                    "removable": True
                })

        return components

    def _generate_ablation_matrix(self, response: str) -> List[Dict[str, Any]]:
        """生成消融实验矩阵"""
        experiments = []
        section = self._extract_section(response, "ABLATION EXPERIMENTS")

        if section:
            items = self._parse_numbered_list(section)
            for i, item in enumerate(items):
                experiments.append({
                    "id": i + 1,
                    "name": self._extract_first_line(item),
                    "description": item,
                    "config": {}  # 具体配置需要后续填充
                })

        # 如果没有明确的消融实验，根据组件生成
        if not experiments:
            components = self._extract_ablation_components(response)
            if components:
                # 全模型
                experiments.append({
                    "id": 1,
                    "name": "Full Model",
                    "description": "All components enabled",
                    "config": {comp["name"]: True for comp in components}
                })

                # 单组件消融
                for i, comp in enumerate(components, 2):
                    config = {c["name"]: True for c in components}
                    config[comp["name"]] = False
                    experiments.append({
                        "id": i,
                        "name": f"w/o {comp['name']}",
                        "description": f"Remove {comp['name']}",
                        "config": config
                    })

        return experiments

    def _extract_implementation_steps(self, response: str) -> List[str]:
        """提取实现步骤"""
        section = self._extract_section(response, "IMPLEMENTATION STEPS")

        if section:
            return self._parse_numbered_list(section)

        return []

    def _extract_section(self, text: str, section_name: str) -> str:
        """提取特定章节"""
        import re
        patterns = [
            rf"###\s*\d*\.?\s*{section_name}(.*?)(?=###|\Z)",
            rf"##\s*\d*\.?\s*{section_name}(.*?)(?=##|\Z)",
            rf"{section_name}(.*?)(?=###|##|\Z)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return ""

    def _parse_numbered_list(self, text: str) -> List[str]:
        """解析编号列表"""
        import re
        items = re.findall(r'(?:^|\n)\s*(?:\d+\.|-)\s*(.+?)(?=\n\s*(?:\d+\.|-)|$)', text, re.DOTALL)
        return [item.strip() for item in items if item.strip()]

    def _extract_first_line(self, text: str) -> str:
        """提取第一行作为名称"""
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            # 移除可能的标记
            first_line = first_line.lstrip('*-•').strip()
            return first_line[:100]  # 限制长度
        return "Unnamed"

    def _generate_report(self, design: Dict[str, Any]) -> str:
        """生成实验设计报告"""

        report = "# Experiment Design Plan\n\n"

        # 创新点
        innovation = design.get("innovation", {})
        report += f"## Innovation: {innovation.get('title', 'N/A')}\n\n"
        report += f"{innovation.get('core_idea', 'N/A')}\n\n"
        report += "---\n\n"

        # 基线方法
        report += "## Baseline Methods\n\n"
        baselines = design.get("baseline_methods", [])
        for i, baseline in enumerate(baselines, 1):
            report += f"### {i}. {baseline['name']}\n\n"
            report += f"{baseline['description']}\n\n"

        report += "---\n\n"

        # 提出的方法
        report += "## Proposed Method\n\n"
        proposed = design.get("proposed_method", {})
        report += f"**Name**: {proposed.get('name', 'N/A')}\n\n"
        report += f"{proposed.get('description', 'N/A')}\n\n"

        components = proposed.get("components", [])
        if components:
            report += "**Key Components**:\n\n"
            for comp in components:
                report += f"- {comp}\n"
            report += "\n"

        report += "---\n\n"

        # 数据集
        report += "## Datasets\n\n"
        datasets = design.get("datasets", [])
        for i, dataset in enumerate(datasets, 1):
            report += f"### {i}. {dataset['name']}\n\n"
            report += f"{dataset['description']}\n\n"

        report += "---\n\n"

        # 评估指标
        report += "## Evaluation Metrics\n\n"
        metrics = design.get("metrics", [])
        for i, metric in enumerate(metrics, 1):
            report += f"{i}. **{metric['name']}**: {metric['description'][:200]}\n"
        report += "\n---\n\n"

        # 消融实验
        report += "## Ablation Study Design\n\n"

        ablation_comps = design.get("ablation_components", [])
        if ablation_comps:
            report += "### Components to Ablate\n\n"
            for comp in ablation_comps:
                report += f"- **{comp['name']}**: {comp['description'][:150]}\n"
            report += "\n"

        ablation_exps = design.get("ablation_experiments", [])
        if ablation_exps:
            report += "### Ablation Experiments\n\n"
            report += "| ID | Experiment | Description |\n"
            report += "|---|---|---|\n"
            for exp in ablation_exps:
                report += f"| {exp['id']} | {exp['name']} | {exp['description'][:100]} |\n"
            report += "\n"

        report += "---\n\n"

        # 实现步骤
        report += "## Implementation Steps\n\n"
        steps = design.get("implementation_steps", [])
        for i, step in enumerate(steps, 1):
            report += f"{i}. {step}\n"

        return report


# 注册技能
SKILL_META = SkillMeta(
    name="experiment_designer",
    description="Design comprehensive experiment plan including baselines and ablation studies",
    inputs_required=[],
    outputs_produced=["experiment_design", "design_json", "design_report"]
)
