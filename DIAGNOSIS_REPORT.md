# 🔍 图表生成问题完整诊断报告

## 问题现象
多论文综述分析完成后，没有生成任何图表，终端也没有显示图表生成相关的日志。

---

## 深度排查结果

### ✅ 1. 代码层面 - 完全正确
**文件**: `research_agent/agent.py`

**第 46-51 行**:
```python
self.multi_paper_skills: list[BaseSkill] = [
    PaperComparatorSkill(),
    ContradictionDetectorSkill(),
    SurveyWriterSkill(),
    DiagramGeneratorSkill(),  # ✅ 已添加
]
```

**第 197-202 行**:
```python
multi_steps = len(self.multi_paper_skills)  # 应该是 4
for index, skill in enumerate(self.multi_paper_skills, start=1):
    progress = (paper_count + index / multi_steps) / (paper_count + 1)
    context.report_progress(skill.name, f"正在执行多论文阶段：{skill.name}", min(progress, 0.98))
    result = skill.run(context=context, llm=self.llm)
    context.add_trace(skill=result.name, message=result.message, step=index, total_steps=multi_steps, phase="multi")
```

**验证**:
```bash
$ python -c "from research_agent.agent import ResearchAgent; agent = ResearchAgent(); print(len(agent.multi_paper_skills))"
4  # ✅ 正确
```

---

### ❌ 2. 运行时状态 - 使用旧代码
**文件**: `workspace/runs/a70a5a2b54/run_manifest.json`

**trace 字段**:
```json
"trace": [
  {"skill": "ingest_paper", ...},
  {"skill": "ingest_paper", ...},
  {"skill": "paper_digest", ...},
  {"skill": "paper_digest", ...},
  {"skill": "paper_comparator", "step": 1, "total_steps": 3},  # ❌ total_steps=3
  {"skill": "contradiction_detector", "step": 2, "total_steps": 3},
  {"skill": "survey_writer", "step": 3, "total_steps": 3}
  // ❌ 没有 diagram_generator
]
```

**问题**: `total_steps: 3` 说明运行时的 `multi_paper_skills` 只有 3 个元素，而不是代码中的 4 个。

---

### 🎯 3. 根本原因 - Uvicorn Reload 缓存

**Uvicorn 的 `--reload` 模式工作原理**:
1. 监控文件变化
2. 检测到变化后重启 worker 进程
3. **但是**: 已经导入的 Python 模块会被缓存在内存中
4. **结果**: 修改 `agent.py` 后，`ResearchAgent.__init__` 中的列表定义没有重新执行

**证据**:
- 代码显示 `len(multi_paper_skills) = 4`
- 运行时显示 `total_steps = 3`
- 说明服务器进程中的 `ResearchAgent` 实例是用旧代码创建的

---

## 解决方案

### 方案 1: 完全重启服务器（推荐）

1. **停止服务器**:
   - 切换到运行 `run_web.py` 的终端
   - 按 `Ctrl+C`
   - **等待看到命令提示符**（确保进程完全退出）

2. **清理缓存**（可选但推荐）:
   ```bash
   python restart_web.py
   ```
   或手动删除:
   ```bash
   find research_agent -type d -name __pycache__ -exec rm -rf {} +
   ```

3. **重新启动**:
   ```bash
   python run_web.py
   ```

### 方案 2: 使用自动重启脚本

```bash
python restart_web.py
```

该脚本会：
1. 提示你手动停止服务器
2. 清理所有 `__pycache__` 目录
3. 重新启动服务器

---

## 验证方法

### 重启后应该看到的日志

**启动时**:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**执行多论文分析时**:
```
[DIAGRAM GENERATOR] STARTED
[DEBUG] Context state:
  - paper_count: 2
  - has paper_digest: True
  - has compare_matrix: True
  - has survey: True
[OK] Found compare_matrix, adding comparison diagrams
[GEN] Generating method comparison chart...
[GEN] Generating performance comparison chart...
[GEN] Generating research evolution timeline...
[CHART] Total diagrams generated: 5
[DONE] DIAGRAM GENERATOR COMPLETED: 5 diagrams
```

### 检查 run_manifest.json

```bash
cat workspace/runs/最新run_id/run_manifest.json | grep -A 20 '"trace"'
```

应该看到:
```json
"trace": [
  ...,
  {"skill": "paper_comparator", "step": 1, "total_steps": 4},  # ✅ 4 不是 3
  {"skill": "contradiction_detector", "step": 2, "total_steps": 4},
  {"skill": "survey_writer", "step": 3, "total_steps": 4},
  {"skill": "diagram_generator", "step": 4, "total_steps": 4}  # ✅ 出现了
]
```

---

## 技术细节

### 为什么 Uvicorn Reload 不够

**Uvicorn 的 reload 机制**:
- 使用 `watchfiles` 监控文件变化
- 检测到变化后发送 SIGHUP 信号给 worker
- Worker 重新导入 `app` 对象

**问题**:
- `app` 对象在 `web.py` 中定义
- `ResearchAgent` 实例在 `web.py` 启动时创建一次
- 修改 `agent.py` 后，`web.py` 没有重新执行
- 所以 `ResearchAgent` 实例还是旧的

**解决方案**:
- 完全杀死进程，清空内存
- 重新启动，重新导入所有模块
- 重新创建 `ResearchAgent` 实例

---

## 已修复的其他问题

### ✅ Windows 控制台编码
- 移除所有 emoji 字符
- 使用纯文本标记: `[DIAGRAM GENERATOR]`, `[DEBUG]`, `[OK]` 等

### ✅ 日志刷新
- 所有 `print()` 语句添加 `flush=True`
- 确保日志立即显示在终端

### ✅ 技能注册
- `DiagramGeneratorSkill` 已添加到 `single_paper_skills`
- `DiagramGeneratorSkill` 已添加到 `multi_paper_skills`
- 已在 `SkillRegistry` 中注册

### ✅ 图表嵌入
- 图表会自动追加到 `survey.md` 和 `comparison_report.md` 末尾
- 使用 Markdown 图片语法: `![标题](diagrams/filename.png)`
- Web 界面可直接渲染显示

---

## 总结

**问题**: Uvicorn reload 模式下，Python 模块缓存导致代码修改不生效

**解决**: 完全重启服务器，清空内存缓存

**验证**: 检查终端日志和 run_manifest.json 中的 trace 字段

**预期**: 多论文分析完成后，自动生成 5 种图表并嵌入到文档中
