"""
Test script for new enhanced skills
"""
from pathlib import Path
from research_agent.context import AgentContext
from research_agent.skills.github_search import GitHubSearchSkill
from research_agent.skills.github_clone import GitHubCloneSkill
from research_agent.skills.enhanced_code_analyzer import EnhancedCodeAnalyzerSkill
from research_agent.skills.gap_analyzer import GapAnalyzerSkill
from research_agent.skills.innovation_proposer import InnovationProposerSkill


def test_github_search():
    """测试 GitHub 搜索功能"""
    print("\n=== Testing GitHub Search ===")

    context = AgentContext(
        project_name="test-github-search",
        run_id="test-001"
    )
    context.set("github_query", "transformer optimization")
    context.set("github_language", "Python")
    context.set("github_min_stars", 100)
    context.set("github_max_results", 5)

    skill = GitHubSearchSkill()
    result = skill.execute(context)

    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.success:
        repos = result.artifacts.get("repositories", [])
        print(f"Found {len(repos)} repositories")
        for repo in repos[:3]:
            print(f"  - {repo['full_name']} (⭐ {repo['stars']})")

    return context


def test_github_clone(context):
    """测试 GitHub 克隆功能"""
    print("\n=== Testing GitHub Clone ===")

    repos = context.get("github_repositories", [])
    if not repos:
        print("No repositories to clone")
        return context

    # 克隆第一个仓库
    context.set("github_repo_name", repos[0]["full_name"])

    skill = GitHubCloneSkill()
    result = skill.execute(context)

    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.success:
        print(f"Clone path: {result.artifacts.get('clone_path')}")

    return context


def test_code_analyzer(context):
    """测试代码分析功能"""
    print("\n=== Testing Code Analyzer ===")

    clone_path = context.get("cloned_repo_path")
    if not clone_path:
        print("No cloned repository to analyze")
        return context

    skill = EnhancedCodeAnalyzerSkill()
    result = skill.execute(context)

    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.success:
        analysis = result.artifacts.get("analysis", {})
        code_structure = analysis.get("code_structure", {})
        print(f"Total files: {code_structure.get('total_files')}")
        print(f"Total lines: {code_structure.get('total_lines')}")
        print(f"Classes: {len(code_structure.get('classes', []))}")

    return context


def test_gap_analyzer(context):
    """测试 gap 分析功能"""
    print("\n=== Testing Gap Analyzer ===")

    # 创建一些模拟的论文摘要
    mock_paper_digests = [
        {
            "metadata": {"title": "Attention Is All You Need"},
            "summary": "Introduces the Transformer architecture based on self-attention mechanisms.",
            "claims": "Transformers achieve state-of-the-art results on machine translation tasks."
        },
        {
            "metadata": {"title": "BERT: Pre-training of Deep Bidirectional Transformers"},
            "summary": "Pre-training bidirectional transformers for language understanding.",
            "claims": "BERT achieves new state-of-the-art on 11 NLP tasks."
        }
    ]

    context.set("paper_digests", mock_paper_digests)

    skill = GapAnalyzerSkill()
    result = skill.execute(context)

    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.success:
        gap_analysis = result.artifacts.get("gap_analysis", {})
        print(f"Limitations found: {len(gap_analysis.get('limitations', []))}")
        print(f"Unsolved problems: {len(gap_analysis.get('unsolved_problems', []))}")
        print(f"Improvement directions: {len(gap_analysis.get('improvement_directions', []))}")

    return context


def test_innovation_proposer(context):
    """测试创新点提出功能"""
    print("\n=== Testing Innovation Proposer ===")

    gap_analysis = context.get("gap_analysis")
    if not gap_analysis:
        print("No gap analysis available")
        return context

    skill = InnovationProposerSkill()
    result = skill.execute(context)

    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.success:
        innovations = result.artifacts.get("innovations", {})
        proposals = innovations.get("proposals", [])
        print(f"Proposed {len(proposals)} innovations:")
        for proposal in proposals:
            print(f"  - {proposal['title']} (Priority: {proposal.get('priority', 'N/A')})")

    return context


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Testing Enhanced Research Agent Skills")
    print("=" * 60)

    try:
        # 测试 GitHub 搜索
        context = test_github_search()

        # 测试 GitHub 克隆（可选，需要网络）
        # context = test_github_clone(context)

        # 测试代码分析（需要先克隆）
        # context = test_code_analyzer(context)

        # 测试 gap 分析
        context = test_gap_analyzer(context)

        # 测试创新点提出
        context = test_innovation_proposer(context)

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
