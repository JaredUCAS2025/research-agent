"""
Environment Setup Skill - 自动配置实验环境
"""
import json
import subprocess
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta


class EnvironmentSetupSkill(BaseSkill):
    """自动配置实验环境（虚拟环境、依赖安装）"""

    def run(self, context: AgentContext, llm) -> SkillResult:
        """
        配置实验环境

        Args:
            context: 需要包含 cloned_repo_path 或 requirements_file
        """
        repo_path = context.get("cloned_repo_path")
        requirements_file = context.get("requirements_file")

        if not repo_path and not requirements_file:
            return SkillResult(
                success=False,
                message="Missing cloned_repo_path or requirements_file in context",
                artifacts={}
            )

        # 确定工作目录
        if repo_path:
            work_dir = Path(repo_path)
        else:
            work_dir = Path(requirements_file).parent

        if not work_dir.exists():
            return SkillResult(
                success=False,
                message=f"Work directory does not exist: {work_dir}",
                artifacts={}
            )

        try:
            # 创建虚拟环境目录
            venv_dir = context.run_dir / "venv"

            # 设置环境
            setup_log = []

            # 1. 创建虚拟环境
            venv_result = self._create_virtualenv(venv_dir, setup_log)
            if not venv_result:
                return SkillResult(
                    success=False,
                    message="Failed to create virtual environment",
                    artifacts={"setup_log": setup_log}
                )

            # 2. 查找依赖文件
            req_files = self._find_requirement_files(work_dir)

            # 3. 安装依赖
            install_success = True
            installed_packages = []

            for req_file in req_files:
                success, packages = self._install_requirements(
                    venv_dir,
                    req_file,
                    setup_log
                )
                if success:
                    installed_packages.extend(packages)
                else:
                    install_success = False
                    setup_log.append(f"Warning: Failed to install from {req_file}")

            # 4. 验证环境
            validation = self._validate_environment(venv_dir, setup_log)

            # 保存设置日志
            log_path = context.run_dir / "environment_setup.log"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(setup_log))

            # 保存环境信息
            env_info = {
                "venv_path": str(venv_dir),
                "python_version": sys.version,
                "requirements_files": [str(f) for f in req_files],
                "installed_packages": installed_packages,
                "validation": validation,
                "setup_log": setup_log
            }

            env_info_path = context.run_dir / "environment_info.json"
            with open(env_info_path, "w", encoding="utf-8") as f:
                json.dump(env_info, f, indent=2, ensure_ascii=False)

            # 更新 context
            context.set("venv_path", str(venv_dir))
            context.set("environment_info", env_info)

            message = "Environment setup completed"
            if not install_success:
                message += " with some warnings"

            return SkillResult(
                success=True,
                message=message,
                artifacts={
                    "venv_path": str(venv_dir),
                    "environment_info": env_info,
                    "setup_log": str(log_path),
                    "env_info_json": str(env_info_path)
                }
            )

        except Exception as e:
            return SkillResult(
                success=False,
                message=f"Environment setup failed: {str(e)}",
                artifacts={}
            )

    def _create_virtualenv(self, venv_dir: Path, log: List[str]) -> bool:
        """创建虚拟环境"""
        try:
            log.append(f"Creating virtual environment at {venv_dir}")

            # 使用 venv 模块创建虚拟环境
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                log.append("✓ Virtual environment created successfully")
                return True
            else:
                log.append(f"✗ Failed to create virtual environment: {result.stderr}")
                return False

        except Exception as e:
            log.append(f"✗ Exception during venv creation: {str(e)}")
            return False

    def _find_requirement_files(self, work_dir: Path) -> List[Path]:
        """查找依赖文件"""
        req_files = []

        # 常见的依赖文件
        candidates = [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-test.txt",
            "setup.py",
            "environment.yml",
            "pyproject.toml"
        ]

        for candidate in candidates:
            file_path = work_dir / candidate
            if file_path.exists():
                req_files.append(file_path)

        return req_files

    def _install_requirements(
        self,
        venv_dir: Path,
        req_file: Path,
        log: List[str]
    ) -> tuple[bool, List[str]]:
        """安装依赖"""
        try:
            log.append(f"\nInstalling from {req_file.name}")

            # 获取 pip 路径
            if sys.platform == "win32":
                pip_path = venv_dir / "Scripts" / "pip.exe"
            else:
                pip_path = venv_dir / "bin" / "pip"

            if not pip_path.exists():
                log.append(f"✗ pip not found at {pip_path}")
                return False, []

            # 根据文件类型选择安装命令
            if req_file.name == "requirements.txt" or "requirements" in req_file.name:
                cmd = [str(pip_path), "install", "-r", str(req_file)]
            elif req_file.name == "setup.py":
                cmd = [str(pip_path), "install", "-e", str(req_file.parent)]
            else:
                log.append(f"⊘ Skipping {req_file.name} (unsupported format)")
                return True, []

            # 执行安装
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode == 0:
                log.append(f"✓ Successfully installed from {req_file.name}")

                # 提取已安装的包
                packages = self._extract_installed_packages(result.stdout)
                return True, packages
            else:
                log.append(f"✗ Installation failed: {result.stderr[:500]}")
                return False, []

        except subprocess.TimeoutExpired:
            log.append(f"✗ Installation timeout (exceeded 10 minutes)")
            return False, []
        except Exception as e:
            log.append(f"✗ Exception during installation: {str(e)}")
            return False, []

    def _extract_installed_packages(self, output: str) -> List[str]:
        """从安装输出中提取包名"""
        packages = []
        lines = output.split('\n')

        for line in lines:
            if "Successfully installed" in line:
                # 提取包名
                parts = line.split("Successfully installed")[1].strip().split()
                packages.extend(parts)

        return packages

    def _validate_environment(self, venv_dir: Path, log: List[str]) -> Dict[str, Any]:
        """验证环境"""
        validation = {
            "venv_exists": venv_dir.exists(),
            "pip_exists": False,
            "python_exists": False,
            "can_import_common_packages": {}
        }

        try:
            # 检查 pip
            if sys.platform == "win32":
                pip_path = venv_dir / "Scripts" / "pip.exe"
                python_path = venv_dir / "Scripts" / "python.exe"
            else:
                pip_path = venv_dir / "bin" / "pip"
                python_path = venv_dir / "bin" / "python"

            validation["pip_exists"] = pip_path.exists()
            validation["python_exists"] = python_path.exists()

            # 测试常见包
            if python_path.exists():
                common_packages = ["numpy", "torch", "tensorflow", "transformers"]

                for package in common_packages:
                    try:
                        result = subprocess.run(
                            [str(python_path), "-c", f"import {package}"],
                            capture_output=True,
                            timeout=10
                        )
                        validation["can_import_common_packages"][package] = (result.returncode == 0)
                    except:
                        validation["can_import_common_packages"][package] = False

            log.append("\n=== Environment Validation ===")
            log.append(f"Virtual environment exists: {validation['venv_exists']}")
            log.append(f"pip exists: {validation['pip_exists']}")
            log.append(f"python exists: {validation['python_exists']}")

        except Exception as e:
            log.append(f"Validation error: {str(e)}")

        return validation


# 注册技能
SKILL_META = SkillMeta(
    name="environment_setup",
    description="Automatically setup experiment environment with virtual env and dependencies",
    inputs_required=[],
    outputs_produced=["venv_path", "environment_info", "setup_log", "env_info_json"]
)
