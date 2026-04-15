# Research Agent Enhancement Design

## 目标
将 Research Agent 升级为一个完整的科研助手，能够：
1. 自主从 GitHub 搜索和获取相关代码
2. 自动配置环境并运行实验
3. 分析现有方法并提出创新点
4. 设计和执行消融实验
5. 生成完整的综述、实验报告和分析文档

## 新增技能模块

### 1. GitHub Integration Skills

#### GitHubSearchSkill
- **功能**: 根据关键词搜索 GitHub 仓库
- **输入**: 搜索关键词、语言过滤、star 数阈值
- **输出**: 仓库列表（名称、描述、star 数、最近更新时间）
- **实现**: 使用 GitHub API

#### GitHubCloneSkill
- **功能**: 克隆指定的 GitHub 仓库到本地
- **输入**: 仓库 URL
- **输出**: 本地路径、克隆状态
- **实现**: git clone 命令

#### CodeAnalyzerSkill
- **功能**: 深度分析代码仓库结构和实现
- **输入**: 仓库路径
- **输出**: 
  - 代码结构图
  - 核心模块识别
  - 依赖关系
  - 实现方法总结
- **实现**: AST 分析 + LLM 理解

### 2. Experiment Execution Skills

#### EnvironmentSetupSkill
- **功能**: 自动配置实验环境
- **输入**: requirements.txt / environment.yml
- **输出**: 环境配置状态、依赖安装日志
- **实现**: 
  - 创建虚拟环境
  - 安装依赖
  - 验证环境

#### ExperimentRunnerSkill
- **功能**: 执行实验脚本
- **输入**: 
  - 脚本路径
  - 参数配置
  - 数据集路径
- **输出**: 
  - 实验日志
  - 结果文件
  - 性能指标
- **实现**: 
  - 子进程执行
  - 实时日志捕获
  - 超时控制
  - 错误处理

#### ResultCollectorSkill
- **功能**: 收集和整理实验结果
- **输入**: 实验输出目录
- **输出**: 
  - 结构化结果 JSON
  - 性能指标表格
  - 可视化图表
- **实现**: 解析日志、提取指标、生成图表

### 3. Innovation Skills

#### GapAnalyzerSkill
- **功能**: 分析现有方法的局限性和研究空白
- **输入**: 
  - 多篇论文的 digest
  - 代码分析结果
- **输出**: 
  - 方法局限性列表
  - 未解决的问题
  - 潜在改进方向
- **实现**: LLM 深度分析

#### InnovationProposerSkill
- **功能**: 提出创新点和改进方案
- **输入**: 
  - Gap 分析结果
  - 现有方法总结
- **输出**: 
  - 创新点列表（优先级排序）
  - 每个创新点的理论依据
  - 预期效果分析
  - 实现难度评估
- **实现**: LLM 创造性推理

#### ExperimentDesignerSkill
- **功能**: 设计实验方案（包括消融实验）
- **输入**: 
  - 创新点描述
  - 基线方法
- **输出**: 
  - 实验设计方案
  - 对比实验配置
  - 消融实验矩阵
  - 评估指标定义
- **实现**: LLM + 实验设计模板

### 4. Ablation Study Skills

#### AblationPlannerSkill
- **功能**: 规划消融实验
- **输入**: 
  - 模型组件列表
  - 创新点
- **输出**: 
  - 消融实验配置列表
  - 每个配置的说明
- **实现**: 组合生成 + LLM 优化

#### AblationExecutorSkill
- **功能**: 批量执行消融实验
- **输入**: 
  - 消融实验配置
  - 基础代码
- **输出**: 
  - 每个配置的实验结果
  - 对比数据
- **实现**: 循环调用 ExperimentRunnerSkill

#### AblationAnalyzerSkill
- **功能**: 分析消融实验结果
- **输入**: 
  - 所有消融实验结果
- **输出**: 
  - 组件贡献度分析
  - 性能对比表格
  - 可视化图表
  - 结论和洞察
- **实现**: 统计分析 + LLM 解读

### 5. Report Generation Skills

#### ComprehensiveSurveySkill
- **功能**: 生成完整的文献综述
- **输入**: 
  - 多篇论文分析
  - 方法演化分析
  - Gap 分析
- **输出**: 
  - 结构化综述文档
  - 方法对比表
  - 研究趋势图
- **实现**: 增强版 SurveyWriterSkill

#### ExperimentReportSkill
- **功能**: 生成实验报告
- **输入**: 
  - 实验设计
  - 实验结果
  - 消融分析
