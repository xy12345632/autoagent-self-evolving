"""天气查询工具"""

import httpx
from typing import Dict, Any, Optional

TOOL_SCHEMA = {
    "name": "weather",
    "description": "查询指定城市的天气",
    "category": "information",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称或ID"
            },
            "units": {
                "type": "string",
                "description": "温度单位，'celsius' 或 'fahrenheit'",
                "default": "celsius"
            }
        },
        "required": ["city"]
    }
}

async def get_weather(city: str, units: str = "celsius") -> Dict[str, Any]:
    """
    获取天气信息

    注意：这是一个示例实现，使用免费的 wttr.in API
    """
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://wttr.in/{city}"
            params = {"format": "j1"}

            response = await client.get(url, params=params, timeout=10.0)
            data = response.json()

            current = data.get("current_condition", [{}])[0]

            temp_c = current.get("temp_C", "N/A")
            temp_f = current.get("temp_F", "N/A")

            weather_desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            humidity = current.get("humidity", "N/A")
            wind_speed = current.get("windspeedKmph", "N/A")

            return {
                "success": True,
                "city": city,
                "temperature_celsius": temp_c,
                "temperature_fahrenheit": temp_f,
                "description": weather_desc,
                "humidity": humidity,
                "wind_speed_kmh": wind_speed
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Weather query failed: {str(e)}"
        }

get_weather._tool_metadata = TOOL_SCHEMA