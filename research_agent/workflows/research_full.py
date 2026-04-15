"""
Full Research Workflow - 完整的自动化科研流程
"""
from typing import Dict, Any, List
from research_agent.base import BaseWorkflow, WorkflowResult
from research_agent.context import AgentContext
from research_agent.registry import WorkflowMeta


class FullResearchWorkflow(BaseWorkflow):
    """
    完整的自动化科研工作流

    从文献调研到实验执行，再到报告生成的端到端流程
    """

    def execute(self, context: AgentContext) -> WorkflowResult:
        """
        执行完整研究流程

        Args:
            context: 需要包含 query（研究主题）
        """
        query = context.get("query")

        if not query:
            return WorkflowResult(
                success=False,
                message="Missing 'query' in context. Please provide a research topic.",
                artifacts={}
            )

        results = []

        try:
            # ============================================================
            # Phase 1: Literature Review & Gap Analysis
            # ============================================================
            self.log("=" * 60)
            self.log("PHASE 1: Literature Review & Gap Analysis")
            self.log("=" * 60)

            # 1.1 搜索论文
            self.log("\n[1/10] Searching papers...")
            result = self.run_skill("paper_search", context)
            results.append(("paper_search", result))

            if not result.success:
                return self._early_exit(results, "Paper search failed")

            # 1.2 下载论文
            self.log("\n[2/10] Downloading papers...")
            result = self.run_skill("paper_download", context)
            results.append(("paper_download", result))

            # 1.3 阅读论文
            self.log("\n[3/10] Reading and analyzing papers...")
            result = self.run_skill("paper_reader", context)
            results.append(("paper_reader", result))

            if not result.success:
                return self._early_exit(results, "Paper reading failed")

            # 1.4 生成综述
            self.log("\n[4/10] Generating literature survey...")
            result = self.run_skill("survey_writer", context)
            results.append(("survey_writer", result))

            # ============================================================
            # Phase 2: Code Analysis & Innovation Design
            # ============================================================
            self.log("\n" + "=" * 60)
            self.log("PHASE 2: Code Analysis & Innovation Design")
            self.log("=" * 60)

            # 2.1 搜索相关代码仓库
            self.log("\n[5/10] Searching GitHub repositories...")
            result = self.run_skill("github_search", context)
            results.append(("github_search", result))

            if result.success:
                # 2.2 克隆仓库
                self.log("\n[6/10] Cloning top repository...")

                # 获取第一个仓库
                repos = context.get("github_repos", [])
                if repos:
                    context.set("repo_url", repos[0].get("url"))
                    result = self.run_skill("github_clone", context)
                    results.append(("github_clone", result))

                    if result.success:
                        # 2.3 分析代码
                        self.log("\n[7/10] Analyzing code...")
                        result = self.run_skill("enhanced_code_analyzer", context)
                        results.append(("enhanced_code_analyzer", result))

            # 2.4 分析研究空白
            self.log("\n[8/10] Analyzing research gaps...")
            result = self.run_skill("gap_analyzer", context)
            results.append(("gap_analyzer", result))

            if not result.success:
                return self._early_exit(results, "Gap analysis failed")

            # 2.5 提出创新点
            self.log("\n[9/10] Proposing innovations...")
            result = self.run_skill("innovation_proposer", context)
            results.append(("innovation_proposer", result))

            if not result.success:
                return self._early_exit(results, "Innovation proposal failed")

            # ============================================================
            # Phase 3: Experiment Design & Execution
            # ============================================================
            self.log("\n" + "=" * 60)
            self.log("PHASE 3: Experiment Design & Execution")
            self.log("=" * 60)

            # 3.1 设计实验
            self.log("\n[10/10] Designing experiments...")
            result = self.run_skill("experiment_designer", context)
            results.append(("experiment_designer", result))

            if not result.success:
                return self._early_exit(results, "Experiment design failed")

            # 3.2 配置环境
            self.log("\n[11/10] Setting up environment...")

            cloned_repo = context.get("cloned_repo_path")
            if cloned_repo:
                result = self.run_skill("environment_setup", context)
                results.append(("environment_setup", result))
            else:
                self.log("Skipping environment setup (no cloned repo)")

            # 3.3 运行实验
            self.log("\n[12/10] Running experiments...")
            result = self.run_skill("experiment_runner", context)
            results.append(("experiment_runner", result))

            if not result.success:
                self.log("Warning: Experiment execution had issues")

            # ============================================================
            # Phase 4: Ablation Study & Analysis
            # ============================================================
            self.log("\n" + "=" * 60)
            self.log("PHASE 4: Ablation Study & Analysis")
            self.log("=" * 60)

            # 4.1 消融实验分析
            self.log("\n[13/10] Analyzing ablation experiments...")
            result = self.run_skill("ablation_study", context)
            results.append(("ablation_study", result))

            if not result.success:
                self.log("Warning: Ablation analysis had issues")

            # ============================================================
            # Phase 5: Report Generation
            # ============================================================
            self.log("\n" + "=" * 60)
            self.log("PHASE 5: Report Generation")
            self.log("=" * 60)

            # 5.1 生成完整报告
            self.log("\n[14/10] Generating comprehensive report...")
            result = self.run_skill("comprehensive_report", context)
            results.append(("comprehensive_report", result))

            # ============================================================
            # Summary
            # ============================================================
            self.log("\n" + "=" * 60)
            self.log("WORKFLOW COMPLETED")
            self.log("=" * 60)

            summary = self._generate_summary(results, context)

            return WorkflowResult(
                success=True,
                message="Full research workflow completed successfully",
                artifacts={
                    "summary": summary,
                    "results": results,
                    "run_dir": str(context.run_dir)
                }
            )

        except Exception as e:
            return WorkflowResult(
                success=False,
                message=f"Workflow failed: {str(e)}",
                artifacts={"results": results}
            )

    def _early_exit(
        self,
        results: List[tuple],
        reason: str
    ) -> WorkflowResult:
        """提前退出工作流"""

        return WorkflowResult(
            success=False,
            message=f"Workflow stopped: {reason}",
            artifacts={"results": results}
        )

    def _generate_summary(
        self,
        results: List[tuple],
        context: AgentContext
    ) -> Dict[str, Any]:
        """生成工作流摘要"""

        summary = {
            "total_steps": len(results),
            "successful_steps": sum(1 for _, r in results if r.success),
            "failed_steps": sum(1 for _, r in results if not r.success),
            "steps": []
        }

        for skill_name, result in results:
            summary["steps"].append({
                "skill": skill_name,
                "success": result.success,
                "message": result.message
            })

        # 关键输出
        summary["key_outputs"] = {
            "papers_found": len(context.get("paper_digests", [])),
            "innovations_proposed": len(context.get("innovation_proposals", {}).get("proposals", [])),
            "experiments_run": context.get("experiment_results", {}).get("total_experiments", 0),
            "report_generated": context.get("comprehensive_report") is not None
        }

        return summary


# 注册工作流
WORKFLOW_META = WorkflowMeta(
    name="research_full",
    description="Complete automated research workflow from literature review to report generation",
    workflow_class=FullResearchWorkflow,
    required_context=["query"],
    optional_context=["max_papers", "github_language", "experiment_timeout"],
    outputs=["summary", "results", "run_dir"]
)
