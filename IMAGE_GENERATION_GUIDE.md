# 图像生成功能使用指南

本系统现在支持两种类型的图像生成：

## 1. 学术图表生成 (Diagram Generator)

自动生成论文所需的各类图表，包括：
- 架构图 (Architecture Diagrams)
- 流程图 (Workflow Diagrams)
- 结果对比图 (Comparison Charts)
- 消融实验热力图 (Ablation Heatmaps)
- 方法对比表 (Method Comparison)
- 系统总览图 (System Overview)

### 技术栈
- **Mermaid**: 用于生成流程图、架构图
- **Matplotlib**: 用于生成统计图表、热力图
- **Graphviz** (可选): 用于复杂图结构

### 使用方法

#### 自动模式
系统会根据研究内容自动生成相关图表：

```python
from research_agent.agent import ResearchAgent
from research_agent.context import AgentContext

agent = ResearchAgent()
context = AgentContext(project_name="my-research")

# 设置为自动生成所有图表
context.set("diagram_type", "auto")

# 运行图表生成技能
harness = agent.run_with_harness("diagram_generator", context)
```

#### 手动指定
```python
# 只生成架构图
context.set("diagram_type", "innovation_architecture")

# 或生成多个
context.set("diagram_type", ["architecture", "workflow", "results_comparison"])
```

### 输出位置
所有图表保存在：`workspace/runs/{run_id}/diagrams/`

### Mermaid 渲染

生成的 `.mmd` 文件可以：
1. 在 GitHub/GitLab 中直接预览
2. 使用 VS Code 的 Mermaid 插件预览
3. 使用 `mermaid-cli` 转换为 SVG/PNG：

```bash
# 安装 mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# 渲染为 SVG
mmdc -i architecture.mmd -o architecture.svg

# 渲染为 PNG
mmdc -i architecture.mmd -o architecture.png
```

---

## 2. AI 图像生成 (AI Image Generator)

使用 AI 模型生成概念图、示意图等。

### 支持的模型

#### DALL-E 3 (OpenAI)
- **优点**: 质量最高，理解能力强
- **缺点**: 需要付费
- **配置**:
  ```bash
  # .env 文件
  OPENAI_API_KEY=sk-...
  IMAGE_MODEL=dalle3
  ```

#### 通义万相 (阿里云)
- **优点**: 国内可用，速度快
- **缺点**: 需要阿里云账号
- **配置**:
  ```bash
  # .env 文件
  DASHSCOPE_API_KEY=sk-...
  IMAGE_MODEL=tongyi
  ```

#### Stable Diffusion (本地/API)
- **优点**: 开源，可本地部署
- **缺点**: 需要配置本地服务
- **配置**:
  ```bash
  # .env 文件
  SD_API_URL=http://localhost:7860
  IMAGE_MODEL=stable_diffusion
  ```

### 使用方法

#### 自动生成
系统会根据研究内容自动生成图像提示词：

```python
context = AgentContext(project_name="my-research")

# 已有创新提案时，会自动生成概念图
context.set("innovation_proposals", {...})

# 运行 AI 图像生成
harness = agent.run_with_harness("ai_image_generator", context)
```

#### 手动指定提示词
```python
image_prompts = [
    {
        "title": "System Architecture",
        "prompt": "A clean technical diagram showing a neural network architecture with attention mechanism, professional academic style, white background"
    },
    {
        "title": "Data Flow",
        "prompt": "Illustration of data preprocessing pipeline for machine learning, minimalist design, clear labels"
    }
]

context.set("image_prompts", image_prompts)
```

### 提示词优化技巧

系统会自动为学术用途优化提示词，但你也可以手动添加：

**推荐关键词**:
- `professional technical illustration`
- `academic paper quality`
- `clean white background`
- `clear labels and annotations`
- `high resolution`
- `minimalist design`
- `schematic diagram`
- `vector style`

**避免的关键词**:
- `artistic`, `creative`, `colorful` (除非需要)
- `photorealistic` (学术图表通常不需要)
- `3D render` (除非特定需要)

### 输出位置
所有 AI 图像保存在：`workspace/runs/{run_id}/ai_images/`

---

## 3. 集成到完整研究流程

在 `research_full` 工作流中自动生成图表：

