import os
from typing import Any, Optional

import yaml

from ..utils.logger import get_logger
from ..utils.paths import GlobalPaths
from .secrets_manager import SecretsManager


logger = get_logger("config_manager")


class ConfigManager:
    _instance: Optional["ConfigManager"] = None
    _config: dict[str, Any] = {}

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._config:
            self._secrets_manager = SecretsManager()
            self.load_config()

    def load_config(self, config_path: Optional[str] = None) -> None:
        GlobalPaths.ensure_directories()

        if config_path is None:
            config_path_env = os.environ.get("AUTOAGENT_CONFIG_PATH")
            if config_path_env:
                config_path = config_path_env
            else:
                user_config_path = GlobalPaths.get_config_path()
                if user_config_path.exists():
                    config_path = str(user_config_path)
                else:
                    default_config = GlobalPaths.get_default_config_path()
                    if default_config.exists():
                        config_path = str(default_config)
                    else:
                        logger.warning("No config file found, using default configuration")
                        self._config = self._get_default_config()
                        self._secrets_manager.load_secrets(self._config)
                        return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using default configuration")
            self._config = self._get_default_config()
        except Exception as e:
            logger.warning(f"Error loading config: {e}, using default configuration")
            self._config = self._get_default_config()

        self._secrets_manager.load_secrets(self._config)

    def _get_default_config(self) -> dict[str, Any]:
        return {
            "model_providers": {
                "opencode_zen": {
                    "endpoint": "https://opencode.ai/zen/v1",
                    "default_model": "minimax-m2.5-free"
                },
                "openrouter": {
                    "endpoint": "https://openrouter.ai/api/v1",
                    "default_model": "openai/gpt-4o-mini"
                }
            },
            "memory": {
                "type": "sqlite_fts"
            },
            "skills": {
                "auto_create": True
            },
            "gateway": {
                "cli": {"enabled": True},
                "telegram": {"enabled": False},
                "discord": {"enabled": False},
                "slack": {"enabled": False},
                "whatsapp": {"enabled": False}
            },
            "tools": {
                "web_search": {"enabled": True, "provider": "duckduckgo"},
                "terminal": {"enabled": True},
                "code_execute": {"enabled": True}
            }
        }

    def get_api_key(self, provider: str) -> Optional[str]:
        api_key_map = {
            "opencode_zen": "opencode_zen_api_key",
            "openrouter": "openrouter_api_key",
        }
        key_name = api_key_map.get(provider)
        if key_name:
            return self._secrets_manager.get_secret(key_name)
        return None

    def get_config(self, section: str, key: Optional[str] = None) -> Any:
        if key is None:
            return self._config.get(section)
        return self._config.get(section, {}).get(key)

    def validate_config(self) -> tuple[bool, list[str]]:
        required_api_keys = ["opencode_zen_api_key", "openrouter_api_key"]
        required_sections = ["model_providers", "memory", "skills", "gateway", "tools"]

        errors = []

        for api_key in required_api_keys:
            if not self.get_api_key(api_key.replace("_api_key", "")):
                errors.append(f"Missing API key: {api_key}")

        for section in required_sections:
            if section not in self._config:
                errors.append(f"Missing required config section: {section}")

        return len(errors) == 0, errors

    @property
    def config(self) -> dict[str, Any]:
        return self._config
