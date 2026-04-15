"""
Innovation Proposer Skill - 提出创新点和改进方案
"""
import json
from typing import Dict, Any, List
from pathlib import Path
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta
from research_agent.llm import LLMClient


class InnovationProposerSkill(BaseSkill):
    """基于 gap 分析提出创新点和改进方案"""

    def __init__(self):
        super().__init__()
        self.llm = LLMClient()

    def execute(self, context: AgentContext) -> SkillResult:
        """
        提出创新点

        Args:
            context: 需要包含 gap_analysis
        """
        gap_analysis = context.get("gap_analysis")
        if not gap_analysis:
            return SkillResult(
                success=False,
                message="Missing gap_analysis in context",
                artifacts={}
            )

        # 获取其他上下文信息
        paper_digests = context.get("paper_digests", [])
        code_analysis = context.get("code_analysis", {})

        try:
            # 生成创新点
            innovations = self._propose_innovations(
                gap_analysis,
                paper_digests,
                code_analysis
            )

            # 保存结果
            output_path = context.run_dir / "innovation_proposals.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(innovations, f, indent=2, ensure_ascii=False)

            # 生成报告
            report = self._generate_report(innovations)
            report_path = context.run_dir / "innovation_proposals.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # 更新 context
            context.set("innovation_proposals", innovations)

            return SkillResult(
                success=True,
                message=f"Successfully proposed {len(innovations.get('proposals', []))} innovations",
                artifacts={
                    "innovations": innovations,
                    "innovations_json": str(output_path),
                    "innovations_report": str(report_path)
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Innovation proposal failed: {str(e)}",
                artifacts={}
            )

    def _propose_innovations(
        self,
        gap_analysis: Dict,
        paper_digests: List[Dict],
        code_analysis: Dict
    ) -> Dict[str, Any]:
        """使用 LLM 提出创新点"""

        prompt = self._build_innovation_prompt(gap_analysis, paper_digests, code_analysis)

        try:
            response = self.llm.generate(prompt, max_tokens=2500)

            # 解析创新点
            innovations = {
                "raw_response": response,
                "proposals": self._parse_proposals(response),
                "summary": self._extract_summary(response)
            }

            return innovations

        except Exception as e:
            return {
                "error": str(e),
                "proposals": [],
                "summary": "Innovation proposal failed"
            }

    def _build_innovation_prompt(
        self,
        gap_analysis: Dict,
        paper_digests: List[Dict],
        code_analysis: Dict
    ) -> str:
        """构建创新提案提示"""

        prompt = """You are a creative research scientist proposing innovative solutions to identified research gaps.

## Research Gaps Identified

"""

        # 添加 gap 分析摘要
        if "summary" in gap_analysis:
            prompt += f"**Summary**: {gap_analysis['summary']}\n\n"

        # 添加局限性
        if gap_analysis.get("limitations"):
            prompt += "### Key Limitations\n\n"
            for i, lim in enumerate(gap_analysis["limitations"][:3], 1):
                prompt += f"{i}. {lim['description'][:200]}\n"
            prompt += "\n"

        # 添加未解决的问题
        if gap_analysis.get("unsolved_problems"):
            prompt += "### Unsolved Problems\n\n"
            for i, prob in enumerate(gap_analysis["unsolved_problems"][:3], 1):
                prompt += f"{i}. {prob['description'][:200]}\n"
            prompt += "\n"

        # 添加改进方向
        if gap_analysis.get("improvement_directions"):
            prompt += "### Suggested Improvement Directions\n\n"
            for i, dir in enumerate(gap_analysis["improvement_directions"][:3], 1):
                prompt += f"{i}. {dir['description'][:200]}\n"
            prompt += "\n"

        prompt += """
## Task

Based on the identified gaps, propose 3-5 concrete, innovative research ideas.

For EACH innovation proposal, provide:

### INNOVATION [Number]: [Short Title]

**1. Core Idea**
- Describe the innovation in 2-3 sentences
- What makes it novel?

**2. Theoretical Foundation**
- Why should this work?
- What principles/theories support it?

**3. Addresses Which Gap**
- Which limitation/problem does it solve?
- How does it improve upon existing methods?

**4. Expected Benefits**
- Performance improvements (quantitative if possible)
- Other advantages (efficiency, interpretability, etc.)

**5. Implementation Difficulty**
- Difficulty level: Low / Medium / High
- Key challenges
- Required resources

**6. Priority**
- Priority: High / Medium / Low
- Justification for priority

Format each proposal clearly with these sections. Be specific and technical.
"""

        return prompt

    def _parse_proposals(self, response: str) -> List[Dict[str, Any]]:
        """解析创新提案"""
        import re

        proposals = []

        # 查找所有 INNOVATION 章节
        innovation_pattern = r'###\s*INNOVATION\s*(\d+):\s*(.+?)(?=###\s*INNOVATION|\Z)'
        matches = re.finditer(innovation_pattern, response, re.IGNORECASE | re.DOTALL)

        for match in matches:
            number = match.group(1)
            content = match.group(2)
            title = content.split('\n')[0].strip()

            proposal = {
                "id": int(number),
                "title": title,
                "core_idea": self._extract_field(content, "Core Idea"),
                "theoretical_foundation": self._extract_field(content, "Theoretical Foundation"),
                "addresses_gap": self._extract_field(content, "Addresses Which Gap"),
                "expected_benefits": self._extract_field(content, "Expected Benefits"),
                "implementation_difficulty": self._extract_difficulty(content),
                "priority": self._extract_priority(content),
                "full_description": content.strip()
            }

            proposals.append(proposal)

        # 如果没有找到结构化的提案，尝试简单分割
        if not proposals:
            proposals = self._fallback_parse(response)

        return proposals

    def _extract_field(self, text: str, field_name: str) -> str:
        """提取特定字段内容"""
        import re

        pattern = rf'\*\*\d*\.?\s*{field_name}\*\*(.*?)(?=\*\*\d*\.|\Z)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1).strip()
        return "Not specified"

    def _extract_difficulty(self, text: str) -> str:
        """提取实现难度"""
        text_lower = text.lower()
        if "difficulty" in text_lower:
            if "low" in text_lower:
                return "Low"
            elif "high" in text_lower:
                return "High"
            else:
                return "Medium"
        return "Medium"

    def _extract_priority(self, text: str) -> str:
        """提取优先级"""
        text_lower = text.lower()
        if "priority" in text_lower:
            if "high" in text_lower:
                return "High"
            elif "low" in text_lower:
                return "Low"
            else:
                return "Medium"
        return "Medium"

    def _fallback_parse(self, response: str) -> List[Dict[str, Any]]:
        """备用解析方法"""
        # 简单地按段落分割
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]

        proposals = []
        for i, para in enumerate(paragraphs[:5], 1):
            if len(para) > 50:  # 过滤太短的段落
                proposals.append({
                    "id": i,
                    "title": f"Innovation {i}",
                    "core_idea": para[:300],
                    "theoretical_foundation": "See full description",
                    "addresses_gap": "See full description",
                    "expected_benefits": "See full description",
                    "implementation_difficulty": "Medium",
                    "priority": "Medium",
                    "full_description": para
                })

        return proposals

    def _extract_summary(self, response: str) -> str:
        """提取摘要"""
        lines = response.split('\n')
        if lines:
            return lines[0][:200]
        return "Innovation proposals generated"

    def _generate_report(self, innovations: Dict[str, Any]) -> str:
        """生成创新提案报告"""

        report = "# Innovation Proposals\n\n"

        report += "## Summary\n\n"
        report += innovations.get("summary", "No summary available")
        report += "\n\n---\n\n"

        proposals = innovations.get("proposals", [])

        if not proposals:
            report += "No innovation proposals generated.\n"
            return report

        # 按优先级排序
        high_priority = [p for p in proposals if p.get("priority") == "High"]
        medium_priority = [p for p in proposals if p.get("priority") == "Medium"]
        low_priority = [p for p in proposals if p.get("priority") == "Low"]

        sorted_proposals = high_priority + medium_priority + low_priority

        for proposal in sorted_proposals:
            report += f"## Innovation {proposal['id']}: {proposal['title']}\n\n"

            report += f"**Priority**: {proposal.get('priority', 'N/A')} | "
            report += f"**Difficulty**: {proposal.get('implementation_difficulty', 'N/A')}\n\n"

            report += "### Core Idea\n\n"
            report += proposal.get('core_idea', 'Not specified')
            report += "\n\n"

            report += "### Theoretical Foundation\n\n"
            report += proposal.get('theoretical_foundation', 'Not specified')
            report += "\n\n"

            report += "### Addresses Which Gap\n\n"
            report += proposal.get('addresses_gap', 'Not specified')
            report += "\n\n"

            report += "### Expected Benefits\n\n"
            report += proposal.get('expected_benefits', 'Not specified')
            report += "\n\n"

            report += "---\n\n"

        return report


# 注册技能
SKILL_META = SkillMeta(
    name="innovation_proposer",
    description="Propose innovative research ideas based on gap analysis",
    skill_class=InnovationProposerSkill,
    required_context=["gap_analysis"],
    optional_context=["paper_digests", "code_analysis"],
    outputs=["innovation_proposals", "innovations_json", "innovations_report"]
)
