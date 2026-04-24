"""
视觉分析工具 - 分析图像内容
"""

import os
from typing import Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def analyze_image(image_path: str, prompt: str = None) -> dict:
    """
    分析图像内容

    参数:
        image_path: 图像文件路径或URL
        prompt: 分析提示词，默认会进行通用分析

    返回:
        包含分析结果的字典
    """
    if not image_path:
        return {"success": False, "error": "图像路径不能为空"}

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

        if image_path.startswith(("http://", "https://")):
            image_url = image_path
            base64_image = None
        else:
            if not os.path.exists(image_path):
                return {"success": False, "error": f"图像文件不存在: {image_path}"}

            with open(image_path, "rb") as image_file:
                import base64
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            image_url = None

        if prompt is None:
            prompt = "请详细描述这张图像的内容，包括场景、物体、颜色、动作等细节。"

        if base64_image:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        else:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000
        )

        analysis = response.choices[0].message.content

        return {
            "success": True,
            "analysis": analysis,
            "model": "gpt-4o",
            "image_path": image_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"图像分析失败: {str(e)}"
        }


def extract_text_from_image(image_path: str) -> dict:
    """
    从图像中提取文字 (OCR功能)

    参数:
        image_path: 图像文件路径或URL

    返回:
        包含提取文字的字典
    """
    return analyze_image(image_path, "请提取图像中的所有文字内容。")
