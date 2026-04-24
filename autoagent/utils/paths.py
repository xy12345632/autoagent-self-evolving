import os
from pathlib import Path
from typing import Optional

import platformdirs


class GlobalPaths:
    APP_NAME = "autoagent"
    INSTANCE_ID = "default"

    @classmethod
    def get_data_dir(cls) -> Path:
        return Path(platformdirs.user_data_dir(cls.APP_NAME, cls.INSTANCE_ID))

    @classmethod
    def get_config_dir(cls) -> Path:
        return Path(platformdirs.user_config_dir(cls.APP_NAME, cls.INSTANCE_ID))

    @classmethod
    def get_cache_dir(cls) -> Path:
        return Path(platformdirs.user_cache_dir(cls.APP_NAME, cls.INSTANCE_ID))

    @classmethod
    def get_log_dir(cls) -> Path:
        return Path(platformdirs.user_log_dir(cls.APP_NAME, cls.INSTANCE_ID))

    @classmethod
    def get_state_dir(cls) -> Path:
        return Path(platformdirs.user_state_dir(cls.APP_NAME, cls.INSTANCE_ID))

    @classmethod
    def ensure_directories(cls) -> dict[str, Path]:
        dirs = {
            "data": cls.get_data_dir(),
            "config": cls.get_config_dir(),
            "cache": cls.get_cache_dir(),
            "log": cls.get_log_dir(),
            "state": cls.get_state_dir(),
        }
        for name, path in dirs.items():
            path.mkdir(parents=True, exist_ok=True)
        return dirs

    @classmethod
    def get_db_path(cls) -> Path:
        data_dir = cls.get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "memory.db"

    @classmethod
    def get_memory_file_path(cls, file_type: str) -> Path:
        data_dir = cls.get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        file_map = {
            "memory": "MEMORY.md",
            "user": "USER.md",
            "soul": "SOUL.md",
        }
        filename = file_map.get(file_type, f"{file_type}.md")
        return data_dir / filename

    @classmethod
    def get_config_path(cls) -> Path:
        config_dir = cls.get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yaml"

    @classmethod
    def get_secrets_path(cls) -> Path:
        config_dir = cls.get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "secrets.yaml"

    @classmethod
    def get_default_config_path(cls) -> Path:
        return Path(__file__).parent.parent / "config" / "config.yaml"

    @classmethod
    def migrate_data_if_needed(cls, source_path: Optional[Path] = None) -> bool:
        if source_path is None:
            source_path = Path(__file__).parent.parent / "data"

        migrated = False

        data_dir = cls.get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)

        if source_path.exists() and source_path.is_dir():
            for item in source_path.iterdir():
                dest = data_dir / item.name
                if not dest.exists():
                    dest.write_bytes(item.read_bytes())
                    migrated = True

        config_dir = cls.get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)

        default_config = cls.get_default_config_path()
        dest_config = cls.get_config_path()
        if default_config.exists() and not dest_config.exists():
            dest_config.write_bytes(default_config.read_bytes())
            migrated = True

        return migrated
