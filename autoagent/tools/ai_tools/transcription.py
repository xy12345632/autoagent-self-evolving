"""
语音转文字工具 - 使用 OpenAI Whisper 或替代API
"""

import os
from typing import Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def transcribe(audio_path: str, language: str = None) -> dict:
    """
    将语音转换为文字

    参数:
        audio_path: 音频文件路径
        language: 音频语言代码 (如 "zh", "en")，不指定则自动检测

    返回:
        包含转录文字的字典
    """
    if not audio_path:
        return {"success": False, "error": "音频路径不能为空"}

    if not os.path.exists(audio_path):
        return {"success": False, "error": f"音频文件不存在: {audio_path}"}

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

        with open(audio_path, "rb") as audio_file:
            kwargs = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": "verbose_json"
            }

            if language:
                kwargs["language"] = language

            response = client.audio.transcriptions.create(**kwargs)

        return {
            "success": True,
            "text": response.text,
            "language": getattr(response, "language", None),
            "duration": getattr(response, "duration", None),
            "audio_path": audio_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"语音转文字失败: {str(e)}"
        }


def transcribe_with_timestamps(audio_path: str, language: str = None) -> dict:
    """
    将语音转换为带时间戳的文字

    参数:
        audio_path: 音频文件路径
        language: 音频语言代码

    返回:
        包含分段转录结果的字典
    """
    if not audio_path:
        return {"success": False, "error": "音频路径不能为空"}

    if not os.path.exists(audio_path):
        return {"success": False, "error": f"音频文件不存在: {audio_path}"}

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

        with open(audio_path, "rb") as audio_file:
            kwargs = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": "verbose_json",
                "timestamp_granularities": ["word"]
            }

            if language:
                kwargs["language"] = language

            response = client.audio.transcriptions.create(**kwargs)

        segments = []
        if hasattr(response, "segments"):
            for seg in response.segments:
                segments.append({
                    "id": seg.get("id"),
                    "start": seg.get("start"),
                    "end": seg.get("end"),
                    "text": seg.get("text")
                })

        return {
            "success": True,
            "text": response.text,
            "language": getattr(response, "language", None),
            "duration": getattr(response, "duration", None),
            "segments": segments,
            "audio_path": audio_path
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"语音转文字失败: {str(e)}"
        }
