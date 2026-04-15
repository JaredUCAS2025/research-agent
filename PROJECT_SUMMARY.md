# Research Agent - 项目总结

## 完成内容

从零开始构建了一个**基于 skill 的科研阅读与写作 agent**，具备以下功能：

### 核心功能
- ✅ 单论文分析工作流
- ✅ 多论文综述工作流
- ✅ 支持 txt / md / pdf 格式
- ✅ 离线模式（无 API Key 时可运行）
- ✅ 结构化输出（JSON + Markdown）

### Skill 插件系统
1. `ingest_paper` - 导入论文（支持 PDF）
2. `summarize_paper` - 生成结构化摘要
3. `extract_claims` - 抽取关键信息
4. `outline_writer` - 生成写作大纲
5. `draft_writer` - 生成科研初稿
6. `survey_writer` - 生成多论文综述

### 项目结构
```
research-agent/
├── main.py                    # 入口
├── requirements.txt           # 依赖（包含 pypdf）
├── .env.example              # 配置模板
├── README.md                 # 完整文档
├── research_agent/
│   ├── agent.py              # 两种工作流（单论文 + 多论文）
│   ├── cli.py                # 命令行接口
│   ├── base.py               # Skill 基类
│   ├── context.py            # 执行上下文
│   ├── config.py             # 配置管理
│   ├── llm.py                # LLM 客户端
│   ├── skills/               # 6 个 skill 实现
│   └── prompts/              # 5 个中文提示词
├── examples/
│   ├── quick_start.py        # 单论文示例
│   └── quick_start_survey.py # 多论文示例
└── workspace/
    ├── inputs/               # 示例论文
    ├── outputs/
    └── runs/                 # 运行产物
```

## 使用方式

### 单论文分析
```bash
python main.py single --project "my-paper" --paper "workspace/inputs/sample_paper.md"
```

### 多论文综述
```bash
python main.py survey --project "my-survey" --papers "paper1.md" "paper2.md" "paper3.md"
```

### 编程调用
```python
from research_agent.agent import ResearchAgent
from research_agent.context import AgentContext

context = AgentContext(project_name="test", paper_path=Path("paper.md"))
agent = ResearchAgent()
result = agent.run_single(context)
```

## 技术栈

- **Python 3.8+**
- **OpenAI API**（可选，支持离线模式）
- **pypdf** - PDF 解析
- **pydantic** - 数据验证
- **rich** - 命令行输出
- **python-dotenv** - 环境配置

## 运行验证

已成功运行以下测试：
- ✅ 单论文模式：生成 summary / claims / outline / draft
- ✅ 多论文模式：生成 survey
- ✅ 离线模式：无 API Key 时正常运行
- ✅ 代码质量：无 lint 错误

## 下一步扩展方向

1. **引用管理** - 自动提取和管理参考文献
2. **写作模式** - 支持 review / rebuttal / survey 三种模式
3. **知识库** - 持久化论文卡片和关系图
4. **Web 界面** - 构建前端交互
5. **外部 skill** - 适配 Cursor/Codex skill 规范
6. **批量处理** - 支持文件夹批量导入
7. **版本控制** - 追踪写作版本演变

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置 API（可选）：
   ```bash
   cp .env.example .env
   # 编辑 .env，填入 OPENAI_API_KEY
   ```

3. 运行示例：
   ```bash
   python main.py single --project "test" --paper "workspace/inputs/sample_paper.md"
   ```

4. 查看产物：
   ```bash
   ls workspace/runs/<run_id>/
   ```

## 代码质量

- ✅ 类型注解完整
- ✅ 无 lint 错误
- ✅ 模块化设计
- ✅ 易于扩展

---

**项目位置**：`d:\myproject\research-agent`

**状态**：MVP 完成，可直接使用