### 修改工作流
编辑 `research_agent/workflows.py`，在报告生成后添加图表生成：

```python
# 在 research_full_graph() 函数中添加
g.add(StateNode(
    name="generate_diagrams",
    node_type="skill",
    skill_name="diagram_generator",
    transitions={"default": "generate_ai_images"}
))

g.add(StateNode(
    name="generate_ai_images",
    node_type="skill",
    skill_name="ai_image_generator",
    transitions={"default": "end"}
))
```

---

## 4. 常见问题

### Q: Mermaid 图表无法渲染？
A: 确保安装了 `mermaid-cli`:
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Q: DALL-E 3 报错 "API key not found"？
A: 检查 `.env` 文件中是否设置了 `OPENAI_API_KEY`

### Q: Matplotlib 图表中文显示乱码？
A: 安装中文字体：
```python
# 在代码中添加
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows
plt.rcParams['axes.unicode_minus'] = False
```

### Q: 如何批量生成图表？
A: 使用循环或列表：
```python
diagram_types = [
    "innovation_architecture",
    "experiment_workflow",
    "results_comparison",
    "ablation_heatmap"
]

for dtype in diagram_types:
    context.set("diagram_type", dtype)
    # 生成图表
```

---

## 5. 示例：完整的图表生成流程

```python
from research_agent.agent import ResearchAgent
from research_agent.context import AgentContext

# 初始化
agent = ResearchAgent()
context = AgentContext(project_name="wind-turbine-detection")

# 1. 运行完整研究流程
context.set("github_query", "wind turbine anomaly detection")
context.set("language", "python")
context.set("min_stars", 10)

harness = agent.run_with_harness("research_full", context)

# 2. 生成学术图表
context.set("diagram_type", "auto")
diagram_result = agent.run_with_harness("diagram_generator", context)

# 3. 生成 AI 图像
context.set("image_model", "dalle3")
image_result = agent.run_with_harness("ai_image_generator", context)

# 4. 查看结果
print(f"Generated diagrams: {context.get('generated_diagrams')}")
print(f"Generated AI images: {context.get('generated_ai_images')}")
```

---

## 6. 高级配置

### 自定义 Mermaid 主题
创建 `mermaid-config.json`:
```json
{
  "theme": "default",
  "themeVariables": {
    "primaryColor": "#4A90E2",
    "primaryTextColor": "#333",
    "primaryBorderColor": "#2C5F8D",
    "lineColor": "#666",
    "secondaryColor": "#E8F4F8",
    "tertiaryColor": "#F5F5F5"
  }
}
```

### 自定义 Matplotlib 样式
```python
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-paper')  # 学术论文风格
plt.rcParams['figure.dpi'] = 300     # 高分辨率
plt.rcParams['font.size'] = 10       # 字体大小
```

---

## 7. 成本估算

### DALL-E 3
- 标准质量 (1024x1024): $0.040/张
- 高质量 (1024x1024): $0.080/张

### 通义万相
- 按次计费，具体查看阿里云定价

### Stable Diffusion
- 本地部署：免费（需要 GPU）
- API 服务：根据服务商定价

---

## 8. 最佳实践

1. **先生成 Mermaid 图表**：快速、免费、易修改
2. **AI 图像用于概念图**：复杂的概念示意图使用 AI 生成
3. **统计图表用 Matplotlib**：精确的数据可视化
4. **保存原始文件**：保留 `.mmd` 和提示词，方便后续修改
5. **版本控制**：将生成的图表加入 git，便于追踪变化

---

## 9. 故障排除

### 图表生成失败
```bash
# 检查依赖
pip install matplotlib seaborn

# 检查 mermaid-cli
mmdc --version

# 查看错误日志
cat workspace/runs/{run_id}/diagrams/generation.log
```

### AI 图像生成超时
- 增加超时时间
- 简化提示词
- 检查网络连接
- 切换到其他模型

---

## 10. 参考资源

- [Mermaid 官方文档](https://mermaid.js.org/)
- [DALL-E 3 API 文档](https://platform.openai.com/docs/guides/images)
- [通义万相文档](https://help.aliyun.com/zh/dashscope/)
- [Matplotlib 图库](https://matplotlib.org/stable/gallery/index.html)
- [学术论文图表规范](https://www.nature.com/nature/for-authors/formatting-guide)
