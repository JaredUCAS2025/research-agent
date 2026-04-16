"""
测试图像生成功能
"""
import os
import sys
from pathlib import Path

# 设置输出编码为 UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from research_agent.context import AgentContext
from research_agent.skills.diagram_generator import DiagramGeneratorSkill
from research_agent.skills.ai_image_generator import AIImageGeneratorSkill


def test_diagram_generator():
    """测试学术图表生成"""
    print("\n" + "="*60)
    print("测试 1: 学术图表生成 (Diagram Generator)")
    print("="*60)

    skill = DiagramGeneratorSkill()
    context = AgentContext(project_name="test-diagrams")

    # 模拟一些研究数据
    context.notes["innovation_proposals"] = {
        "proposals": [{
            "title": "Attention-Based Anomaly Detection",
            "core_idea": "Use multi-head attention mechanism to detect anomalies in wind turbine sensor data",
            "full_description": "The proposed method consists of three main components: 1) Data preprocessing module, 2) Attention-based feature extraction, 3) Anomaly scoring mechanism"
        }]
    }

    context.notes["experiment_design"] = {
        "baseline_methods": [
            {"name": "Isolation Forest"},
            {"name": "One-Class SVM"}
        ],
        "proposed_method": {
            "name": "Attention-Anomaly",
            "components": ["Attention Layer", "LSTM Encoder", "Anomaly Scorer"]
        }
    }

    context.notes["experiment_results"] = {
        "results": [
            {"name": "Isolation Forest", "success": True, "metrics": {"F1": 0.75, "Precision": 0.72, "Recall": 0.78}},
            {"name": "One-Class SVM", "success": True, "metrics": {"F1": 0.78, "Precision": 0.76, "Recall": 0.80}},
            {"name": "Attention-Anomaly", "success": True, "metrics": {"F1": 0.85, "Precision": 0.83, "Recall": 0.87}}
        ]
    }

    context.notes["ablation_analysis"] = {
        "component_contributions": [
            {
                "removed_component": "Attention Layer",
                "performance_drop": {"F1": 0.08, "Precision": 0.07, "Recall": 0.09}
            },
            {
                "removed_component": "LSTM Encoder",
                "performance_drop": {"F1": 0.05, "Precision": 0.04, "Recall": 0.06}
            }
        ]
    }

    # 生成图表
    context.notes["diagram_type"] = "auto"
    result = skill.run(context, None)

    print(f"\n结果: {result.message}")

    # 检查生成的文件
    diagram_dir = context.run_dir / "diagrams"
    if diagram_dir.exists():
        print(f"\n生成的图表文件:")
        for file in diagram_dir.iterdir():
            print(f"  - {file.name} ({file.stat().st_size} bytes)")
    else:
        print("\n⚠️  未找到图表目录")

    return result


def test_ai_image_generator():
    """测试 AI 图像生成"""
    print("\n" + "="*60)
    print("测试 2: AI 图像生成 (AI Image Generator)")
    print("="*60)

    # 检查 API 密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  未设置 OPENAI_API_KEY，跳过 AI 图像生成测试")
        print("提示: 在 .env 文件中设置 OPENAI_API_KEY 以启用此功能")
        return None

    skill = AIImageGeneratorSkill()
    context = AgentContext(project_name="test-ai-images")

    # 手动指定图像提示词
    image_prompts = [
        {
            "title": "Neural Network Architecture",
            "prompt": "A clean technical diagram of a neural network with attention mechanism for anomaly detection. Show input layer, attention layers, LSTM encoder, and output layer. Professional academic style, white background, clear labels."
        }
    ]

    context.notes["image_prompts"] = image_prompts
    context.notes["image_model"] = "dalle3"

    print("\n正在生成 AI 图像（这可能需要几秒钟）...")
    result = skill.run(context, None)

    print(f"\n结果: {result.message}")

    # 检查生成的文件
    image_dir = context.run_dir / "ai_images"
    if image_dir.exists():
        print(f"\n生成的 AI 图像:")
        for file in image_dir.iterdir():
            if file.suffix in ['.png', '.jpg', '.jpeg']:
                print(f"  - {file.name} ({file.stat().st_size / 1024:.1f} KB)")
    else:
        print("\n⚠️  未找到图像目录")

    return result


def test_mermaid_rendering():
    """测试 Mermaid 渲染"""
    print("\n" + "="*60)
    print("测试 3: Mermaid 渲染检查")
    print("="*60)

    import subprocess

    try:
        result = subprocess.run(
            ["mmdc", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"\n✓ mermaid-cli 已安装: {result.stdout.strip()}")
            print("  可以自动渲染 Mermaid 图表为 SVG/PNG")
        else:
            print("\n✗ mermaid-cli 未正确安装")

    except FileNotFoundError:
        print("\n⚠️  mermaid-cli 未安装")
        print("\n安装方法:")
        print("  npm install -g @mermaid-js/mermaid-cli")
        print("\n或者:")
        print("  - 在 GitHub/GitLab 中直接预览 .mmd 文件")
        print("  - 使用 VS Code 的 Mermaid 插件")
        print("  - 访问 https://mermaid.live/ 在线预览")


def test_matplotlib():
    """测试 Matplotlib"""
    print("\n" + "="*60)
    print("测试 4: Matplotlib 检查")
    print("="*60)

    try:
        import matplotlib
        import matplotlib.pyplot as plt
        print(f"\n✓ Matplotlib 已安装: {matplotlib.__version__}")

        # 测试中文支持
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei']
            print("✓ 中文字体支持已配置")
        except:
            print("⚠️  中文字体可能不支持，图表中的中文可能显示为方块")

    except ImportError:
        print("\n✗ Matplotlib 未安装")
        print("安装方法: pip install matplotlib seaborn")


def main():
    print("\n" + "="*60)
    print("图像生成功能测试")
    print("="*60)

    # 测试环境检查
    test_mermaid_rendering()
    test_matplotlib()

    # 测试图表生成
    diagram_result = test_diagram_generator()

    # 测试 AI 图像生成（如果配置了 API 密钥）
    ai_result = test_ai_image_generator()

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    if diagram_result and diagram_result.message.startswith("Successfully"):
        print("✓ 学术图表生成: 成功")
    else:
        print("✗ 学术图表生成: 失败")

    if ai_result:
        if ai_result.message.startswith("Successfully"):
            print("✓ AI 图像生成: 成功")
        else:
            print("✗ AI 图像生成: 失败")
    else:
        print("⊘ AI 图像生成: 跳过（未配置 API 密钥）")

    print("\n查看生成的文件:")
    print(f"  workspace/runs/")

    print("\n详细使用指南:")
    print(f"  IMAGE_GENERATION_GUIDE.md")


if __name__ == "__main__":
    main()
