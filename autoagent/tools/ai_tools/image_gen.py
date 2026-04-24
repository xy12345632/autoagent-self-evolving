"""
图像生成工具 - 使用 DALL-E 或替代API生成图像
"""

import os
import uuid
import base64
from typing import Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def generate_image(prompt: str, size: str = "1024x1024", model: str = "dalle-3") -> dict:
    """
    使用AI生成图像

    参数:
        prompt: 图像描述提示词
        size: 图像尺寸，支持 "256x256", "512x512", "1024x1024" (DALL-E 3)
        model: 图像生成模型，默认 "dalle-3"

    返回:
        包含生成结果的字典，包含 image_path 或 image_data
    """
    if not prompt or not prompt.strip():
        return {"success": False, "error": "Prompt不能为空"}

    valid_sizes = ["256x256", "512x512", "1024x1024"]
    if size not in valid_sizes:
        size = "1024x1024"

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "success": False,
            "error": "未配置OPENAI_API_KEY环境变量"
        }

    try:
        if not OPENAI_AVAILABLE:
            return {"success": False, "error": "OpenAI库未安装，请运行: pip install openai"}

        client = OpenAI(api_key=api_key)

        response = client.images.generate(
            model="dall-e-3" if model == "dalle-3" else model,
            prompt=prompt,
            size=size,
            quality="standard" if model == "dalle-3" else "standard",
            n=1,
        )

        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt

        return {
            "success": True,
            "image_url": image_url,
            "revised_prompt": revised_prompt,
            "model": model,
            "size": size
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"图像生成失败: {str(e)}"
        }


def generate_image_to_file(prompt: str, output_path: str = None, size: str = "1024x1024") -> dict:
    """
    生成图像并保存到文件

    参数:
        prompt: 图像描述提示词
        output_path: 输出文件路径，默认在当前目录生成唯一文件名
        size: 图像尺寸

    返回:
        包含文件路径的字典
    """
    result = generate_image(prompt, size)

    if not result.get("success"):
        return result

    try:
        import requests

        image_url = result["image_url"]
        response = requests.get(image_url)

        if response.status_code == 200:
            if output_path is None:
                output_path = f"./generated_image_{uuid.uuid4().hex[:8]}.png"

            with open(output_path, "wb") as f:
                f.write(response.content)

            result["image_path"] = output_path
            result.pop("image_url", None)
            return result
        else:
            return {
                "success": False,
                "error": f"下载图像失败: HTTP {response.status_code}"
            }

    except ImportError:
        return {
            "success": False,
            "error": "需要requests库来下载图像，请运行: pip install requests",
            "image_url": result.get("image_url")
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"保存图像失败: {str(e)}"
        }
