"""
网页浏览工具 - 获取网页内容
"""

import httpx
from bs4 import BeautifulSoup
from typing import Optional


def browse(url: str, action: str = "get", element: str = None) -> dict:
    """
    浏览网页并获取内容

    Args:
        url: 目标URL
        action: 操作类型，"get"获取全文，"find"查找元素
        element: CSS选择器（当action为find时使用）

    Returns:
        dict: 包含success状态和content或error信息
    """
    if not url or not url.strip():
        return {"success": False, "error": "URL不能为空"}

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        if action == "find" and element:
            elements = soup.select(element)
            if not elements:
                return {"success": False, "error": f"未找到匹配的元素: {element}"}

            results = []
            for elem in elements[:10]:
                results.append({
                    "tag": elem.name,
                    "text": elem.get_text(strip=True)[:500],
                    "html": str(elem)[:1000]
                })

            return {
                "success": True,
                "url": url,
                "action": action,
                "selector": element,
                "count": len(results),
                "elements": results
            }

        text = soup.get_text(separator="\n", strip=True)
        lines = [line for line in text.split("\n") if line.strip()]
        content = "\n".join(lines)

        return {
            "success": True,
            "url": url,
            "action": action,
            "content": content[:10000],
            "raw_content": response.text[:5000]
        }

    except httpx.TimeoutException:
        return {"success": False, "error": "请求超时"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP错误: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"浏览失败: {str(e)}"}
