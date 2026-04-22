# 🚨 重启服务器指南

## 问题
Uvicorn 的 `--reload` 模式不会重新加载已导入的 Python 模块，导致代码修改后不生效。

## 解决方案

### 方法1：完全重启（推荐）
1. 在运行 `run_web.py` 的终端按 `Ctrl+C`
2. **等待进程完全退出**（看到命令提示符）
3. 再次运行：`python run_web.py`

### 方法2：强制杀死进程
```bash
# Windows
taskkill /F /IM python.exe

# 然后重新启动
python run_web.py
```

### 方法3：使用新的启动脚本
```bash
python restart_web.py
```

## 验证是否生效
重启后，在终端应该看到：
```
[DIAGRAM GENERATOR] Checking if diagram generation is needed...
[DIAGRAM GENERATOR] Found survey content, will generate diagrams
[DIAGRAM GENERATOR] Generating 5 types of diagrams...
```

## 当前状态
- ✅ 代码已修复（multi_paper_skills 包含 DiagramGeneratorSkill）
- ✅ 单论文流程已包含图表生成
- ✅ 多论文流程已包含图表生成
- ⚠️ **需要完全重启服务器才能生效**
