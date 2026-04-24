"""新闻获取工具"""

import httpx
from typing import Dict, Any, Optional, List

TOOL_SCHEMA = {
    "name": "news",
    "description": "获取最新新闻",
    "category": "information",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "新闻主题，如 'technology', 'sports', 'business'",
                "default": "general"
            },
            "country": {
                "type": "string",
                "description": "国家代码，如 'us', 'cn', 'jp'",
                "default": "us"
            },
            "limit": {
                "type": "integer",
                "description": "返回新闻数量",
                "default": 5
            }
        }
    }
}

async def get_news(topic: str = "general", country: str = "us", limit: int = 5) -> Dict[str, Any]:
    """
    获取最新新闻
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://newsapi.org/v2/top-headlines",
                params={
                    "category": topic,
                    "country": country,
                    "pageSize": limit,
                    "apiKey": "demo"
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])

                return {
                    "success": True,
                    "topic": topic,
                    "count": len(articles),
                    "articles": [
                        {
                            "title": a.get("title", ""),
                            "description": a.get("description", ""),
                            "url": a.get("url", ""),
                            "source": a.get("source", {}).get("name", "")
                        }
                        for a in articles[:limit]
                    ]
                }
            else:
                return {
                    "success": False,
                    "error": f"News API error: {response.status_code}"
                }
    except Exception as e:
        return {
            "success": False,
            "error": f"News fetch failed: {str(e)}"
        }

get_news._tool_metadata = TOOL_SCHEMA