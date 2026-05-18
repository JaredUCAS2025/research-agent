"""Fact Validator Skill - 验证AI生成内容的真实性，防止幻觉"""

from __future__ import annotations
from typing import TYPE_CHECKING
import json
import re

if TYPE_CHECKING:
    from ..context import AgentContext
    from ..llm import LLMClient
    from ..base import SkillResult

from ..base import BaseSkill
from ..registry import SkillMeta


class FactValidatorSkill(BaseSkill):
    """验证AI生成内容的事实准确性，防止幻觉"""

    meta = SkillMeta(
        name="fact_validator",
        description="验证AI生成内容的事实准确性，标记可疑内容，防止AI幻觉",
        inputs_required=["innovation_proposal", "experiment_results"],
        outputs_produced=["validation_report", "confidence_scores"],
        artifacts=["validation_report.json"],
        modes=["research_full"],
    )

    def execute(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        """执行事实验证"""

        context.report_progress("fact_validator", "开始验证AI生成内容...", 0.1)

        # 获取需要验证的内容
        innovation = context.get("innovation_proposal", {})
        experiments = context.get("experiment_results", {})
        gap_analysis = context.get("gap_analysis", {})
        code_analysis = context.get("code_analysis", {})

        validation_report = {
            "overall_confidence": 0.0,
            "validations": [],
            "warnings": [],
            "recommendations": []
        }

        # 1. 验证创新点的可行性
        context.report_progress("fact_validator", "验证创新点可行性...", 0.2)
        innovation_validation = self._validate_innovation(llm, innovation, gap_analysis, code_analysis)
        validation_report["validations"].append(innovation_validation)

        # 2. 验证实验结果的合理性
        context.report_progress("fact_validator", "验证实验结果合理性...", 0.4)
        experiment_validation = self._validate_experiments(llm, experiments, innovation)
        validation_report["validations"].append(experiment_validation)

        # 3. 交叉验证：检查内容一致性
        context.report_progress("fact_validator", "交叉验证内容一致性...", 0.6)
        consistency_check = self._check_consistency(llm, innovation, experiments, gap_analysis)
        validation_report["validations"].append(consistency_check)

        # 4. 检测可疑的数值和声明
        context.report_progress("fact_validator", "检测可疑数值和声明...", 0.8)
        suspicious_items = self._detect_suspicious_claims(innovation, experiments)
        validation_report["warnings"].extend(suspicious_items)

        # 5. 计算总体置信度
        overall_confidence = self._calculate_confidence(validation_report["validations"])
        validation_report["overall_confidence"] = overall_confidence

        # 6. 生成建议
        validation_report["recommendations"] = self._generate_recommendations(validation_report)

        # 保存验证报告
        context.save_json("validation_report.json", validation_report)
        context.set("validation_report", validation_report)
        context.set("fact_check_confidence", overall_confidence)

        context.report_progress("fact_validator", "事实验证完成", 1.0)

        # 根据置信度决定是否警告
        from ..base import SkillResult
        if overall_confidence < 0.6:
            return SkillResult(
                name=self.meta.name,
                message=f"⚠️ 验证完成，但置信度较低 ({overall_confidence:.1%})，请仔细检查标记的问题"
            )
        elif overall_confidence < 0.8:
            return SkillResult(
                name=self.meta.name,
                message=f"✓ 验证完成，置信度中等 ({overall_confidence:.1%})，建议审查部分内容"
            )
        else:
            return SkillResult(
                name=self.meta.name,
                message=f"✓ 验证完成，置信度高 ({overall_confidence:.1%})"
            )

    def _validate_innovation(self, llm: LLMClient, innovation: dict,
                            gap_analysis: dict, code_analysis: dict) -> dict:
        """验证创新点的可行性和合理性"""

        system_prompt = """你是一位严谨的科研审查专家。请评估提出的创新点是否：
1. 技术上可行
2. 与现有代码库兼容
3. 真正解决了识别的研究空白
4. 没有明显的逻辑漏洞

请给出：
- feasibility_score: 可行性评分 (0-1)
- issues: 发现的问题列表
- evidence: 支持你判断的证据
"""

        user_prompt = f"""
创新点：
{json.dumps(innovation, ensure_ascii=False, indent=2)}

研究空白：
{json.dumps(gap_analysis, ensure_ascii=False, indent=2)}

代码分析：
{json.dumps(code_analysis, ensure_ascii=False, indent=2)}

请以JSON格式返回验证结果。
"""

        try:
            result = llm.complete_json(system_prompt, user_prompt, timeout=120.0)
            return {
                "category": "innovation_feasibility",
                "score": result.get("feasibility_score", 0.5),
                "issues": result.get("issues", []),
                "evidence": result.get("evidence", "")
            }
        except Exception as e:
            return {
                "category": "innovation_feasibility",
                "score": 0.5,
                "issues": [f"验证失败: {str(e)}"],
                "evidence": ""
            }

    def _validate_experiments(self, llm: LLMClient, experiments: dict, innovation: dict) -> dict:
        """验证实验结果的合理性"""

        system_prompt = """你是一位实验验证专家。请检查实验结果是否：
1. 与提出的方法相符
2. 数值合理（没有异常高或异常低的值）
3. 改进幅度可信
4. 实验设置完整

请给出：
- validity_score: 有效性评分 (0-1)
- anomalies: 发现的异常
- missing_info: 缺失的信息
"""

        user_prompt = f"""
实验结果：
{json.dumps(experiments, ensure_ascii=False, indent=2)}

提出的方法：
{json.dumps(innovation, ensure_ascii=False, indent=2)}

请以JSON格式返回验证结果。
"""

        try:
            result = llm.complete_json(system_prompt, user_prompt, timeout=120.0)
            return {
                "category": "experiment_validity",
                "score": result.get("validity_score", 0.5),
                "issues": result.get("anomalies", []),
                "missing": result.get("missing_info", [])
            }
        except Exception as e:
            return {
                "category": "experiment_validity",
                "score": 0.5,
                "issues": [f"验证失败: {str(e)}"],
                "missing": []
            }

    def _check_consistency(self, llm: LLMClient, innovation: dict,
                          experiments: dict, gap_analysis: dict) -> dict:
        """检查不同部分之间的一致性"""

        system_prompt = """你是一位逻辑一致性检查专家。请检查：
1. 创新点是否真正解决了识别的研究空白
2. 实验设计是否验证了创新点
3. 各部分描述是否一致（没有矛盾）

请给出：
- consistency_score: 一致性评分 (0-1)
- contradictions: 发现的矛盾
- alignment_issues: 对齐问题
"""

        user_prompt = f"""
创新点：
{json.dumps(innovation, ensure_ascii=False, indent=2)}

实验结果：
{json.dumps(experiments, ensure_ascii=False, indent=2)}

研究空白：
{json.dumps(gap_analysis, ensure_ascii=False, indent=2)}

请以JSON格式返回一致性检查结果。
"""

        try:
            result = llm.complete_json(system_prompt, user_prompt, timeout=120.0)
            return {
                "category": "consistency",
                "score": result.get("consistency_score", 0.5),
                "issues": result.get("contradictions", []) + result.get("alignment_issues", [])
            }
        except Exception as e:
            return {
                "category": "consistency",
                "score": 0.5,
                "issues": [f"验证失败: {str(e)}"]
            }

    def _detect_suspicious_claims(self, innovation: dict, experiments: dict) -> list:
        """检测可疑的数值和声明"""
        warnings = []

        # 检查实验结果中的异常数值
        if isinstance(experiments, dict):
            results = experiments.get("results", {})
            for metric, value in results.items():
                if isinstance(value, (int, float)):
                    # 检查是否有异常高的改进
                    if value > 50:  # 超过50%的改进通常需要仔细验证
                        warnings.append({
                            "type": "suspicious_improvement",
                            "metric": metric,
                            "value": value,
                            "message": f"{metric}的改进幅度({value}%)异常高，需要验证"
                        })
                    # 检查是否有完美的数值（可能是幻觉）
                    if value == 100 or value == 1.0:
                        warnings.append({
                            "type": "perfect_score",
                            "metric": metric,
                            "value": value,
                            "message": f"{metric}达到完美值，这在实际中很少见"
                        })

        # 检查创新点中的绝对性声明
        innovation_text = json.dumps(innovation, ensure_ascii=False)
        absolute_terms = ["完全解决", "彻底消除", "100%", "完美", "绝对", "永远", "从不"]
        for term in absolute_terms:
            if term in innovation_text:
                warnings.append({
                    "type": "absolute_claim",
                    "term": term,
                    "message": f"发现绝对性声明'{term}'，科学研究中应避免绝对化表述"
                })

        return warnings

    def _calculate_confidence(self, validations: list) -> float:
        """计算总体置信度"""
        if not validations:
            return 0.5

        scores = [v.get("score", 0.5) for v in validations]
        return sum(scores) / len(scores)

    def _generate_recommendations(self, report: dict) -> list:
        """生成改进建议"""
        recommendations = []
        confidence = report["overall_confidence"]

        if confidence < 0.6:
            recommendations.append("总体置信度较低，建议重新审查所有标记的问题")

        if len(report["warnings"]) > 5:
            recommendations.append("发现多个可疑声明，建议使用更保守的表述")

        for validation in report["validations"]:
            if validation.get("score", 1.0) < 0.6:
                category = validation.get("category", "unknown")
                recommendations.append(f"'{category}'部分需要改进，请查看具体问题")

        if not recommendations:
            recommendations.append("内容质量良好，可以继续后续步骤")

        return recommendations
