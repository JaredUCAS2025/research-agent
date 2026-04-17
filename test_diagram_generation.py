"""测试图表生成功能"""
import sys
from pathlib import Path
from research_agent.context import AgentContext
from research_agent.skills.diagram_generator import DiagramGeneratorSkill
from research_agent.llm import LLMClient

# 创建测试上下文
context = AgentContext(project_name="test_diagrams")

# 模拟 survey 场景的数据
context.notes["survey_content"] = "This is a test survey content"
context.notes["survey_taxonomy"] = "Test taxonomy"
context.notes["survey_evolution"] = "Test evolution"

# 模拟 compare_matrix 数据
context.notes["compare_matrix"] = {
    "papers": [
        {
            "title": "FedAvg: Communication-Efficient Learning",
            "method_family": "Federated Averaging",
            "year": 2017,
            "key_innovation": "Averaging local models"
        },
        {
            "title": "FedProx: Federated Optimization",
            "method_family": "Federated Averaging",
            "year": 2020,
            "key_innovation": "Proximal term for heterogeneity"
        },
        {
            "title": "FedDyn: Dynamic Regularization",
            "method_family": "Dynamic Regularization",
            "year": 2021,
            "key_innovation": "Dynamic regularization"
        }
    ]
}

# 模拟单论文数据
context.paper_digest = {
    "title": "Test Paper",
    "method": "Test Method",
    "architecture": "Test Architecture"
}

context.method_card = "Test method card"

print("Testing diagram generation...")
print(f"Run directory: {context.run_dir}")

# 创建 diagram generator
generator = DiagramGeneratorSkill()
llm = LLMClient()

# 运行生成
result = generator.run(context, llm)

print(f"\nResult: {result.message}")

# 检查生成的文件
diagram_dir = context.run_dir / "diagrams"
if diagram_dir.exists():
    print(f"\nGenerated files in {diagram_dir}:")
    for file in diagram_dir.iterdir():
        print(f"  - {file.name} ({file.stat().st_size} bytes)")
else:
    print(f"\nNo diagrams directory created!")

print(f"\nGenerated diagrams info:")
if "generated_diagrams" in context.notes:
    for diagram in context.notes["generated_diagrams"]:
        print(f"  - {diagram.get('type')}: {diagram.get('title')}")
