# Research Agent 使用示例

本文档展示如何使用 Research Agent 的各种功能。

## 快速开始

### 1. 基础配置

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加你的 API 密钥
```

### 2. 运行完整研究流程

```python
from research_agent.agent import ResearchAgent

# 创建 agent
agent = ResearchAgent()

# 运行完整研究流程
result = agent.run_workflow(
    "research_full",
    query="transformer attention mechanism optimization"
)

print(f"研究完成！结果保存在: {result.artifacts['run_dir']}")
```

## 使用单个技能

### 搜索 GitHub 仓库

```python
from research_agent.agent import ResearchAgent

agent = ResearchAgent()

# 搜索相关代码
result = agent.run_skill(
    "github_search",
    query="transformer pytorch",
    language="Python",
    sort="stars",
    max_results=10
)

# 查看结果
repos = result.artifacts["github_repos"]
for repo in repos:
    print(f"{repo['name']}: {repo['stars']} stars")
```

### 分析论文并提出创新点

```python
from research_agent.agent import ResearchAgent

agent = ResearchAgent()

# 1. 搜索论文
agent.run_skill("paper_search", query="attention mechanism")

# 2. 阅读论文
agent.run_skill("paper_reader")

# 3. 分析研究空白
agent.run_skill("gap_analyzer")

# 4. 提出创新点
result = agent.run_skill("innovation_proposer")

# 查看创新提案
proposals = result.artifacts["innovation_proposals"]["proposals"]
for i, proposal in enumerate(proposals, 1):
    print(f"\n创新点 {i}: {proposal['title']}")
    print(f"核心思想: {proposal['core_idea']}")
    print(f"优先级: {proposal['priority']}")
```

### 设计和运行实验

```python
from research_agent.agent import ResearchAgent

agent = ResearchAgent()

# 假设已经有了创新点
# agent.context.set("innovation_proposals", {...})

# 1. 设计实验
agent.run_skill("experiment_designer")

# 2. 配置环境（如果有克隆的仓库）
agent.run_skill("environment_setup")

# 3. 运行实验
result = agent.run_skill("experiment_runner")

# 查看结果
exp_results = result.artifacts["experiment_results"]
print(f"完成 {exp_results['total_experiments']} 个实验")
print(f"成功: {exp_results['successful']}, 失败: {exp_results['failed']}")
```

### 消融实验分析

```python
from research_agent.agent import ResearchAgent

agent = ResearchAgent()

# 假设已经运行了实验
# agent.context.set("experiment_results", {...})

# 分析消融实验
result = agent.run_skill("ablation_study")

# 查看组件重要性排名
analysis = result.artifacts["ablation_analysis"]
for item in analysis["ranking"]:
    print(f"{item['rank']}. {item['component']}: {item['impact']:.4f}")
```

### 生成完整报告

```python
from research_agent.agent import ResearchAgent

agent = ResearchAgent()

# 假设已经完成了所有分析和实验
# 生成综合报告
result = agent.run_skill("comprehensive_report")

print(f"报告已生成:")
print(f"- Markdown: {result.artifacts['report_markdown']}")
print(f"- LaTeX: {result.artifacts['report_latex']}")
print(f"- 演示文稿: {result.artifacts['presentation']}")
```

## 自定义工作流

你可以创建自定义工作流来组合不同的技能：

```python
from research_agent.agent import ResearchAgent

agent = ResearchAgent()

# 自定义流程：只做文献调研和创新提出
agent.run_skill("paper_search", query="your topic")
agent.run_skill("paper_reader")
agent.run_skill("survey_writer")
agent.run_skill("gap_analyzer")
agent.run_skill("innovation_proposer")

print("文献调研和创新分析完成！")
```

## 高级用法

### 使用 GitHub Token

在 `.env` 文件中添加：

```bash
GITHUB_TOKEN=your_github_token_here
```

这将提高 GitHub API 的速率限制。

### 配置实验参数

在 `.env` 文件中配置：

```bash
# 实验超时时间（秒）
EXPERIMENT_TIMEOUT=3600

# 最大并行实验数
MAX_PARALLEL_EXPERIMENTS=2

# 是否使用 Docker
USE_DOCKER=false

# 资源限制
MAX_MEMORY_GB=8
MAX_DISK_GB=50
```

### 查看运行日志

所有运行结果都保存在 `workspace/runs/` 目录下：

```bash
workspace/runs/
├── run_20240115_143022/
│   ├── papers/              # 下载的论文
│   ├── survey.md            # 生成的综述
│   ├── gap_analysis.json    # 空白分析
│   ├── innovations.json     # 创新提案
│   ├── experiment_design.md # 实验设计
│   ├── experiments/         # 实验结果
│   ├── ablation_study.md    # 消融实验报告
│   └── comprehensive_report.md  # 完整报告
```

## 常见问题

### Q: 如何只运行部分流程？

A: 使用单个技能而不是完整工作流：

```python
# 只做文献调研
agent.run_skill("paper_search", query="your topic")
agent.run_skill("paper_reader")
agent.run_skill("survey_writer")
```

### Q: 实验执行失败怎么办？

A: 检查以下几点：
1. 确保克隆的代码仓库有可执行的脚本
2. 检查依赖是否正确安装
3. 查看 `experiment_run.log` 了解详细错误信息
4. 如果没有真实代码，系统会运行模拟实验

### Q: 如何自定义 LLM 模型？

A: 在 `.env` 文件中配置：

```bash
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4  # 或其他模型
```

### Q: 生成的报告在哪里？

A: 所有报告都在 `workspace/runs/<run_id>/` 目录下，包括：
- `survey.md`: 文献综述
- `experiment_design.md`: 实验设计
- `ablation_study.md`: 消融实验报告
- `comprehensive_report.md`: 完整研究报告
- `presentation.md`: 演示文稿

## 更多示例

查看 `examples/` 目录获取更多使用示例：

- `example_basic.py`: 基础使用
- `example_full_workflow.py`: 完整工作流
- `example_custom.py`: 自定义流程
- `example_github_only.py`: 只使用 GitHub 功能

## 技术支持

- GitHub Issues: https://github.com/JaredUCAS2025/research-agent/issues
- 文档: 查看 `ENHANCEMENT_DESIGN.md` 和 `ENHANCEMENT_PROGRESS.md`
