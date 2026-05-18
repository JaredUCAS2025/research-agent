"""LaTeX Paper Writer Skill - 生成完整的学术论文LaTeX文档"""

from __future__ import annotations
from pathlib import Path
import json
import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import AgentContext
    from ..llm import LLMClient
    from ..base import SkillResult

from ..base import BaseSkill
from ..registry import SkillMeta


class LaTeXPaperWriterSkill(BaseSkill):
    """生成完整的LaTeX格式学术论文，包含所有图表和引用"""

    meta = SkillMeta(
        name="latex_paper_writer",
        description="生成完整的LaTeX格式学术论文，包含所有章节、图表、引用和打包",
        inputs_required=["innovation_proposal", "experiment_results", "diagrams"],
        outputs_produced=["latex_paper", "paper_package"],
        artifacts=["paper.tex", "paper.zip"],
        modes=["research_full"],
    )

    def execute(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        """生成LaTeX论文并打包"""

        # 获取必要的数据
        innovation = context.get("innovation_proposal", {})
        experiments = context.get("experiment_results", {})
        ablation = context.get("ablation_results", {})
        gap_analysis = context.get("gap_analysis", {})

        # 构建论文内容提示
        prompt = self._build_paper_prompt(innovation, experiments, ablation, gap_analysis)

        # 生成论文各部分
        context.report_progress("latex_paper_writer", "正在生成论文摘要和引言...", 0.1)
        abstract_intro = self._generate_abstract_intro(llm, prompt, innovation)

        context.report_progress("latex_paper_writer", "正在生成相关工作...", 0.2)
        related_work = self._generate_related_work(llm, gap_analysis)

        context.report_progress("latex_paper_writer", "正在生成方法论...", 0.4)
        methodology = self._generate_methodology(llm, innovation)

        context.report_progress("latex_paper_writer", "正在生成实验部分...", 0.6)
        experiments_section = self._generate_experiments(llm, experiments, ablation)

        context.report_progress("latex_paper_writer", "正在生成结论...", 0.8)
        conclusion = self._generate_conclusion(llm, innovation, experiments)

        # 组装完整LaTeX文档
        context.report_progress("latex_paper_writer", "正在组装LaTeX文档...", 0.9)
        latex_content = self._assemble_latex(
            abstract_intro, related_work, methodology,
            experiments_section, conclusion, context
        )

        # 保存LaTeX文件
        latex_path = context.save_text("paper.tex", latex_content)

        # 创建压缩包
        zip_path = self._create_package(context, latex_path)

        # 保存到context
        context.set("latex_paper", latex_content)
        context.set("paper_package_path", str(zip_path))

        context.report_progress("latex_paper_writer", "LaTeX论文生成完成", 1.0)

        return self.success(
            message=f"已生成LaTeX论文并打包到 {zip_path.name}",
            data={"latex_path": str(latex_path), "package_path": str(zip_path)}
        )

    def _build_paper_prompt(self, innovation, experiments, ablation, gap_analysis) -> str:
        """构建论文生成的基础提示"""
        return f"""
基于以下研究内容生成高质量学术论文：

创新点：
{json.dumps(innovation, ensure_ascii=False, indent=2)}

实验结果：
{json.dumps(experiments, ensure_ascii=False, indent=2)}

消融实验：
{json.dumps(ablation, ensure_ascii=False, indent=2)}

研究空白分析：
{json.dumps(gap_analysis, ensure_ascii=False, indent=2)}
"""

    def _generate_abstract_intro(self, llm: LLMClient, prompt: str, innovation: dict) -> str:
        """生成摘要和引言"""
        system_prompt = """你是一位经验丰富的学术论文写作专家。
请生成论文的摘要(Abstract)和引言(Introduction)部分。

要求：
1. 摘要150-200词，包含：背景、问题、方法、结果、结论
2. 引言包含：研究背景、现有问题、本文贡献、论文结构
3. 使用学术化语言，避免口语化表达
4. 突出创新点和贡献
5. 直接输出LaTeX格式的内容，不要包含\\section命令（会在组装时添加）
"""

        user_prompt = f"""{prompt}

请生成Abstract和Introduction部分的LaTeX内容。
创新点：{innovation.get('innovation_points', [])}
"""

        return llm.complete(system_prompt, user_prompt, timeout=180.0)

    def _generate_related_work(self, llm: LLMClient, gap_analysis: dict) -> str:
        """生成相关工作部分"""
        system_prompt = """你是一位学术论文写作专家。
请生成Related Work部分，综述现有研究并指出研究空白。

要求：
1. 按主题组织相关工作
2. 客观评价现有方法的优缺点
3. 明确指出研究空白
4. 自然过渡到本文工作
5. 直接输出LaTeX格式内容
"""

        user_prompt = f"""
研究空白分析：
{json.dumps(gap_analysis, ensure_ascii=False, indent=2)}

请生成Related Work部分的LaTeX内容。
"""

        return llm.complete(system_prompt, user_prompt, timeout=180.0)

    def _generate_methodology(self, llm: LLMClient, innovation: dict) -> str:
        """生成方法论部分"""
        system_prompt = """你是一位学术论文写作专家。
请生成Methodology部分，详细描述提出的方法。

要求：
1. 清晰描述方法的整体框架
2. 详细说明关键技术细节
3. 使用算法伪代码（algorithm环境）
4. 引用相关图表（\\ref{fig:xxx}）
5. 数学公式使用equation环境
6. 直接输出LaTeX格式内容
"""

        user_prompt = f"""
创新方法：
{json.dumps(innovation, ensure_ascii=False, indent=2)}

请生成Methodology部分的LaTeX内容，包括方法描述和算法伪代码。
"""

        return llm.complete(system_prompt, user_prompt, timeout=180.0)

    def _generate_experiments(self, llm: LLMClient, experiments: dict, ablation: dict) -> str:
        """生成实验部分"""
        system_prompt = """你是一位学术论文写作专家。
请生成Experiments部分，包括实验设置、结果和分析。

要求：
1. 描述实验设置（数据集、基线、评估指标、实现细节）
2. 展示主要实验结果（使用table环境）
3. 进行消融实验分析
4. 讨论结果的意义
5. 引用图表（\\ref{tab:xxx}, \\ref{fig:xxx}）
6. 直接输出LaTeX格式内容
"""

        user_prompt = f"""
实验结果：
{json.dumps(experiments, ensure_ascii=False, indent=2)}

消融实验：
{json.dumps(ablation, ensure_ascii=False, indent=2)}

请生成Experiments部分的LaTeX内容，包括实验设置、结果表格和分析。
"""

        return llm.complete(system_prompt, user_prompt, timeout=180.0)

    def _generate_conclusion(self, llm: LLMClient, innovation: dict, experiments: dict) -> str:
        """生成结论部分"""
        system_prompt = """你是一位学术论文写作专家。
请生成Conclusion部分，总结工作并展望未来。

要求：
1. 总结主要贡献
2. 强调实验结果
3. 讨论局限性
4. 提出未来工作方向
5. 简洁有力
6. 直接输出LaTeX格式内容
"""

        user_prompt = f"""
创新点：
{json.dumps(innovation, ensure_ascii=False, indent=2)}

实验结果：
{json.dumps(experiments, ensure_ascii=False, indent=2)}

请生成Conclusion部分的LaTeX内容。
"""

        return llm.complete(system_prompt, user_prompt, timeout=120.0)

    def _assemble_latex(self, abstract_intro: str, related_work: str,
                       methodology: str, experiments: str, conclusion: str,
                       context: AgentContext) -> str:
        """组装完整的LaTeX文档"""

        # 获取项目名称
        project_name = context.project_name or "Research Paper"

        # LaTeX文档头部
        header = r"""\documentclass[conference]{IEEEtran}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{algorithm}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{hyperref}

\begin{document}

\title{""" + project_name + r"""}

\author{
\IEEEauthorblockN{Author Name}
\IEEEauthorblockA{\textit{Department} \\
\textit{University}\\
City, Country \\
email@example.com}
}

\maketitle

"""

        # 组装各部分
        body = f"""
\\begin{{abstract}}
{abstract_intro}
\\end{{abstract}}

\\section{{Introduction}}
{abstract_intro}

\\section{{Related Work}}
{related_work}

\\section{{Methodology}}
{methodology}

\\section{{Experiments}}
{experiments}

\\section{{Conclusion}}
{conclusion}

\\section*{{Acknowledgment}}
This work was supported by [Funding Information].

\\begin{{thebibliography}}{{00}}
\\bibitem{{ref1}} Author, A., ``Title,'' Journal, vol. X, no. Y, pp. Z, Year.
\\end{{thebibliography}}

\\end{{document}}
"""

        return header + body

    def _create_package(self, context: AgentContext, latex_path: Path) -> Path:
        """创建包含LaTeX文件和所有图片的压缩包"""
        zip_path = context.run_dir / "paper_package.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加LaTeX文件
            zipf.write(latex_path, "paper.tex")

            # 添加所有图表
            diagrams_dir = context.run_dir / "diagrams"
            if diagrams_dir.exists():
                for img_file in diagrams_dir.glob("*"):
                    if img_file.is_file():
                        zipf.write(img_file, f"figures/{img_file.name}")

            # 添加README
            readme_content = """# LaTeX Paper Package

## Contents
- paper.tex: Main LaTeX source file
- figures/: All figures and diagrams

## Compilation
1. Upload all files to Overleaf
2. Or compile locally:
   ```
   pdflatex paper.tex
   bibtex paper
   pdflatex paper.tex
   pdflatex paper.tex
   ```

## Notes
- Replace author information in paper.tex
- Add proper citations in the bibliography section
- Adjust figure references as needed
"""
            zipf.writestr("README.md", readme_content)

        return zip_path