- **输出**: 
  - 完整实验报告
  - 结果分析
  - 可视化图表
- **实现**: LLM + 报告模板

#### PresentationGeneratorSkill
- **功能**: 生成汇报文档（PPT/Markdown）
- **输入**: 
  - 综述
  - 实验报告
  - 关键发现
- **输出**: 
  - Markdown 格式汇报
  - 可选：HTML slides
- **实现**: 模板生成 + LLM 润色

## 新工作流设计

### research_full Workflow

```
START
  ↓
[LLM Decision: 确定研究主题和目标]
  ↓
GitHubSearchSkill → 搜索相关仓库
  ↓
[User Confirm: 选择要分析的仓库]
  ↓
[Batch: GitHubCloneSkill + CodeAnalyzerSkill]
  ↓
[Batch: 论文搜索和分析（复用现有 survey 流程）]
  ↓
GapAnalyzerSkill → 分析研究空白
  ↓
InnovationProposerSkill → 提出创新点
  ↓
[User Confirm: 选择要实现的创新点]
  ↓
ExperimentDesignerSkill → 设计实验方案
  ↓
[User Confirm: 确认实验设计]
  ↓
EnvironmentSetupSkill → 配置环境
  ↓
[Batch: 基线实验 + 改进方法实验]
  ↓
AblationPlannerSkill → 规划消融实验
  ↓
AblationExecutorSkill → 执行消融实验
  ↓
ResultCollectorSkill → 收集所有结果
  ↓
AblationAnalyzerSkill → 分析消融结果
  ↓
[Parallel: ComprehensiveSurveySkill + ExperimentReportSkill + PresentationGeneratorSkill]
  ↓
[User Confirm: 审阅最终报告]
  ↓
END
```

## 技术实现要点

### 1. GitHub API 集成
- 使用 PyGithub 或 requests 直接调用 API
- 需要 GitHub Token（可选，提高 rate limit）
- 搜索、克隆、分析 README 和代码

### 2. 实验执行沙箱
- 使用 Docker 容器隔离实验环境（可选）
- 或使用 venv/conda 虚拟环境
- 超时控制和资源限制
- 日志实时捕获

### 3. 结果可视化
- matplotlib/seaborn 生成图表
- 保存为 PNG/SVG
- 嵌入到报告中

### 4. 安全考虑
- 代码执行前进行安全检查
- 限制文件系统访问
- 用户确认关键操作
- 日志记录所有操作

## 配置扩展

新增环境变量：
```bash
# GitHub API
GITHUB_TOKEN=your_github_token  # 可选，提高 API 限制

# 实验配置
EXPERIMENT_TIMEOUT=3600  # 单个实验超时时间（秒）
MAX_PARALLEL_EXPERIMENTS=2  # 最大并行实验数
USE_DOCKER=false  # 是否使用 Docker 隔离

# 资源限制
MAX_MEMORY_GB=8  # 最大内存使用
MAX_DISK_GB=50  # 最大磁盘使用
```

## 实现优先级

### Phase 1: GitHub Integration（第一阶段）
1. GitHubSearchSkill
2. GitHubCloneSkill
3. CodeAnalyzerSkill（增强版 RepoIngestorSkill）

### Phase 2: Innovation & Design（第二阶段）
1. GapAnalyzerSkill
2. InnovationProposerSkill
3. ExperimentDesignerSkill

### Phase 3: Experiment Execution（第三阶段）
1. EnvironmentSetupSkill
2. ExperimentRunnerSkill
3. ResultCollectorSkill

### Phase 4: Ablation Study（第四阶段）
1. AblationPlannerSkill
2. AblationExecutorSkill
3. AblationAnalyzerSkill

### Phase 5: Advanced Reporting（第五阶段）
1. ComprehensiveSurveySkill
2. ExperimentReportSkill
3. PresentationGeneratorSkill

### Phase 6: Integration（第六阶段）
1. 构建 research_full workflow
2. Web UI 集成
3. 端到端测试

## 预期效果

完成后，用户可以：
1. 输入研究主题（如 "transformer optimization"）
2. Agent 自动搜索相关论文和代码
3. 分析现有方法，提出 3-5 个创新点
4. 用户选择一个创新点
5. Agent 自动设计实验、配置环境、运行实验
6. 执行完整的消融实验
7. 生成包含综述、实验报告、消融分析的完整文档
8. 生成汇报 PPT/Markdown

整个流程可能需要数小时到数天（取决于实验复杂度），但大部分是自动化的。
