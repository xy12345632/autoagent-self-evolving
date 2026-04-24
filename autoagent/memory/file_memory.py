import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..utils.logger import get_logger
from ..utils.paths import GlobalPaths

logger = get_logger("file_memory")


class MemoryFile:
    MEMORY_FILE = "MEMORY.md"
    USER_FILE = "USER.md"
    SOUL_FILE = "SOUL.md"

    def __init__(self, base_path: Optional[str] = None):
        if base_path is None:
            self.base_path = GlobalPaths.get_data_dir()
        else:
            self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self._memory_file = self.base_path / self.MEMORY_FILE
        self._user_file = self.base_path / self.USER_FILE
        self._soul_file = self.base_path / self.SOUL_FILE

    def _read_file(self, file_path: Path) -> str:
        if not file_path.exists():
            return ""
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return ""

    def _write_file(self, file_path: Path, content: str) -> bool:
        try:
            file_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")
            return False

    def read(self, file_type: str) -> str:
        file_map = {
            "memory": self._memory_file,
            "user": self._user_file,
            "soul": self._soul_file,
        }
        file_path = file_map.get(file_type.lower())
        if file_path is None:
            raise ValueError(f"Unknown file type: {file_type}")
        return self._read_file(file_path)

    def write(self, content: str, file_type: str) -> bool:
        file_map = {
            "memory": self._memory_file,
            "user": self._user_file,
            "soul": self._soul_file,
        }
        file_path = file_map.get(file_type.lower())
        if file_path is None:
            raise ValueError(f"Unknown file type: {file_type}")

        header = self._generate_header(file_type)
        return self._write_file(file_path, header + "\n\n" + content)

    def append(self, content: str, file_type: str) -> bool:
        existing = self.read(file_type)
        new_content = existing + "\n\n" + content if existing else content
        return self.write(new_content, file_type)

    def _generate_header(self, file_type: str) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        titles = {
            "memory": "# 记忆文件",
            "user": "# 用户信息",
            "soul": "# 灵魂配置",
        }
        return f"{titles.get(file_type, '# 文件')} | 最后更新: {now}"

    def get_all_memories(self) -> dict[str, str]:
        return {
            "memory": self.read("memory"),
            "user": self.read("user"),
            "soul": self.read("soul"),
        }

    def parse_memories(self, file_type: str) -> list[dict[str, str]]:
        content = self.read(file_type)
        if not content:
            return []

        memories = []
        blocks = re.split(r"\n(?=#+\s)", content)

        for block in blocks:
            block = block.strip()
            if not block or block.startswith("# "):
                continue

            lines = block.split("\n", 1)
            if len(lines) == 2:
                title, body = lines
                memories.append({
                    "title": title.strip("- ").strip(),
                    "content": body.strip(),
                })
            elif len(lines) == 1:
                memories.append({
                    "title": "",
                    "content": block.strip(),
                })

        return memories

    def file_exists(self, file_type: str) -> bool:
        file_map = {
            "memory": self._memory_file,
            "user": self._user_file,
            "soul": self._soul_file,
        }
        file_path = file_map.get(file_type.lower())
        return file_path.exists() if file_path else False

    def get_file_path(self, file_type: str) -> Optional[str]:
        file_map = {
            "memory": self._memory_file,
            "user": self._user_file,
            "soul": self._soul_file,
        }
        file_path = file_map.get(file_type.lower())
        return str(file_path) if file_path else None

    def backup(self, file_type: str) -> Optional[str]:
        content = self.read(file_type)
        if not content:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_type}_backup_{timestamp}.md"

        file_map = {
            "memory": self._memory_file,
            "user": self._user_file,
            "soul": self._soul_file,
        }
        file_path = file_map.get(file_type.lower())
        if file_path is None:
            return None

        backup_path = file_path.parent / backup_name
        try:
            backup_path.write_text(content, encoding="utf-8")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to backup {file_type}: {e}")
            return None
