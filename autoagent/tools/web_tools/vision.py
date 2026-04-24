"""
视觉分析工具 - 分析网页截图
"""

import base64
import os
from typing import Optional


def analyze_screenshot(image_path: str) -> str:
    """
    分析网页截图，描述页面内容

    Args:
        image_path: 截图文件路径

    Returns:
        str: 截图内容描述
    """
    if not os.path.exists(image_path):
        return f"错误: 文件不存在 - {image_path}"

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()

        encoded = base64.b64encode(image_data).decode("utf-8")

        try:
            import anthropic
            client = anthropic.Anthropic()
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": encoded
                                }
                            },
                            {
                                "type": "text",
                                "text": "请详细描述这张截图的内容，包括页面布局、主要元素、文本内容等。"
                            }
                        ]
                    }
                ]
            )
            return response.content[0].text

        except ImportError:
            return _analyze_with_openai(encoded)
        except Exception as e:
            return f"分析失败: {str(e)}"

    except Exception as e:
        return f"读取图片失败: {str(e)}"


def _analyze_with_openai(encoded_data: str) -> str:
    """使用OpenAI Vision API分析截图"""
    try:
        from openai import OpenAI
        client = OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{encoded_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "请详细描述这张截图的内容。"
                        }
                    ]
                }
            ],
            max_tokens=1024
        )
        return response.choices[0].message.content

    except ImportError:
        return "错误: 需要安装 anthropic 或 openai 库来分析截图"
    except Exception as e:
        return f"OpenAI分析失败: {str(e)}"
