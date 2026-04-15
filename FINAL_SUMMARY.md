# Research Agent - 完整项目总结

## 🎯 项目概览

从零开始构建了一个**基于 skill 的科研阅读与写作 agent**，包含命令行工具和 Web 交互界面。

**项目位置**：`d:\myproject\research-agent`

**状态**：✅ MVP 完成，可直接使用

---

## ✨ 核心功能

### 1. 单论文分析工作流
- 导入论文（txt/md/pdf）
- 生成结构化摘要
- 抽取关键信息（贡献、方法、实验、局限）
- 生成写作大纲
- 生成科研初稿

### 2. 多论文综述工作流
- 批量导入多篇论文
- 各自生成摘要
- 对比分析和综述生成

### 3. 交互方式
- **Web 界面**：可视化、易用、无需命令行
- **命令行**：快速、脚本化、适合自动化
- **Python API**：编程调用、灵活集成

### 4. 离线模式
- 无 API Key 时可运行
- 输出占位结果，方便调试流程

---

## 🏗️ 技术架构

### Skill 插件系统（6 个 skills）

```
ingest_paper → summarize_paper → extract_claims → outline_writer → draft_writer → survey_writer
```

### 核心模块

| 模块 | 功能 |
|------|------|
| agent.py | 两种工作流编排 |
| cli.py | 命令行接口 |
| web.py | Flask Web 服务 |
| llm.py | OpenAI API 客户端 |
| context.py | 执行上下文管理 |
| config.py | 配置加载 |
| base.py | Skill 基类 |

---

## 📦 项目结构

```
research-agent/
├── main.py                    # CLI 入口
├── run_web.py                 # Web 服务入口
├── requirements.txt           # 依赖
├── .env.example              # 配置模板
├── README.md                 # 完整文档
├── QUICKSTART.md             # 快速启动
│
├── research_agent/
│   ├── agent.py              # 核心 agent
│   ├── cli.py                # 命令行接口
│   ├── web.py                # Web 服务
│   ├── skills/               # 6 个 skill
│   ├── prompts/              # 5 个中文提示词
│   ├── templates/            # HTML 模板
│   └── static/               # CSS + JS
│
├── examples/
│   ├── quick_start.py
│   └── quick_start_survey.py
│
└── workspace/
    ├── inputs/               # 示例论文
    └── runs/                 # 运行产物
```

---

## 🚀 快速开始

### 启动 Web 界面

```bash
cd d:\myproject\research-agent
python run_web.py
```

打开浏览器：`http://127.0.0.1:5000`

### 或使用命令行

```bash
python main.py single --project "my-paper" --paper "workspace/inputs/sample_paper.md"
python main.py survey --project "my-survey" --papers "paper1.md" "paper2.md"
```

---

## ✅ 已验证

- ✅ 单论文模式运行成功
- ✅ 多论文模式运行成功
- ✅ Web 界面加载成功
- ✅ 离线模式正常工作
- ✅ 代码无 lint 错误

---

## 📝 使用示例

### Web 界面
1. 打开 `http://127.0.0.1:5000`
2. 上传论文（txt/md/pdf）
3. 查看结果（摘要、关键信息、大纲、初稿）

### Python API
```python
from pathlib import Path
from research_agent.agent import ResearchAgent
from research_agent.context import AgentContext

context = AgentContext(project_name="test", paper_path=Path("paper.md"))
agent = ResearchAgent()
result = agent.run_single(context)
```

---

## 🔮 下一步扩展

1. 引用管理与参考文献
2. Review / Rebuttal 写作模式
3. 知识库持久化
4. 批量处理
5. 版本控制

---

**版本**：1.0 MVP | **状态**：✅ 可直接使用
