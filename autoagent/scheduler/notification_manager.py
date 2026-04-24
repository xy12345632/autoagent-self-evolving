from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class NotificationPlatform(Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    WEBHOOK = "webhook"


class NotificationManager:
    def __init__(self):
        self._platforms: Dict[str, Any] = {}
        self._notification_history: List[Dict[str, Any]] = []
        self._webhook_urls: Dict[str, str] = {}

    def register_platform(self, platform: str, handler: Any):
        self._platforms[platform] = handler
        logger.info(f"Platform registered: {platform}")

    def register_webhook(self, name: str, url: str):
        self._webhook_urls[name] = url
        logger.info(f"Webhook registered: {name}")

    async def send_notification(
        self,
        platform: str,
        message: str,
        recipient: Optional[str] = None,
        **kwargs
    ) -> bool:
        try:
            notification = {
                "platform": platform,
                "message": message,
                "recipient": recipient,
                "timestamp": datetime.now().isoformat(),
                "status": "pending"
            }

            logger.info(f"Sending notification via {platform}: {message[:50]}...")

            if platform == NotificationPlatform.WEBHOOK.value:
                return await self._send_webhook(recipient or "default", message, **kwargs)

            handler = self._platforms.get(platform)
            if not handler:
                logger.error(f"Platform handler not found: {platform}")
                return False

            if hasattr(handler, "send_message"):
                result = await handler.send_message(recipient or "", message)
            elif hasattr(handler, "send"):
                result = await handler.send(message, recipient=recipient, **kwargs)
            else:
                logger.error(f"Handler does not support sending: {platform}")
                return False

            notification["status"] = "sent" if result else "failed"
            self._notification_history.append(notification)
            return result

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            notification["status"] = "error"
            notification["error"] = str(e)
            self._notification_history.append(notification)
            return False

    async def _send_webhook(
        self,
        webhook_name: str,
        message: str,
        **kwargs
    ) -> bool:
        import aiohttp

        url = self._webhook_urls.get(webhook_name)
        if not url:
            logger.error(f"Webhook URL not found: {webhook_name}")
            return False

        payload = {
            "content": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Webhook request failed: {e}")
            return False

    async def send_result(
        self,
        task_id: str,
        result: Any,
        platform: Optional[str] = None,
        **kwargs
    ) -> bool:
        result_str = self._format_result(result)

        status_emoji = "✅"
        status_text = "成功"

        message = (
            f"{status_emoji} **任务完成**\n\n"
            f"**任务ID**: `{task_id}`\n"
            f"**状态**: {status_text}\n"
            f"**结果**: {result_str}\n"
            f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if platform:
            return await self.send_notification(platform, message, **kwargs)

        success = True
        for p in self._platforms.keys():
            if not await self.send_notification(p, message, **kwargs):
                success = False
        return success

    async def send_error(
        self,
        task_id: str,
        error: Exception,
        platform: Optional[str] = None,
        **kwargs
    ) -> bool:
        error_message = str(error)
        error_type = type(error).__name__

        message = (
            f"❌ **任务失败**\n\n"
            f"**任务ID**: `{task_id}`\n"
            f"**错误类型**: {error_type}\n"
            f"**错误信息**: {error_message}\n"
            f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if platform:
            return await self.send_notification(platform, message, **kwargs)

        success = True
        for p in self._platforms.keys():
            if not await self.send_notification(p, message, **kwargs):
                success = False
        return success

    def _format_result(self, result: Any) -> str:
        if result is None:
            return "无"
        if isinstance(result, (str, int, float, bool)):
            return str(result)[:200]
        if isinstance(result, dict):
            try:
                return json.dumps(result, ensure_ascii=False, indent=2)[:500]
            except:
                return str(result)[:200]
        if isinstance(result, (list, tuple)):
            return f"列表 ({len(result)} 项)"
        return str(result)[:200]

    def get_notification_history(
        self,
        limit: int = 100,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        history = self._notification_history
        if platform:
            history = [n for n in history if n.get("platform") == platform]
        return history[-limit:]

    def clear_history(self):
        self._notification_history.clear()
        logger.info("Notification history cleared")
