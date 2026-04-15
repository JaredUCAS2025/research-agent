# Research Agent

[中文](#中文文档) | [English](#english-documentation)

---

## English Documentation

### Overview

A **Skill-based LLM Agent System** designed for academic research workflows, including paper reading, multi-paper comparison, conversational follow-ups, and lightweight code repository analysis.

This is not just a “paper summarization script” — it's an intelligent workbench built around real research workflows:

- Fast structured reading of single papers
- Multi-paper comparison, conflict detection, and survey generation
- Artifact persistence with scoped chat support
- Local code repository profiling, AST analysis, and environment recommendations
- Dual entry points (CLI & Web) for experimentation and demonstration
- LLM-driven state graph orchestration (Harness mode) with user confirmation at key checkpoints

### Why This Project Matters

Most LLM applications in research stop at “copy paper content to model, get a summary.” This approach has problems:

- Results are not reusable
- Follow-up questions lack contextual anchors
- Multi-paper systematic comparison is difficult
- Same paper gets processed repeatedly (slow & expensive)
- Disconnected from real research workflows (code repos, reproduction environments)

**Research Agent** solves a more realistic problem:

> How to organize paper reading, structured understanding, comparative analysis, artifact persistence, and follow-up interactions into a scalable agent workflow.

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/JaredUCAS2025/research-agent.git
cd research-agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API key
```

4. **Run Web UI**
```bash
python run_web.py
# Open http://127.0.0.1:5000 in your browser
```

### Configuration

Edit `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: custom endpoint
OPENAI_MODEL=gpt-4  # Main model for heavy tasks
OPENAI_FAST_MODEL=gpt-3.5-turbo  # Optional: faster model for chat/planning
```

- `OPENAI_API_KEY`: Your API key
- `OPENAI_BASE_URL`: Custom OpenAI-compatible endpoint (optional)
- `OPENAI_MODEL`: Main model for paper analysis and survey generation
- `OPENAI_FAST_MODEL`: Optional fast model for chat and lightweight tasks

### Usage Examples

**Single Paper Analysis (CLI)**
```bash
python main.py single --project “my-paper” --paper “workspace/inputs/sample_paper.md”
```

**Multi-Paper Survey (CLI)**
```bash
python main.py survey --project “my-survey” --papers “paper1.md” “paper2.md”
```

**Python API**
```python
from pathlib import Path
from research_agent.agent import ResearchAgent
from research_agent.context import AgentContext

context = AgentContext(
    project_name=”demo-paper”,
    paper_path=Path(“workspace/inputs/sample_paper.md”)
)
agent = ResearchAgent()
result = agent.run_single(context)
print(result.run_id)
```

### Core Features

- **Single Paper Reading**: Fast structured extraction (metadata, claims, methods)
- **Multi-Paper Survey**: Comparison matrix, conflict detection, survey generation
- **Scoped Chat**: Conversational follow-ups based on generated artifacts
- **Repository Analysis**: Code profiling, AST analysis, dependency resolution
- **Harness Orchestration**: LLM-driven workflow with dynamic routing
- **Dual Interface**: CLI and Web UI

### Architecture

Built on **Skill-based Agent Architecture** with:
- Modular skills with metadata (`SkillMeta`)
- Context-driven state sharing (`AgentContext`)
- Artifact persistence (structured JSON/Markdown outputs)
- Prompt stack (soul + skills + memory + task)
- Harness orchestrator (state graph + LLM decision nodes)

---

## 中文文档

### 概述

一个面向**科研阅读、多论文对比、会话式追问与轻量代码仓库理解**的 Skill-based LLM Agent 系统。

它不是一个简单的”论文摘要脚本”，而是一个围绕科研工作流设计的智能体工作台：

- 对单篇论文做快速结构化阅读
- 对多篇论文做对比、冲突识别与综述生成
- 对运行结果进行 artifact 落盘，支持后续 scoped chat
- 对本地代码仓库生成画像、AST 摘要和环境建议
- 提供 CLI 与 Web 双入口，便于实验和展示
- 支持 LLM 驱动的状态图编排（Harness 模式），在关键节点暂停等待用户确认

### 快速开始

1. **克隆仓库**
```bash
git clone https://github.com/JaredUCAS2025/research-agent.git
cd research-agent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，添加你的 API 密钥
```

4. **启动 Web 界面**
```bash
python run_web.py
# 在浏览器中打开 http://127.0.0.1:5000
```

### 配置说明

编辑 `.env` 文件：

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选：自定义接口地址
OPENAI_MODEL=gpt-4  # 主模型，用于重任务
OPENAI_FAST_MODEL=gpt-3.5-turbo  # 可选：快速模型，用于对话和轻量任务
```

### 使用示例

**单论文分析（CLI）**
```bash
python main.py single --project "my-paper" --paper "workspace/inputs/sample_paper.md"
```

**多论文综述（CLI）**
```bash
python main.py survey --project "my-survey" --papers "paper1.md" "paper2.md"
```

**Python API**
```python
from pathlib import Path
from research_agent.agent import ResearchAgent
from research_agent.context import AgentContext

context = AgentContext(
    project_name="demo-paper",
    paper_path=Path("workspace/inputs/sample_paper.md")
)
agent = ResearchAgent()
result = agent.run_single(context)
print(result.run_id)
```

---

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

For questions or feedback, please open an issue on GitHub.

---

## Detailed Documentation (Chinese)

## Why this project matters

科研场景里的大模型应用，经常停留在“把论文内容复制给模型，然后要一个摘要”。这种方式的问题是：

- 结果不可复用
- 后续追问缺乏上下文锚点
- 多篇论文难以系统比较
- 同一篇论文会被反复处理，速度慢、成本高
- 与代码仓库、复现环境等真实科研环节脱节

`Research Agent` 想解决的是一个更真实的问题：

> 如何把论文阅读、结构化理解、对比分析、产物沉淀和后续交互组织成一个可扩展的 agent workflow。

---

## Core capabilities

### 1. 单篇论文快速阅读

支持输入：

- `txt`
- `md`
- `pdf`

默认采用**快速模式**，核心流程为：

- 导入论文文本
- 生成 `paper_digest.json`
- 提取：元信息、摘要、claims、结构、方法卡片
- 保存为 JSON / Markdown artifacts

输出示例：

- `paper_preview.txt`
- `paper_digest.json`
- `paper_metadata.json`
- `summary.md`
- `claims.md`
- `paper_structure.md`
- `method_card.md`
- `run_manifest.json`

### 2. 多论文对比与综述

对多篇论文逐篇做快速 digest 后，进入聚合阶段：

- 生成单篇 profile
- 生成对比矩阵 `compare_matrix.json`
- 生成冲突/不可直接比较报告 `comparison_report.md`
- 生成最终综述 `survey.md`

适合的任务包括：

- Related Work 预研
- 某个方向的论文横向对比
- 多篇论文方法脉络梳理
- 数据集 / 指标口径差异分析

### 3. Scoped Chat

在任务完成后，用户可以继续基于已有产物追问。

例如：

- 只基于 `compare_matrix.json` 继续提问
- 只基于 `repo_profile.json` 继续提问
- 默认基于全部 artifacts 回答

这让系统具备了“先分析，再追问”的闭环能力，而不是一次性输出。

### 4. 代码仓库理解基础能力

除了论文阅读，还支持本地仓库分析：

- 仓库画像 `repo_profile.json`
- Python AST 摘要 `ast_analysis.json`
- 依赖/环境建议 `env_resolution.json`

这是为了贴近真实科研场景：

> 研究人员不仅要读论文，还要看 official repo、判断复现依赖和代码结构。

---

## Architecture overview

项目采用 **Skill-based Agent Architecture**，并引入了 LLM 驱动的状态图编排器（Harness）。

### 主要模块

- `agent.py`：负责工作流编排，支持传统固定流水线和 Harness 模式
- `context.py`：负责上下文状态传递
- `llm.py`：负责模型调用封装、JSON 清洗、重试、流式输出、双模型切换
- `skills/`：负责具体能力模块，每个 skill 附带 `SkillMeta` 元数据
- `prompts/`：负责每个 skill 的 system prompt
- `prompt_stack.py`：负责组装 soul + skill 描述 + memory + task prompt
- `graph.py`：状态图数据结构（`StateNode` / `WorkflowGraph`）
- `registry.py`：技能注册表（`SkillMeta` / `SkillRegistry`）
- `planner.py`：LLM 决策节点逻辑
- `harness.py`：状态图执行器，支持 skill 执行、LLM 决策、用户确认暂停
- `workflows.py`：内置工作流图定义（single / survey / repo / auto）
- `web.py`：负责 Web 工作台与任务管理
- `cli.py`：负责命令行入口

### 核心设计思想

#### Skill 化

把复杂任务拆成多个边界明确的 skill，而不是一个超长 prompt。

#### Context 驱动

各个 skill 不直接耦合，而是通过 `AgentContext` 共享状态。

#### Artifact 落盘

把模型输出沉淀为结构化文件，而不是只返回瞬时回答。

#### Prompt Stack

每次 LLM 调用自动组装 soul（身份）+ skill 描述 + memory（用户偏好）+ task prompt，形成分层 system prompt。

#### Harness 编排

通过状态图 + LLM 决策节点实现动态工作流编排，在关键阶段暂停等待用户确认（半自主模式）。

#### 双入口

同时支持 CLI 和 Web，兼顾实验、演示与后续扩展。

---

## Current workflow

### Single paper (fast mode)

```text
START → IngestPaperSkill → PaperDigestSkill → [confirm] → END
```

### Multi-paper survey

```text
START → [batch: IngestPaper + PaperDigest per paper (concurrent)]
  → [confirm] → PaperComparatorSkill → ContradictionDetectorSkill
  → SurveyWriterSkill → [confirm] → END
```

### Repo analysis

```text
START → RepoIngestorSkill → ASTAnalyzerSkill → EnvResolverSkill → [confirm] → END
```

### Auto mode (Harness + LLM decision)

```text
START → [LLM decision: single/survey/repo?] → 自动路由到对应分支
```

---

## Project structure

```text
research-agent/
├── main.py
├── run_web.py
├── requirements.txt
├── .env.example
├── README.md
├── examples/
│   ├── quick_start.py
│   └── quick_start_survey.py
├── research_agent/
│   ├── __init__.py
│   ├── agent.py              # 工作流编排（固定模式 + Harness 模式）
│   ├── base.py               # BaseSkill / SkillResult 抽象
│   ├── cli.py                # CLI 入口
│   ├── config.py             # 路径与配置管理
│   ├── context.py            # AgentContext 共享状态
│   ├── graph.py              # StateNode / WorkflowGraph 状态图
│   ├── harness.py            # Harness 执行器（状态机循环）
│   ├── llm.py                # LLM 调用封装（含流式、双模型）
│   ├── planner.py            # LLM 决策节点逻辑
│   ├── prompt_stack.py       # System prompt 组装（soul+skills+memory+task）
│   ├── registry.py           # SkillMeta / SkillRegistry 技能注册表
│   ├── soul.md               # AI 身份定义（菜菜不吃鱼）
│   ├── memory.md             # 用户偏好与行为记忆
│   ├── web.py                # Flask Web 服务
│   ├── workflows.py          # 内置工作流图（single/survey/repo/auto）
│   ├── prompts/              # Skill system prompts + planner prompt
│   ├── skills/               # 技能模块（含 SkillMeta 元数据）
│   ├── static/               # 前端 JS / CSS
│   └── templates/            # HTML 模板
└── workspace/
    ├── inputs/
    ├── outputs/
    ├── runs/
    ├── sessions/
    └── uploads/
```

---

## Installation

```bash
python -m pip install -r requirements.txt
```

### Main dependencies

- `openai`
- `python-dotenv`
- `pydantic`
- `rich`
- `PyYAML`
- `pypdf`
- `flask`
- `werkzeug`

---

## Configuration

复制 `.env.example` 为 `.env`：

```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-5.4-mini
# 可选：为 chat 等轻量任务配置更快的模型
# OPENAI_FAST_MODEL=gpt-5.4-mini
```

### 字段说明

- `OPENAI_API_KEY`：模型服务 key
- `OPENAI_BASE_URL`：兼容 OpenAI 协议的自定义接口地址
- `OPENAI_MODEL`：主模型（用于论文分析、综述生成等重任务）
- `OPENAI_FAST_MODEL`：可选快速模型（用于 chat 追问、planner 决策等轻量任务）

如果未配置 `OPENAI_API_KEY`，系统会进入离线模式，输出占位结果，适合调试流程。

---

## Usage

## 1. Web UI

启动：

```bash
python run_web.py
```

浏览器打开：

```text
http://127.0.0.1:5000
```

### Web 支持的能力

- 单论文快速分析
- 多论文综述
- 代码仓库分析
- 任务状态 / 分阶段 ETA / trace 展示
- 任务取消
- Harness 模式下的用户确认交互
- artifact 查看
- session 历史记录
- scoped chat（支持流式输出）

## 2. CLI

### 单论文

```bash
python main.py single --project "my-paper" --paper "workspace/inputs/sample_paper.md"
```

### 多论文

```bash
python main.py survey --project "my-survey" --papers "workspace/inputs/sample_paper.md" "workspace/inputs/sample_paper_2.md"
```

## 3. Python API

```python
from pathlib import Path
from research_agent.agent import ResearchAgent
from research_agent.context import AgentContext

context = AgentContext(
    project_name="demo-paper",
    paper_path=Path("workspace/inputs/sample_paper.md")
)
agent = ResearchAgent()
result = agent.run_single(context)
print(result.run_id)
```

---

## Problems solved during development

### 1. 论文理解链路过长、推理太慢

最初单篇论文流程会多次向模型发送同一篇论文内容，分别做 metadata、summary、claims、structure 等任务。

**Solution**：引入 `PaperDigestSkill` 一次性产出全部核心信息，并把默认模式改为 fast mode。

### 2. 多论文分析时间太长

多篇论文逐篇串行处理，总时长随论文数线性增长。

**Solution**：多论文 digest 阶段改为并发执行（ThreadPoolExecutor，最多 4 路并行）。

### 3. 多论文难以系统比较

仅对多篇论文逐篇做摘要，不足以支撑真正的综述任务。

**Solution**：新增 `PaperComparatorSkill` + `ContradictionDetectorSkill` + `SurveyWriterSkill`，形成 profile → compare matrix → contradiction report → survey 链路。

### 4. 结果不可复用、后续追问无锚点

**Solution**：引入 artifact 落盘和 scoped chat，支持基于已生成结果继续提问。Chat 端支持 SSE 流式输出，降低等待感。

### 5. 对话响应延迟高

**Solution**：引入双模型机制（`OPENAI_FAST_MODEL`），chat 和 planner 等轻量任务自动走快速模型；同时支持流式输出。

### 6. 长任务无法暂停或取消

**Solution**：新增 cooperative cancellation 机制，前端可随时取消正在运行的任务。

### 7. 缺少 ETA 和阶段感知

**Solution**：新增 `estimate_stage_breakdown()`，前端展示分阶段 ETA 标签，当前阶段高亮。

### 8. 工作流硬编码，缺乏灵活性

**Solution**：引入 Harness 框架 — 状态图 + LLM 决策节点 + 用户确认机制，支持动态工作流编排。

### 9. 缺少 AI 身份和行为一致性

**Solution**：引入 soul.md（AI 身份定义）+ memory.md（用户偏好记忆）+ prompt_stack.py（自动组装分层 system prompt）。

---

## Limitations

### 1. 长文切分策略仍比较基础

目前仍以截断为主，未来可用 chunking + hierarchical summarization。

### 2. Harness 的 auto 模式尚未接入 Web 前端入口

auto_graph 已定义，但 Web 端暂未提供"智能模式"按钮，需手动调用 API 或后续迭代。

### 3. 评测体系不完整

缺少系统化 benchmark，主要以功能验证为主。

---

## Relation to OpenClaw / Skill / Harness

这个项目的设计理念与当前流行的大模型系统工程方向一致：

### Skill

能力被拆成边界明确的模块，每个 skill 附带 `SkillMeta` 元数据（输入、输出、适用模式），通过 `SkillRegistry` 统一管理。

### Harness

系统已实现完整的状态图编排器：

- `StateNode` / `WorkflowGraph` 定义工作流图
- `Harness` 执行器驱动状态机循环
- `decision` 节点由 LLM planner 动态选择转移
- `confirm` 节点暂停等待用户确认
- `batch` 节点支持并发处理
- 4 条内置工作流图（single / survey / repo / auto）

### Prompt Stack

每次 LLM 调用自动组装分层 system prompt：

- soul（身份、语气、行为边界）
- skill descriptions（当前可用技能列表）
- memory（用户偏好与长期规则）
- task prompt（具体任务指令）

---

## Roadmap

### Short-term

- Web 前端接入 Harness auto 模式入口
- 长文 chunking + hierarchical summarization
- 更精确的 ETA（基于历史运行数据）

### Mid-term

- 更完整的 repo understanding（多语言 AST、依赖图）
- citation / rebuttal / review skills
- 评测 benchmark pipeline

### Long-term

- multi-agent workflow（多智能体协作）
- event bus / callback hooks
- 研究工作流全链路支持（从论文阅读到实验复现）

---

## Resume-ready summary

设计并实现了一个基于 Skill 的科研智能体系统，支持单篇论文快速阅读、多篇论文对比综述、结构化产物生成、会话式追问和轻量代码仓库分析。项目采用 `Agent + Context + Prompt Stack + Skill + Harness` 架构，实现了论文导入、阅读卡片提取、对比矩阵生成、冲突识别、综述写作与 Web 工作台交互。通过 `paper digest` 快速模式和多论文并发处理显著减少推理时延，引入 soul/memory 分层 prompt stack 保证 AI 行为一致性，并构建了基于状态图 + LLM 决策节点的 Harness 编排器，支持动态工作流路由和半自主执行。