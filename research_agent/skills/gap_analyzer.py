"""
Gap Analyzer Skill - 分析研究空白和方法局限性
"""
import json
from typing import Dict, Any, List
from pathlib import Path
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta
from research_agent.llm import LLMClient


class GapAnalyzerSkill(BaseSkill):
    """分析现有方法的局限性和研究空白"""

    def __init__(self):
        super().__init__()
        self.llm = LLMClient()

    def run(self, context: AgentContext, llm) -> SkillResult:
        """
        分析研究空白

        Args:
            context: 需要包含论文分析结果和/或代码分析结果
        """
        # 收集所有可用的分析结果
        paper_digests = context.get("paper_digests", [])
        code_analysis = context.get("code_analysis", {})
        comparison_matrix = context.get("comparison_matrix", {})

        if not paper_digests and not code_analysis:
            return SkillResult(
                success=False,
                message="No paper digests or code analysis found in context",
                artifacts={}
            )

        try:
            # 生成 gap 分析
            gap_analysis = self._analyze_gaps(
                paper_digests,
                code_analysis,
                comparison_matrix
            )

            # 保存结果
            output_path = context.run_dir / "gap_analysis.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(gap_analysis, f, indent=2, ensure_ascii=False)

            # 生成报告
            report = self._generate_report(gap_analysis)
            report_path = context.run_dir / "gap_analysis.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # 更新 context
            context.set("gap_analysis", gap_analysis)

            return SkillResult(
                success=True,
                message="Successfully analyzed research gaps",
                artifacts={
                    "gap_analysis": gap_analysis,
                    "gap_analysis_json": str(output_path),
                    "gap_analysis_report": str(report_path)
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Gap analysis failed: {str(e)}",
                artifacts={}
            )

    def _analyze_gaps(
        self,
        paper_digests: List[Dict],
        code_analysis: Dict,
        comparison_matrix: Dict
    ) -> Dict[str, Any]:
        """使用 LLM 分析研究空白"""

        # 构建分析提示
        prompt = self._build_analysis_prompt(
            paper_digests,
            code_analysis,
            comparison_matrix
        )

        # 调用 LLM
        try:
            response = self.llm.complete("", prompt, max_tokens=2000)

            # 解析响应
            gap_analysis = {
                "raw_analysis": response,
                "limitations": self._extract_limitations(response),
                "unsolved_problems": self._extract_problems(response),
                "improvement_directions": self._extract_directions(response),
                "summary": self._extract_summary(response)
            }

            return gap_analysis

        except Exception as e:
            return {
                "error": str(e),
                "limitations": [],
                "unsolved_problems": [],
                "improvement_directions": [],
                "summary": "Analysis failed"
            }

    def _build_analysis_prompt(
        self,
        paper_digests: List[Dict],
        code_analysis: Dict,
        comparison_matrix: Dict
    ) -> str:
        """构建分析提示"""

        prompt = """You are a research expert analyzing the current state of research in a specific area.

Based on the following information, identify research gaps, limitations, and opportunities for innovation.

"""

        # 添加论文信息
        if paper_digests:
            prompt += "## Analyzed Papers\n\n"
            for i, digest in enumerate(paper_digests[:5], 1):  # 最多5篇
                prompt += f"### Paper {i}\n"
                if "metadata" in digest:
                    prompt += f"**Title**: {digest['metadata'].get('title', 'N/A')}\n"
                if "summary" in digest:
                    prompt += f"**Summary**: {digest['summary'][:500]}...\n"
                if "claims" in digest:
                    prompt += f"**Key Claims**: {digest['claims'][:500]}...\n"
                prompt += "\n"

        # 添加代码分析
        if code_analysis:
            prompt += "## Code Implementation Analysis\n\n"
            if "llm_analysis" in code_analysis:
                prompt += code_analysis["llm_analysis"][:1000]
                prompt += "\n\n"

        # 添加对比矩阵
        if comparison_matrix:
            prompt += "## Method Comparison\n\n"
            prompt += str(comparison_matrix)[:1000]
            prompt += "\n\n"

        prompt += """
## Task

Please provide a comprehensive gap analysis with the following structure:

### 1. LIMITATIONS
List 3-5 key limitations of current methods. For each limitation:
- Describe the limitation clearly
- Explain why it matters
- Provide evidence from the papers/code

### 2. UNSOLVED PROBLEMS
Identify 3-5 important problems that remain unsolved. For each problem:
- State the problem clearly
- Explain its significance
- Discuss why current methods fail to solve it

### 3. IMPROVEMENT DIRECTIONS
Suggest 3-5 promising directions for improvement. For each direction:
- Describe the direction
- Explain the potential benefits
- Assess feasibility (high/medium/low)

### 4. SUMMARY
Provide a brief summary (2-3 sentences) of the most critical gaps and opportunities.

Format your response clearly with these section headers.
"""

        return prompt

    def _extract_limitations(self, response: str) -> List[Dict[str, str]]:
        """从响应中提取局限性"""
        limitations = []

        # 简单的文本解析（可以改进）
        if "LIMITATIONS" in response or "Limitations" in response:
            section = self._extract_section(response, "LIMITATIONS")
            items = self._parse_numbered_list(section)
            for item in items[:5]:
                limitations.append({
                    "description": item,
                    "severity": "medium"  # 可以用 LLM 进一步分析
                })

        return limitations

    def _extract_problems(self, response: str) -> List[Dict[str, str]]:
        """从响应中提取未解决的问题"""
        problems = []

        if "UNSOLVED PROBLEMS" in response or "Unsolved Problems" in response:
            section = self._extract_section(response, "UNSOLVED PROBLEMS")
            items = self._parse_numbered_list(section)
            for item in items[:5]:
                problems.append({
                    "description": item,
                    "importance": "high"
                })

        return problems

    def _extract_directions(self, response: str) -> List[Dict[str, str]]:
        """从响应中提取改进方向"""
        directions = []

        if "IMPROVEMENT DIRECTIONS" in response or "Improvement Directions" in response:
            section = self._extract_section(response, "IMPROVEMENT DIRECTIONS")
            items = self._parse_numbered_list(section)
            for item in items[:5]:
                # 尝试提取可行性
                feasibility = "medium"
                if "high" in item.lower():
                    feasibility = "high"
                elif "low" in item.lower():
                    feasibility = "low"

                directions.append({
                    "description": item,
                    "feasibility": feasibility
                })

        return directions

    def _extract_summary(self, response: str) -> str:
        """从响应中提取摘要"""
        if "SUMMARY" in response or "Summary" in response:
            section = self._extract_section(response, "SUMMARY")
            return section.strip()
        return "No summary available"

    def _extract_section(self, text: str, section_name: str) -> str:
        """提取特定章节的内容"""
        import re

        # 尝试多种格式
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

        # 匹配 "1. xxx" 或 "- xxx" 格式
        items = re.findall(r'(?:^|\n)\s*(?:\d+\.|-)\s*(.+?)(?=\n\s*(?:\d+\.|-)|$)', text, re.DOTALL)
        return [item.strip() for item in items if item.strip()]

    def _generate_report(self, gap_analysis: Dict[str, Any]) -> str:
        """生成 gap 分析报告"""

        report = "# Research Gap Analysis\n\n"

        report += "## Summary\n\n"
        report += gap_analysis.get("summary", "No summary available")
        report += "\n\n---\n\n"

        report += "## Limitations of Current Methods\n\n"
        limitations = gap_analysis.get("limitations", [])
        if limitations:
            for i, lim in enumerate(limitations, 1):
                report += f"### {i}. {lim['description'][:100]}...\n\n"
                report += f"**Severity**: {lim['severity']}\n\n"
                report += f"{lim['description']}\n\n"
        else:
            report += "No limitations identified.\n\n"

        report += "---\n\n"

        report += "## Unsolved Problems\n\n"
        problems = gap_analysis.get("unsolved_problems", [])
        if problems:
            for i, prob in enumerate(problems, 1):
                report += f"### {i}. {prob['description'][:100]}...\n\n"
                report += f"**Importance**: {prob['importance']}\n\n"
                report += f"{prob['description']}\n\n"
        else:
            report += "No unsolved problems identified.\n\n"

        report += "---\n\n"

        report += "## Improvement Directions\n\n"
        directions = gap_analysis.get("improvement_directions", [])
        if directions:
            for i, dir in enumerate(directions, 1):
                report += f"### {i}. {dir['description'][:100]}...\n\n"
                report += f"**Feasibility**: {dir['feasibility']}\n\n"
                report += f"{dir['description']}\n\n"
        else:
            report += "No improvement directions identified.\n\n"

        return report


# 注册技能
SKILL_META = SkillMeta(
    name="gap_analyzer",
    description="Analyze research gaps, limitations, and opportunities for innovation",
    inputs_required=[],
    outputs_produced=["gap_analysis", "gap_analysis_json", "gap_analysis_report"]
)
