# 快速启动指南

## 安装

```bash
cd d:\myproject\research-agent
python -m pip install -r requirements.txt
```

## 配置（可选）

如果要使用 OpenAI API：

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY
```

## 启动 Web 界面

```bash
python run_web.py
```

然后在浏览器打开：`http://127.0.0.1:5000`

**功能**：
- 上传论文（支持 txt/md/pdf）
- 单论文分析：生成摘要、关键信息、大纲、初稿
- 多论文综述：生成对比分析和综述

## 命令行使用

### 单论文分析

```bash
python main.py single --project "my-paper" --paper "workspace/inputs/sample_paper.md"
```

### 多论文综述

```bash
python main.py survey --project "my-survey" --papers "workspace/inputs/sample_paper.md" "workspace/inputs/sample_paper_2.md"
```

## 示例

### Python 编程调用

```python
from pathlib import Path
from research_agent.agent import ResearchAgent
from research_agent.context import AgentContext

# 单论文
context = AgentContext(
    project_name="my-research",
    paper_path=Path("workspace/inputs/sample_paper.md")
)
agent = ResearchAgent()
result = agent.run_single(context)

print(f"Run ID: {result.run_id}")
print(f"Summary: {result.summary[:200]}...")
```

## 输出

所有产物保存在 `workspace/runs/<run_id>/`：
- `summary.md` - 结构化摘要
- `claims.md` - 关键信息
- `outline.md` - 写作大纲
- `draft.md` - 科研初稿
- `survey.md` - 多论文综述（仅多论文模式）
- `run_manifest.json` - 运行记录

## 离线模式

如果没有配置 `OPENAI_API_KEY`，程序会以离线模式运行，输出占位结果，方便先调通流程。

## 故障排除

**问题**：导入 PDF 时出错
**解决**：确保已安装 pypdf：`pip install pypdf`

**问题**：Web 界面无法访问
**解决**：确保 Flask 已安装：`pip install flask`

**问题**：API 调用失败
**解决**：检查 `.env` 中的 `OPENAI_API_KEY` 是否正确

---

更多信息见 `README.md`
