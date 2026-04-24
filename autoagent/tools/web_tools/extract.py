"""
网页内容提取工具 - 使用CSS选择器提取特定内容
"""

import httpx
from bs4 import BeautifulSoup
from typing import Optional, List, Dict


def extract(url: str, selector: str = None) -> dict:
    """
    从网页中提取指定内容

    Args:
        url: 目标URL
        selector: CSS选择器，如 "article p", ".content img", "#title"

    Returns:
        dict: 包含success状态和extracted数据或error信息
    """
    if not url or not url.strip():
        return {"success": False, "error": "URL不能为空"}

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        if not selector:
            text = soup.get_text(separator="\n", strip=True)
            return {
                "success": True,
                "url": url,
                "content": text[:20000]
            }

        elements = soup.select(selector)

        if not elements:
            return {
                "success": False,
                "error": f"未找到匹配的元素: {selector}",
                "available_tags": list(set(tag.name for tag in soup.find_all(True)))[:20]
            }

        extracted = []
        for i, elem in enumerate(elements[:50]):
            item = {
                "index": i,
                "tag": elem.name,
                "text": elem.get_text(strip=True)[:2000] if elem.get_text() else None,
                "html": str(elem)[:2000],
            }

            if elem.name == "a":
                item["href"] = elem.get("href")
            elif elem.name == "img":
                item["src"] = elem.get("src")
                item["alt"] = elem.get("alt")
            elif elem.name == "input":
                item["type"] = elem.get("type")
                item["name"] = elem.get("name")
                item["value"] = elem.get("value")

            extracted.append(item)

        return {
            "success": True,
            "url": url,
            "selector": selector,
            "count": len(extracted),
            "extracted": extracted
        }

    except httpx.TimeoutException:
        return {"success": False, "error": "请求超时"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP错误: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"提取失败: {str(e)}"}
