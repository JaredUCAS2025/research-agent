from __future__ import annotations

from pathlib import Path
import ast

from ..base import BaseSkill, SkillResult
from ..context import AgentContext
from ..llm import LLMClient
from ..registry import SkillMeta

REPO_INGESTOR_META = SkillMeta(
    name="repo_ingestor",
    description="扫描本地仓库目录，生成仓库画像",
    inputs_required=["repo_path"],
    outputs_produced=["repo_profile"],
    artifacts=["repo_profile.json"],
    modes=["repo"],
)

AST_ANALYZER_META = SkillMeta(
    name="ast_analyzer",
    description="解析 Python 文件 AST，输出函数、类、导入摘要",
    inputs_required=["repo_profile"],
    outputs_produced=["ast_analysis"],
    artifacts=["ast_analysis.json"],
    modes=["repo"],
)

ENV_RESOLVER_META = SkillMeta(
    name="env_resolver",
    description="读取依赖文件并给出环境建议",
    inputs_required=["repo_profile"],
    outputs_produced=["env_resolution"],
    artifacts=["env_resolution.json"],
    modes=["repo"],
)


class RepoIngestorSkill(BaseSkill):
    name = "repo_ingestor"
    description = "Inspect a local repository tree and capture key project files."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        repo_path_raw = str(context.notes.get("repo_path", "")).strip()
        if not repo_path_raw:
            raise ValueError("notes.repo_path is required")

        repo_path = Path(repo_path_raw)
        if not repo_path.exists() or not repo_path.is_dir():
            raise ValueError(f"repo_path does not exist: {repo_path}")

        important_files: list[str] = []
        for pattern in ["*.py", "requirements.txt", "pyproject.toml", "environment.yml", "setup.py", "README*"]:
            important_files.extend(str(path.relative_to(repo_path)) for path in repo_path.rglob(pattern))

        important_files = sorted(dict.fromkeys(important_files))[:200]
        context.repo_profile = {
            "repo_path": str(repo_path),
            "important_files": important_files,
            "python_file_count": len([p for p in important_files if p.endswith('.py')]),
        }
        context.save_json("repo_profile.json", context.repo_profile)
        return SkillResult(self.name, "Repository profile generated.")


class ASTAnalyzerSkill(BaseSkill):
    name = "ast_analyzer"
    description = "Analyze Python files and build a lightweight AST summary."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        repo_path_raw = str(context.repo_profile.get("repo_path") or context.notes.get("repo_path", "")).strip()
        if not repo_path_raw:
            raise ValueError("repo_path is required before AST analysis")

        repo_path = Path(repo_path_raw)
        summary: dict[str, dict[str, list[str]]] = {}
        for py_file in repo_path.rglob("*.py"):
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except Exception:
                continue

            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            imports: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

            summary[str(py_file.relative_to(repo_path))] = {
                "functions": functions[:40],
                "classes": classes[:20],
                "imports": imports[:40],
            }

        context.ast_analysis = {
            "repo_path": str(repo_path),
            "files": summary,
        }
        context.save_json("ast_analysis.json", context.ast_analysis)
        return SkillResult(self.name, "AST analysis generated.")


class EnvResolverSkill(BaseSkill):
    name = "env_resolver"
    description = "Summarize environment and dependency requirements for a repository."

    def run(self, context: AgentContext, llm: LLMClient) -> SkillResult:
        repo_path_raw = str(context.repo_profile.get("repo_path") or context.notes.get("repo_path", "")).strip()
        if not repo_path_raw:
            raise ValueError("repo_path is required before env resolution")

        repo_path = Path(repo_path_raw)
        files_to_check = ["requirements.txt", "pyproject.toml", "environment.yml", "setup.py"]
        contents: dict[str, str] = {}
        for name in files_to_check:
            file_path = repo_path / name
            if file_path.exists():
                contents[name] = file_path.read_text(encoding="utf-8", errors="ignore")[:12000]

        context.env_resolution = {
            "repo_path": str(repo_path),
            "files": contents,
            "recommendation": "优先创建隔离环境，并根据 requirements / pyproject / environment.yml 选择 pip 或 conda。",
        }
        context.save_json("env_resolution.json", context.env_resolution)
        return SkillResult(self.name, "Environment resolution summary generated.")
