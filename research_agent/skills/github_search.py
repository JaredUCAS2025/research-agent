"""
GitHub Search Skill - 搜索 GitHub 仓库
"""
import json
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta


class GitHubSearchSkill(BaseSkill):
    """搜索 GitHub 仓库"""

    def __init__(self):
        super().__init__()
        self.github_token = self._get_github_token()
        self.headers = {}
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"

    def _get_github_token(self) -> Optional[str]:
        """从环境变量获取 GitHub token"""
        import os
        return os.getenv("GITHUB_TOKEN")

    def execute(self, context: AgentContext) -> SkillResult:
        """
        执行 GitHub 搜索

        Args:
            context: 需要包含 github_query, language (可选), min_stars (可选)
        """
        query = context.get("github_query")
        if not query:
            return SkillResult(
                success=False,
                message="Missing github_query in context",
                artifacts={}
            )

        language = context.get("github_language", "")
        min_stars = context.get("github_min_stars", 10)
        max_results = context.get("github_max_results", 10)

        # 构建搜索查询
        search_query = query
        if language:
            search_query += f" language:{language}"
        if min_stars:
            search_query += f" stars:>={min_stars}"

        # 调用 GitHub API
        try:
            repos = self._search_repositories(search_query, max_results)

            if not repos:
                return SkillResult(
                    success=True,
                    message=f"No repositories found for query: {query}",
                    artifacts={"repositories": []}
                )

            # 保存结果
            output_path = context.run_dir / "github_search_results.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(repos, f, indent=2, ensure_ascii=False)

            # 生成可读报告
            report = self._generate_report(repos, query)
            report_path = context.run_dir / "github_search_report.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            # 更新 context
            context.set("github_repositories", repos)

            return SkillResult(
                success=True,
                message=f"Found {len(repos)} repositories for query: {query}",
                artifacts={
                    "repositories": repos,
                    "search_results_json": str(output_path),
                    "search_report_md": str(report_path)
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                message=f"GitHub search failed: {str(e)}",
                artifacts={}
            )

    def _search_repositories(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        调用 GitHub API 搜索仓库
        """
        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(max_results, 100)
        }

        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        # 提取关键信息
        repos = []
        for item in items[:max_results]:
            repo = {
                "name": item["name"],
                "full_name": item["full_name"],
                "description": item.get("description", ""),
                "url": item["html_url"],
                "clone_url": item["clone_url"],
                "stars": item["stargazers_count"],
                "forks": item["forks_count"],
                "language": item.get("language", ""),
                "updated_at": item["updated_at"],
                "topics": item.get("topics", []),
                "license": item.get("license", {}).get("name", "N/A") if item.get("license") else "N/A"
            }
            repos.append(repo)

        return repos

    def _generate_report(self, repos: List[Dict[str, Any]], query: str) -> str:
        """生成搜索结果报告"""
        report = f"# GitHub Search Results\n\n"
        report += f"**Query**: {query}\n\n"
        report += f"**Total Results**: {len(repos)}\n\n"
        report += "---\n\n"

        for i, repo in enumerate(repos, 1):
            report += f"## {i}. [{repo['full_name']}]({repo['url']})\n\n"
            report += f"**Description**: {repo['description']}\n\n"
            report += f"- **Stars**: ⭐ {repo['stars']}\n"
            report += f"- **Forks**: 🍴 {repo['forks']}\n"
            report += f"- **Language**: {repo['language']}\n"
            report += f"- **License**: {repo['license']}\n"
            report += f"- **Last Updated**: {repo['updated_at']}\n"

            if repo['topics']:
                report += f"- **Topics**: {', '.join(repo['topics'])}\n"

            report += f"- **Clone URL**: `{repo['clone_url']}`\n\n"
            report += "---\n\n"

        return report


# 注册技能
SKILL_META = SkillMeta(
    name="github_search",
    description="Search GitHub repositories by keywords, language, and stars",
    skill_class=GitHubSearchSkill,
    required_context=["github_query"],
    optional_context=["github_language", "github_min_stars", "github_max_results"],
    outputs=["github_repositories", "search_results_json", "search_report_md"]
)
