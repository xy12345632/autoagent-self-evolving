import pytest
from unittest.mock import MagicMock, patch
import os
import yaml


class TestConfigManager:
    def test_singleton_pattern(self):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        mgr1 = ConfigManager()
        mgr2 = ConfigManager()
        assert mgr1 is mgr2

    def test_get_api_key_mapping(self):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        with patch.object(ConfigManager, 'load_config'):
            mgr = ConfigManager()
            with patch.object(mgr, '_secrets_manager') as mock_secrets:
                mock_secrets.get_secret.return_value = "test_key_123"
                key = mgr.get_api_key("opencode_zen")
                assert key == "test_key_123"

    def test_get_api_key_unknown_provider(self):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        with patch.object(ConfigManager, 'load_config'):
            mgr = ConfigManager()
            key = mgr.get_api_key("unknown_provider")
            assert key is None

    def test_get_config_section(self, mock_config):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = mock_config.copy()

        mgr = ConfigManager()
        mgr._config = mock_config

        result = mgr.get_config("model_providers")
        assert result == mock_config["model_providers"]

    def test_get_config_key(self, mock_config):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        mgr = ConfigManager()
        mgr._config = mock_config

        result = mgr.get_config("memory", "storage_path")
        assert result == "data/memory.json"

    def test_get_config_nonexistent(self, mock_config):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        mgr = ConfigManager()
        mgr._config = mock_config

        result = mgr.get_config("nonexistent_section")
        assert result is None

        result = mgr.get_config("memory", "nonexistent_key")
        assert result is None

    @patch('autoagent.config.config_manager.GlobalPaths.ensure_directories')
    @patch('autoagent.config.config_manager.GlobalPaths.get_config_path')
    @patch('autoagent.config.config_manager.GlobalPaths.get_default_config_path')
    @patch('autoagent.config.config_manager.open', create=True)
    @patch('autoagent.config.config_manager.yaml.safe_load')
    def test_load_config_default_path(self, mock_yaml, mock_open, mock_def_config, mock_user_config, mock_ensure):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        mock_def_config.return_value.exists.return_value = True
        mock_user_config.return_value.exists.return_value = False

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_yaml.return_value = {"test": "config"}

        mgr = ConfigManager()

        assert mock_open.call_count == 1

    @patch('autoagent.config.config_manager.SecretsManager')
    @patch('autoagent.config.config_manager.open', create=True)
    @patch('autoagent.config.config_manager.yaml.safe_load')
    def test_load_config_custom_path(self, mock_yaml, mock_open, mock_secrets_cls):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        mock_yaml.return_value = {"custom": "config"}

        mgr = ConfigManager()
        mgr.load_config("/custom/path/config.yaml")

        mock_open.assert_called_with("/custom/path/config.yaml", "r", encoding="utf-8")

    def test_validate_config_complete(self, mock_config):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        mgr = ConfigManager()
        mgr._config = mock_config

        with patch.object(mgr, 'get_api_key') as mock_get_key:
            mock_get_key.side_effect = ["key1", "key2"]
            valid, errors = mgr.validate_config()
            assert valid is True
            assert len(errors) == 0

    def test_validate_config_missing_api_keys(self, mock_config):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        mgr = ConfigManager()
        mgr._config = mock_config

        with patch.object(mgr, 'get_api_key') as mock_get_key:
            mock_get_key.return_value = None
            valid, errors = mgr.validate_config()
            assert valid is False
            assert len(errors) == 2
            assert any("API key" in e for e in errors)

    def test_validate_config_missing_sections(self, mock_config):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {"model_providers": {}}

        mgr = ConfigManager()
        mgr._config = {"model_providers": {}}

        with patch.object(mgr, 'get_api_key') as mock_get_key:
            mock_get_key.side_effect = ["key1", "key2"]
            valid, errors = mgr.validate_config()
            assert valid is False
            assert any("section" in e for e in errors)

    def test_config_property(self, mock_config):
        from autoagent.config.config_manager import ConfigManager
        ConfigManager._instance = None
        ConfigManager._config = {}

        mgr = ConfigManager()
        mgr._config = mock_config

        assert mgr.config == mock_config


class TestSecretsManager:
    def test_secrets_manager_init(self):
        from autoagent.config.secrets_manager import SecretsManager
        mgr = SecretsManager()
        assert mgr._secrets == {}

    def test_load_secrets(self):
        from autoagent.config.secrets_manager import SecretsManager
        mgr = SecretsManager()

        config = {
            "opencode_zen_api_key": "secret_key_123",
            "openrouter_api_key": "router_key_456"
        }
        mgr.load_secrets(config)

        assert mgr.get_secret("opencode_zen_api_key") == "secret_key_123"
        assert mgr.get_secret("openrouter_api_key") == "router_key_456"

    def test_get_secret_not_found(self):
        from autoagent.config.secrets_manager import SecretsManager
        mgr = SecretsManager()

        result = mgr.get_secret("nonexistent_key")
        assert result is None

    def test_set_secret(self):
        from autoagent.config.secrets_manager import SecretsManager
        mgr = SecretsManager()

        mgr.set_secret("new_key", "new_value")
        assert mgr.get_secret("new_key") == "new_value"
