import os
from typing import Any, Optional


class SecretsManager:
    _secrets: dict[str, Any] = {}

    def load_secrets(self, config: dict[str, Any]) -> None:
        self._secrets = {}
        env_mapping = {
            "opencode_zen_api_key": "OPENCODE_ZEN_API_KEY",
            "openrouter_api_key": "OPENROUTER_API_KEY",
        }

        for config_key, env_var in env_mapping.items():
            env_value = os.environ.get(env_var)
            if env_value:
                self._secrets[config_key] = env_value
            elif config_key in config:
                self._secrets[config_key] = config[config_key]

        bot_token_keys = [
            "gateway.telegram.bot_token",
            "gateway.discord.bot_token",
            "gateway.slack.bot_token",
        ]
        for token_key in bot_token_keys:
            parts = token_key.split(".")
            value = config
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, "")
                else:
                    value = ""
                    break
            env_suffix = "_".join(parts[:-1]).upper() + "_BOT_TOKEN"
            env_value = os.environ.get(env_suffix)
            if env_value:
                self._secrets[token_key] = env_value

    def get_secret(self, key: str) -> Optional[str]:
        return self._secrets.get(key)

    def set_secret(self, key: str, value: str) -> None:
        self._secrets[key] = value
