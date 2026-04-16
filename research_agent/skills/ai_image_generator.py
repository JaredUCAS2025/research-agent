"""
AI Image Generator Skill - 使用 AI 模型生成论文插图
支持：DALL-E 3, Stable Diffusion, 通义万相等
"""
import json
import os
import base64
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from research_agent.base import BaseSkill, SkillResult
from research_agent.context import AgentContext
from research_agent.registry import SkillMeta
from research_agent.llm import LLMClient


class AIImageGeneratorSkill(BaseSkill):
    """使用 AI 生成学术论文所需的概念图、示意图"""

    def __init__(self):
        super().__init__()
        self.llm = LLMClient()

        # 支持的模型
        self.models = {
            "dalle3": self._generate_dalle3,
            "tongyi": self._generate_tongyi,
            "stable_diffusion": self._generate_stable_diffusion,
        }

    def run(self, context: AgentContext, llm) -> SkillResult:
        """
        生成 AI 图像

        Args:
            context: 需要包含 image_prompts 或自动从其他分析结果生成
        """
        # 获取配置
        model = context.notes.get("image_model", os.getenv("IMAGE_MODEL", "dalle3"))
        image_prompts = context.notes.get("image_prompts", [])

        # 如果没有提供 prompts，自动生成
        if not image_prompts:
            image_prompts = self._auto_generate_prompts(context)

        if not image_prompts:
            return SkillResult(
                name="ai_image_generator",
                message="No image prompts provided or generated"
            )

        try:
            generated_images = []
            image_dir = context.run_dir / "ai_images"
            image_dir.mkdir(exist_ok=True)

            generator = self.models.get(model)
            if not generator:
                return SkillResult(
                    name="ai_image_generator",
                    message=f"Unsupported model: {model}"
                )

            for i, prompt_data in enumerate(image_prompts, 1):
                if isinstance(prompt_data, str):
                    prompt = prompt_data
                    title = f"Image {i}"
                else:
                    prompt = prompt_data.get("prompt", "")
                    title = prompt_data.get("title", f"Image {i}")

                # 优化 prompt（添加学术风格）
                enhanced_prompt = self._enhance_prompt_for_academic(prompt)

                # 生成图像
                result = generator(enhanced_prompt, image_dir, f"image_{i}", title)

                if result:
                    generated_images.append(result)

            # 生成图像索引
            index = self._generate_image_index(generated_images)
            index_path = image_dir / "image_index.md"
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index)

            # 更新 context
            context.notes.__setitem__("generated_ai_images", generated_images)

            return SkillResult(
                name="ai_image_generator",
                message=f"Successfully generated {len(generated_images)} AI images"
            )

        except Exception as e:
            return SkillResult(
                name="ai_image_generator",
                message=f"AI image generation failed: {str(e)}"
            )

    def _auto_generate_prompts(self, context: AgentContext) -> List[Dict[str, str]]:
        """根据研究内容自动生成图像 prompts"""

        prompts = []

        # 从创新提案生成概念图
        innovation = context.notes.get("innovation_proposals", {})
        proposals = innovation.get("proposals", [])

        if proposals:
            selected = proposals[0]

            # 使用 LLM 生成图像描述
            llm_prompt = f"""Based on this research innovation, generate a detailed image prompt for creating a conceptual illustration:

Title: {selected.get('title', 'N/A')}
Core Idea: {selected.get('core_idea', 'N/A')}

Generate a prompt for an AI image generator that will create a clear, professional illustration showing the key concept.
The image should be suitable for an academic paper.

Format: Just output the image prompt, no explanation.
Style: Clean, professional, technical illustration style.
"""

            try:
                image_prompt = self.llm.complete("", llm_prompt, max_tokens=200)
                prompts.append({
                    "title": "Innovation Concept Illustration",
                    "prompt": image_prompt.strip()
                })
            except:
                pass

        # 从实验设计生成流程图概念
        exp_design = context.notes.get("experiment_design", {})
        if exp_design:
            prompts.append({
                "title": "Experiment Pipeline Illustration",
                "prompt": "A clean technical diagram showing a machine learning experiment pipeline with data preprocessing, model training, and evaluation stages. Professional academic style, white background, clear labels."
            })

        return prompts

    def _enhance_prompt_for_academic(self, prompt: str) -> str:
        """为学术用途优化 prompt"""

        # 添加学术风格关键词
        style_keywords = [
            "professional technical illustration",
            "clean white background",
            "clear labels and annotations",
            "academic paper quality",
            "high resolution",
            "minimalist design"
        ]

        # 如果 prompt 中没有风格描述，添加
        if not any(keyword in prompt.lower() for keyword in ["style", "professional", "academic"]):
            prompt += f". Style: {', '.join(style_keywords[:3])}"

        return prompt

    def _generate_dalle3(
        self,
        prompt: str,
        output_dir: Path,
        filename: str,
        title: str
    ) -> Optional[Dict[str, Any]]:
        """使用 DALL-E 3 生成图像"""

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "title": title,
                "prompt": prompt,
                "error": "OPENAI_API_KEY not set"
            }

        try:
            url = "https://api.openai.com/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "standard"
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            image_url = result["data"][0]["url"]

            # 下载图像
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()

            image_path = output_dir / f"{filename}.png"
            with open(image_path, "wb") as f:
                f.write(image_response.content)

            return {
                "title": title,
                "prompt": prompt,
                "model": "dall-e-3",
                "image_file": str(image_path),
                "url": image_url
            }

        except Exception as e:
            return {
                "title": title,
                "prompt": prompt,
                "model": "dall-e-3",
                "error": str(e)
            }

    def _generate_tongyi(
        self,
        prompt: str,
        output_dir: Path,
        filename: str,
        title: str
    ) -> Optional[Dict[str, Any]]:
        """使用通义万相生成图像"""

        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return {
                "title": title,
                "prompt": prompt,
                "error": "DASHSCOPE_API_KEY not set"
            }

        try:
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
            headers = {
                "X-DashScope-Async": "enable",
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "wanx-v1",
                "input": {
                    "prompt": prompt
                },
                "parameters": {
                    "size": "1024*1024",
                    "n": 1
                }
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()

            # 通义万相是异步的，需要轮询结果
            task_id = result["output"]["task_id"]

            # 轮询任务状态
            import time
            for _ in range(30):  # 最多等待30秒
                time.sleep(1)

                status_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
                status_response = requests.get(status_url, headers=headers, timeout=10)
                status_result = status_response.json()

                if status_result["output"]["task_status"] == "SUCCEEDED":
                    image_url = status_result["output"]["results"][0]["url"]

                    # 下载图像
                    image_response = requests.get(image_url, timeout=30)
                    image_response.raise_for_status()

                    image_path = output_dir / f"{filename}.png"
                    with open(image_path, "wb") as f:
                        f.write(image_response.content)

                    return {
                        "title": title,
                        "prompt": prompt,
                        "model": "tongyi-wanxiang",
                        "image_file": str(image_path),
                        "url": image_url
                    }
                elif status_result["output"]["task_status"] == "FAILED":
                    return {
                        "title": title,
                        "prompt": prompt,
                        "model": "tongyi-wanxiang",
                        "error": "Task failed"
                    }

            return {
                "title": title,
                "prompt": prompt,
                "model": "tongyi-wanxiang",
                "error": "Timeout waiting for image generation"
            }

        except Exception as e:
            return {
                "title": title,
                "prompt": prompt,
                "model": "tongyi-wanxiang",
                "error": str(e)
            }

    def _generate_stable_diffusion(
        self,
        prompt: str,
        output_dir: Path,
        filename: str,
        title: str
    ) -> Optional[Dict[str, Any]]:
        """使用 Stable Diffusion API 生成图像"""

        # 支持多个 SD API 端点
        api_url = os.getenv("SD_API_URL", "http://localhost:7860")

        try:
            url = f"{api_url}/sdapi/v1/txt2img"
            data = {
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, distorted, ugly",
                "steps": 30,
                "width": 1024,
                "height": 1024,
                "cfg_scale": 7,
                "sampler_name": "DPM++ 2M Karras"
            }

            response = requests.post(url, json=data, timeout=120)
            response.raise_for_status()

            result = response.json()

            # SD API 返回 base64 编码的图像
            image_data = base64.b64decode(result["images"][0])

            image_path = output_dir / f"{filename}.png"
            with open(image_path, "wb") as f:
                f.write(image_data)

            return {
                "title": title,
                "prompt": prompt,
                "model": "stable-diffusion",
                "image_file": str(image_path)
            }

        except Exception as e:
            return {
                "title": title,
                "prompt": prompt,
                "model": "stable-diffusion",
                "error": str(e)
            }

    def _generate_image_index(self, images: List[Dict[str, Any]]) -> str:
        """生成图像索引文档"""

        index = "# Generated AI Images\n\n"
        index += f"Total images: {len(images)}\n\n"
        index += "---\n\n"

        for i, image in enumerate(images, 1):
            index += f"## {i}. {image.get('title', 'Untitled')}\n\n"

            if image.get('image_file'):
                index += f"![{image['title']}]({image['image_file']})\n\n"

            index += f"**Model**: {image.get('model', 'unknown')}\n\n"
            index += f"**Prompt**: {image.get('prompt', 'N/A')}\n\n"

            if image.get('error'):
                index += f"**Error**: {image['error']}\n\n"

            if image.get('url'):
                index += f"**Original URL**: {image['url']}\n\n"

            index += "---\n\n"

        return index


# 注册技能
SKILL_META = SkillMeta(
    name="ai_image_generator",
    description="Generate AI images for academic papers using DALL-E 3, Tongyi Wanxiang, or Stable Diffusion",
    inputs_required=[],
    outputs_produced=["generated_ai_images"]
)
