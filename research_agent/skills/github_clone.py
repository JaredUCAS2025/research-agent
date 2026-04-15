"""
GitHub Clone Skill - 克隆 GitHub 仓库到本地
"""
import json
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta


class GitHubCloneSkill(BaseSkill):
    """克隆 GitHub 仓库到本地"""

    def execute(self, context: AgentContext) -> SkillResult:
        """
        克隆指定的 GitHub 仓库

        Args:
            context: 需要包含 github_clone_url 或 github_repo_name
        """
        clone_url = context.get("github_clone_url")
        repo_name = context.get("github_repo_name")

        if not clone_url and not repo_name:
            return SkillResult(
                success=False,
                message="Missing github_clone_url or github_repo_name in context",
                artifacts={}
            )

        # 如果只有 repo_name，从 github_repositories 中查找
        if not clone_url and repo_name:
            repos = context.get("github_repositories", [])
            for repo in repos:
                if repo["full_name"] == repo_name or repo["name"] == repo_name:
                    clone_url = repo["clone_url"]
                    break

            if not clone_url:
                return SkillResult(
                    success=False,
                    message=f"Repository {repo_name} not found in search results",
                    artifacts={}
                )

        # 确定克隆目标目录
        clone_base_dir = context.run_dir / "cloned_repos"
        clone_base_dir.mkdir(exist_ok=True)

        # 从 URL 提取仓库名
        repo_folder_name = clone_url.rstrip("/").split("/")[-1].replace(".git", "")
        clone_path = clone_base_dir / repo_folder_name

        # 如果已存在，先删除或跳过
        if clone_path.exists():
            import shutil
            shutil.rmtree(clone_path)

        try:
            # 执行 git clone
            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(clone_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                return SkillResult(
                    success=False,
                    message=f"Git clone failed: {result.stderr}",
                    artifacts={}
                )

            # 分析仓库基本信息
            repo_info = self._analyze_repo_structure(clone_path)

            # 保存仓库信息
            info_path = context.run_dir / f"{repo_folder_name}_info.json"
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(repo_info, f, indent=2, ensure_ascii=False)

            # 更新 context
            context.set("cloned_repo_path", str(clone_path))
            context.set("cloned_repo_info", repo_info)

            return SkillResult(
                success=True,
                message=f"Successfully cloned repository to {clone_path}",
                artifacts={
                    "clone_path": str(clone_path),
                    "repo_info": repo_info,
                    "repo_info_json": str(info_path)
                }
            )

        except subprocess.TimeoutExpired:
            return SkillResult(
                success=False,
                message="Git clone timeout (exceeded 5 minutes)",
                artifacts={}
            )
        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Clone failed: {str(e)}",
                artifacts={}
            )

    def _analyze_repo_structure(self, repo_path: Path) -> Dict[str, Any]:
        """分析仓库基本结构"""
        info = {
            "path": str(repo_path),
            "name": repo_path.name,
            "files": [],
            "directories": [],
            "has_readme": False,
            "has_requirements": False,
            "has_setup_py": False,
            "has_dockerfile": False,
            "programming_languages": set(),
            "total_files": 0,
            "total_size_mb": 0
        }

        # 遍历仓库文件
        try:
            total_size = 0
            for item in repo_path.rglob("*"):
                # 跳过 .git 目录
                if ".git" in item.parts:
                    continue

                if item.is_file():
                    info["total_files"] += 1
                    total_size += item.stat().st_size

                    # 记录根目录的重要文件
                    if item.parent == repo_path:
                        info["files"].append(item.name)

                        # 检查特殊文件
                        lower_name = item.name.lower()
                        if lower_name in ["readme.md", "readme.txt", "readme"]:
                            info["has_readme"] = True
                        elif lower_name == "requirements.txt":
                            info["has_requirements"] = True
                        elif lower_name == "setup.py":
                            info["has_setup_py"] = True
                        elif lower_name == "dockerfile":
                            info["has_dockerfile"] = True

                    # 识别编程语言
                    suffix = item.suffix.lower()
                    lang_map = {
                        ".py": "Python",
                        ".js": "JavaScript",
                        ".ts": "TypeScript",
                        ".java": "Java",
                        ".cpp": "C++",
                        ".c": "C",
                        ".go": "Go",
                        ".rs": "Rust",
                        ".rb": "Ruby",
                        ".php": "PHP"
                    }
                    if suffix in lang_map:
                        info["programming_languages"].add(lang_map[suffix])

                elif item.is_dir() and item.parent == repo_path:
                    info["directories"].append(item.name)

            info["total_size_mb"] = round(total_size / (1024 * 1024), 2)
            info["programming_languages"] = list(info["programming_languages"])

        except Exception as e:
            info["error"] = str(e)

        return info


# 注册技能
SKILL_META = SkillMeta(
    name="github_clone",
    description="Clone a GitHub repository to local directory",
    skill_class=GitHubCloneSkill,
    required_context=["github_clone_url or github_repo_name"],
    optional_context=["github_repositories"],
    outputs=["cloned_repo_path", "cloned_repo_info", "repo_info_json"]
)
