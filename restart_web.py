#!/usr/bin/env python3
"""
强制重启 Web 服务器脚本
解决 Uvicorn reload 模式下模块缓存问题
"""
import os
import sys
import subprocess
import shutil

def main():
    print("=" * 60)
    print("强制重启 Research Agent Web 服务器")
    print("=" * 60)

    # 1. 提示用户手动停止服务器
    print("\n[1/2] 请先停止当前运行的服务器:")
    print("  - 切换到运行 run_web.py 的终端")
    print("  - 按 Ctrl+C 停止服务器")
    print("  - 等待进程完全退出")
    input("\n按 Enter 继续...")

    # 2. 清理 Python 缓存
    print("\n[2/2] 清理 Python 缓存...")
    cache_dirs = []
    for root, dirs, files in os.walk('research_agent'):
        if '__pycache__' in dirs:
            cache_dirs.append(os.path.join(root, '__pycache__'))

    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"[OK] 删除缓存: {cache_dir}")
        except Exception as e:
            print(f"[WARN] 无法删除 {cache_dir}: {e}")

    # 3. 启动新服务器
    print("\n启动新服务器...")
    print("=" * 60)
    try:
        subprocess.run([sys.executable, 'run_web.py'], check=True)
    except KeyboardInterrupt:
        print("\n\n[INFO] 服务器已停止")
    except Exception as e:
        print(f"\n[ERROR] 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
