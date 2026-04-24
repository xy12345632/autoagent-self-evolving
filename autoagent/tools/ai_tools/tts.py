"""
文本转语音工具 - 使用 OpenAI TTS 或替代API
"""

import os
import uuid
from typing import Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
DEFAULT_VOICE = "alloy"

SUPPORTED_MODELS = ["tts-1", "tts-1-hd"]
DEFAULT_MODEL = "tts-1"


def text_to_speech(text: str, voice: str = "alloy", output_path: str = None) -> dict:
    """
    将文本转换为语音

    参数:
        text: 要转换的文本内容
        voice: 语音风格，支持: alloy, echo, fable, onyx, nova, shimmer
        output_path: 输出文件路径，默认在当前目录生成唯一文件名

    返回:
        包含音频文件路径的字典
    """
    if not text or not text.strip():
        return {"success": False, "error": "文本内容不能为空"}

    if voice not in SUPPORTED_VOICES:
        voice = DEFAULT_VOICE

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

        response = client.audio.speech.create(
            model=DEFAULT_MODEL,
            voice=voice,
            input=text,
            response_format="mp3"
        )

        if output_path is None:
            output_path = f"./speech_{uuid.uuid4().hex[:8]}.mp3"

        response.stream_to_file(output_path)

        return {
            "success": True,
            "output_path": output_path,
            "voice": voice,
            "model": DEFAULT_MODEL,
            "text_length": len(text)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"语音合成失败: {str(e)}"
        }


def speech_to_file(text: str, output_path: str, voice: str = "alloy", model: str = "tts-1") -> dict:
    """
    将文本转换为语音并保存到指定文件

    参数:
        text: 要转换的文本内容
        output_path: 输出文件路径
        voice: 语音风格
        model: TTS模型

    返回:
        包含音频文件路径的字典
    """
    return text_to_speech(text, voice, output_path)
