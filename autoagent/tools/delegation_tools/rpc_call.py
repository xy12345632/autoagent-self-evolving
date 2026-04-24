"""
RPC调用工具 - 发起RPC请求到其他服务或组件
"""

import os
import uuid
import json
import time
import httpx
from typing import Optional, Dict, Any
from datetime import datetime


_RPC_REGISTRY = {}


def register_service(name: str, endpoint: str, methods: list = None):
    """
    注册一个可用的RPC服务

    参数:
        name: 服务名称
        endpoint: 服务端点URL
        methods: 支持的方法列表
    """
    _RPC_REGISTRY[name] = {
        "name": name,
        "endpoint": endpoint,
        "methods": methods or ["call"],
        "registered_at": datetime.now().isoformat()
    }


def make_rpc_call(method: str, params: dict = None) -> dict:
    """
    发起RPC调用

    参数:
        method: RPC方法名，格式: "service.method" 或 "method"
        params: 方法参数

    返回:
        RPC调用结果
    """
    if not method:
        return {"success": False, "error": "方法名不能为空"}

    if "." in method:
        service_name, method_name = method.split(".", 1)
    else:
        method_name = method
        service_name = None

    params = params or {}

    if service_name and service_name not in _RPC_REGISTRY:
        return {
            "success": False,
            "error": f"服务未注册: {service_name}"
        }

    call_id = str(uuid.uuid4())[:8]

    start_time = time.time()

    try:
        if service_name:
            endpoint = _RPC_REGISTRY[service_name]["endpoint"]
            full_url = f"{endpoint.rstrip('/')}/{method_name}"
        else:
            full_url = method_name

        timeout = params.pop("_timeout", 30)
        headers = params.pop("_headers", {})

        if full_url.startswith("http://") or full_url.startswith("https://"):
            result = _http_rpc_call(full_url, params, timeout, headers)
        else:
            result = _internal_rpc_call(service_name, method_name, params)

        elapsed = time.time() - start_time

        return {
            "success": True,
            "call_id": call_id,
            "method": method,
            "result": result,
            "elapsed_time": round(elapsed, 3)
        }

    except Exception as e:
        elapsed = time.time() - start_time

        return {
            "success": False,
            "call_id": call_id,
            "method": method,
            "error": str(e),
            "elapsed_time": round(elapsed, 3)
        }


def _http_rpc_call(url: str, params: dict, timeout: int, headers: dict) -> Any:
    """通过HTTP发起RPC调用"""
    try:
        import httpx

        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                url,
                json=params,
                headers={
                    "Content-Type": "application/json",
                    **headers
                }
            )

            response.raise_for_status()

            return response.json()

    except httpx.TimeoutException:
        raise Exception(f"RPC调用超时: {url}")
    except httpx.HTTPStatusError as e:
        raise Exception(f"HTTP错误: {e.response.status_code}")
    except Exception as e:
        raise Exception(f"HTTP请求失败: {str(e)}")


def _internal_rpc_call(service_name: str, method_name: str, params: dict) -> Any:
    """内部RPC调用"""
    if service_name not in _RPC_REGISTRY:
        raise Exception(f"服务未注册: {service_name}")

    raise Exception(f"内部方法未实现: {service_name}.{method_name}")


def list_registered_services() -> dict:
    """
    列出所有已注册的服务

    返回:
        服务列表字典
    """
    services = []

    for name, info in _RPC_REGISTRY.items():
        services.append({
            "name": info.get("name"),
            "endpoint": info.get("endpoint"),
            "methods": info.get("methods"),
            "registered_at": info.get("registered_at")
        })

    return {
        "success": True,
        "services": services,
        "total": len(services)
    }


def batch_rpc_call(calls: list) -> dict:
    """
    批量发起RPC调用

    参数:
        calls: 调用列表，每项包含 method 和 params

    返回:
        批量调用结果
    """
    results = []

    for call in calls:
        method = call.get("method")
        params = call.get("params")

        if not method:
            results.append({
                "success": False,
                "error": "方法名不能为空"
            })
            continue

        result = make_rpc_call(method, params)
        results.append(result)

    success_count = len([r for r in results if r.get("success")])

    return {
        "success": True,
        "results": results,
        "total": len(calls),
        "success_count": success_count,
        "failed_count": len(calls) - success_count
    }
