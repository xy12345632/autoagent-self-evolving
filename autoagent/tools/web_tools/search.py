"""
网页搜索工具 - 使用DuckDuckGo进行搜索
"""

import httpx
from typing import Optional


def search(query: str, num_results: int = 10) -> dict:
    """
    使用DuckDuckGo进行网页搜索

    Args:
        query: 搜索关键词
        num_results: 返回结果数量，默认10

    Returns:
        dict: 包含success状态和results列表或error信息
    """
    if not query or not query.strip():
        return {"success": False, "error": "搜索关键词不能为空"}

    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=num_results)):
                if i >= num_results:
                    break
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }

    except ImportError:
        return _search_fallback(query, num_results)
    except Exception as e:
        return {"success": False, "error": f"搜索失败: {str(e)}"}


def _search_fallback(query: str, num_results: int) -> dict:
    """
    备用搜索方案 - 使用SerpAPI免费端点
    """
    try:
        url = "https://duckduckgo.com/html/"
        params = {"q": query}

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        for item in soup.select(".result")[:num_results]:
            title_elem = item.select_one(".result__title")
            snippet_elem = item.select_one(".result__snippet")
            if title_elem:
                link = title_elem.get("href", "")
                results.append({
                    "title": title_elem.get_text(strip=True),
                    "url": link,
                    "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                })

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        return {"success": False, "error": f"备用搜索也失败: {str(e)}"}
