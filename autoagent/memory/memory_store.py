import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

from ..utils.logger import get_logger
from ..utils.paths import GlobalPaths
from .schemas import MemoryEntry, MemoryType

logger = get_logger("memory_store")


class MemoryStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = str(GlobalPaths.get_db_path())
        else:
            self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self) -> None:
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    importance INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_archived INTEGER DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)
            """)

            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    content,
                    content_rowid='id',
                    content='memories'
                )
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
                END
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.id, old.content);
                END
            """)

            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.id, old.content);
                    INSERT INTO memories_fts(rowid, content) VALUES (new.id, new.content);
                END
            """)

            logger.info("Memory database initialized")

    def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[dict[str, Any]] = None,
        importance: int = 5,
    ) -> int:
        now = datetime.now().isoformat()
        metadata_json = str(metadata) if metadata else "{}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memories (content, memory_type, metadata, importance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (content, memory_type.value, metadata_json, importance, now, now),
            )
            memory_id = cursor.lastrowid
            logger.debug(f"Stored memory with id: {memory_id}")
            return memory_id

    def search_memories(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        if not query.strip():
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT m.* FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE memories_fts MATCH ? AND m.is_archived = 0
                ORDER BY rank, m.importance DESC
                LIMIT ?
                """,
                (query, limit),
            )

            rows = cursor.fetchall()
            return [self._row_to_entry(row) for row in rows]

    def get_recent_memories(self, limit: int = 20) -> list[MemoryEntry]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM memories
                WHERE is_archived = 0
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [self._row_to_entry(row) for row in rows]

    def update_memory(self, memory_id: int, content: str) -> bool:
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE memories SET content = ?, updated_at = ? WHERE id = ?
                """,
                (content, now, memory_id),
            )
            return cursor.rowcount > 0

    def delete_memory(self, memory_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    def get_memory_by_id(self, memory_id: int) -> Optional[MemoryEntry]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_entry(row)
            return None

    def get_all_memories(self) -> list[MemoryEntry]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM memories
                WHERE is_archived = 0
                ORDER BY updated_at DESC
                """
            )
            rows = cursor.fetchall()
            return [self._row_to_entry(row) for row in rows]

    def get_memories_by_type(
        self, memory_type: MemoryType, limit: int = 50
    ) -> list[MemoryEntry]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM memories
                WHERE memory_type = ? AND is_archived = 0
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (memory_type.value, limit),
            )
            rows = cursor.fetchall()
            return [self._row_to_entry(row) for row in rows]

    def archive_memory(self, memory_id: int) -> bool:
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE memories SET is_archived = 1, updated_at = ? WHERE id = ?",
                (now, memory_id),
            )
            return cursor.rowcount > 0

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        import json

        metadata = {}
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                metadata = {}

        created_at = row["created_at"]
        updated_at = row["updated_at"]

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return MemoryEntry(
            id=row["id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            metadata=metadata,
            importance=row["importance"],
            created_at=created_at,
            updated_at=updated_at,
            is_archived=bool(row["is_archived"]),
        )

    def create_fts_index(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
            logger.info("FTS5 index rebuilt")

    def get_stats(self) -> dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as total FROM memories")
            total = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM memories WHERE is_archived = 0"
            )
            active = cursor.fetchone()["count"]

            cursor.execute(
                """
                SELECT memory_type, COUNT(*) as count
                FROM memories GROUP BY memory_type
                """
            )
            by_type = {row["memory_type"]: row["count"] for row in cursor.fetchall()}

            return {
                "total_memories": total,
                "active_memories": active,
                "archived_memories": total - active,
                "by_type": by_type,
            }
