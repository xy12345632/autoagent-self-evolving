"""翻译工具"""

import httpx
from typing import Dict, Any, Optional

TOOL_SCHEMA = {
    "name": "translate",
    "description": "翻译文本到指定语言",
    "category": "utility",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要翻译的文本"
            },
            "target_lang": {
                "type": "string",
                "description": "目标语言代码，如 'en', 'zh', 'ja', 'ko', 'fr', 'de'",
                "default": "en"
            },
            "source_lang": {
                "type": "string",
                "description": "源语言代码，'auto' 表示自动检测",
                "default": "auto"
            }
        },
        "required": ["text"]
    }
}

async def translate(text: str, target_lang: str = "en", source_lang: str = "auto") -> Dict[str, Any]:
    """
    翻译文本

    Args:
        text: 要翻译的文本
        target_lang: 目标语言
        source_lang: 源语言

    Returns:
        翻译结果
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mymemory.translated.net/get",
                params={
                    "q": text,
                    "langpair": f"{source_lang}|{target_lang}"
                },
                timeout=10.0
            )
            data = response.json()

            if data.get("responseStatus") == 200:
                return {
                    "success": True,
                    "translated_text": data["responseData"]["translatedText"],
                    "source_lang": data.get("sourceLang", source_lang),
                    "target_lang": target_lang
                }
            else:
                return {
                    "success": False,
                    "error": data.get("responseDetails", "Translation failed")
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

translate._tool_metadata = TOOL_SCHEMA