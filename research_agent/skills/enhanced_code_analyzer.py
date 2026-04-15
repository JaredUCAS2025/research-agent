"""
Enhanced Code Analyzer Skill - 深度分析代码仓库
"""
import json
import ast
from typing import Dict, Any, List
from pathlib import Path
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta
from research_agent.llm import LLMClient


class EnhancedCodeAnalyzerSkill(BaseSkill):
    """深度分析代码仓库结构和实现"""

    def __init__(self):
        super().__init__()
        self.llm = LLMClient()

    def execute(self, context: AgentContext) -> SkillResult:
        """
        深度分析代码仓库

        Args:
            context: 需要包含 cloned_repo_path
        """
        repo_path = context.get("cloned_repo_path")
        if not repo_path:
            return SkillResult(
                success=False,
                message="Missing cloned_repo_path in context",
                artifacts={}
            )

        repo_path = Path(repo_path)
        if not repo_path.exists():
            return SkillResult(
                success=False,
                message=f"Repository path does not exist: {repo_path}",
                artifacts={}
            )

        try:
            # 1. 读取 README
            readme_content = self._read_readme(repo_path)

            # 2. 分析 Python 代码结构
            code_structure = self._analyze_python_code(repo_path)

            # 3. 分析依赖
            dependencies = self._analyze_dependencies(repo_path)

            # 4. 使用 LLM 生成深度分析
            analysis = self._generate_llm_analysis(
                readme_content,
                code_structure,
                dependencies,
                repo_path.name
            )

            # 保存分析结果
            output = {
                "repo_name": repo_path.name,
                "repo_path": str(repo_path),
                "readme_summary": readme_content[:1000] if readme_content else "No README found",
                "code_structure": code_structure,
                "dependencies": dependencies,
                "llm_analysis": analysis
            }

            output_path = context.run_dir / f"{repo_path.name}_analysis.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            # 生成可读报告
            report = self._generate_report(output)
            report_path = context.run_dir / f"{repo_path.name}_analysis.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # 更新 context
            context.set("code_analysis", output)

            return SkillResult(
                success=True,
                message=f"Successfully analyzed repository: {repo_path.name}",
                artifacts={
                    "analysis": output,
                    "analysis_json": str(output_path),
                    "analysis_report": str(report_path)
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Code analysis failed: {str(e)}",
                artifacts={}
            )

    def _read_readme(self, repo_path: Path) -> str:
        """读取 README 文件"""
        readme_files = ["README.md", "README.txt", "README", "readme.md"]
        for filename in readme_files:
            readme_path = repo_path / filename
            if readme_path.exists():
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        return f.read()
                except:
                    pass
        return ""

    def _analyze_python_code(self, repo_path: Path) -> Dict[str, Any]:
        """分析 Python 代码结构"""
        structure = {
            "modules": [],
            "classes": [],
            "functions": [],
            "total_lines": 0,
            "total_files": 0
        }

        for py_file in repo_path.rglob("*.py"):
            if ".git" in py_file.parts or "__pycache__" in py_file.parts:
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    structure["total_lines"] += lines
                    structure["total_files"] += 1

                    # 解析 AST
                    try:
                        tree = ast.parse(content)

                        # 提取类和函数
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                structure["classes"].append({
                                    "name": node.name,
                                    "file": str(py_file.relative_to(repo_path)),
                                    "line": node.lineno
                                })
                            elif isinstance(node, ast.FunctionDef):
                                # 只记录顶层函数
                                if node.col_offset == 0:
                                    structure["functions"].append({
                                        "name": node.name,
                                        "file": str(py_file.relative_to(repo_path)),
                                        "line": node.lineno
                                    })
                    except:
                        pass

            except:
                pass

        return structure

    def _analyze_dependencies(self, repo_path: Path) -> Dict[str, Any]:
        """分析项目依赖"""
        dependencies = {
            "requirements": [],
            "setup_py": [],
            "conda_env": []
        }

        # 读取 requirements.txt
        req_file = repo_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, "r", encoding="utf-8") as f:
                    dependencies["requirements"] = [
                        line.strip() for line in f
                        if line.strip() and not line.startswith("#")
                    ]
            except:
                pass

        # 读取 setup.py
        setup_file = repo_path / "setup.py"
        if setup_file.exists():
            try:
                with open(setup_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 简单提取（不执行代码）
                    if "install_requires" in content:
                        dependencies["setup_py"] = ["Found install_requires in setup.py"]
            except:
                pass

        # 读取 environment.yml
        env_file = repo_path / "environment.yml"
        if env_file.exists():
            dependencies["conda_env"] = ["Found conda environment.yml"]

        return dependencies

    def _generate_llm_analysis(
        self,
        readme: str,
        code_structure: Dict,
        dependencies: Dict,
        repo_name: str
    ) -> str:
        """使用 LLM 生成深度分析"""

        prompt = f"""Analyze this code repository and provide insights:

Repository: {repo_name}

README (first 1000 chars):
{readme[:1000]}

Code Structure:
- Total Python files: {code_structure['total_files']}
- Total lines of code: {code_structure['total_lines']}
- Classes: {len(code_structure['classes'])}
- Functions: {len(code_structure['functions'])}

Dependencies:
- Requirements: {len(dependencies['requirements'])} packages
- Has setup.py: {bool(dependencies['setup_py'])}
- Has conda env: {bool(dependencies['conda_env'])}

Please provide:
1. **Purpose**: What does this repository do?
2. **Key Components**: What are the main modules/classes?
3. **Implementation Approach**: What techniques/algorithms are used?
4. **Dependencies**: What are the key dependencies?
5. **Usage**: How is this typically used?

Keep the analysis concise and focused on technical details.
"""

        try:
            response = self.llm.generate(prompt, max_tokens=1000)
            return response
        except Exception as e:
            return f"LLM analysis failed: {str(e)}"

    def _generate_report(self, analysis: Dict[str, Any]) -> str:
        """生成分析报告"""
        report = f"# Code Analysis Report: {analysis['repo_name']}\n\n"

        report += "## Repository Overview\n\n"
        report += f"**Path**: `{analysis['repo_path']}`\n\n"

        report += "## Code Structure\n\n"
        cs = analysis['code_structure']
        report += f"- **Total Python Files**: {cs['total_files']}\n"
        report += f"- **Total Lines of Code**: {cs['total_lines']}\n"
        report += f"- **Classes**: {len(cs['classes'])}\n"
        report += f"- **Functions**: {len(cs['functions'])}\n\n"

        if cs['classes']:
            report += "### Key Classes\n\n"
            for cls in cs['classes'][:10]:  # 只显示前10个
                report += f"- `{cls['name']}` in `{cls['file']}:{cls['line']}`\n"
            report += "\n"

        report += "## Dependencies\n\n"
        deps = analysis['dependencies']
        if deps['requirements']:
            report += "### Requirements.txt\n\n"
            for req in deps['requirements'][:20]:  # 只显示前20个
                report += f"- {req}\n"
            report += "\n"

        report += "## LLM Analysis\n\n"
        report += analysis['llm_analysis']
        report += "\n"

        return report


# 注册技能
SKILL_META = SkillMeta(
    name="enhanced_code_analyzer",
    description="Deep analysis of code repository structure and implementation",
    skill_class=EnhancedCodeAnalyzerSkill,
    required_context=["cloned_repo_path"],
    optional_context=[],
    outputs=["code_analysis", "analysis_json", "analysis_report"]
)
