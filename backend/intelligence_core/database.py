"""SQLite database layer for the Intelligence Core.

Provides a small connection pool backed by :class:`queue.Queue`, thread-local
statement execution, automatic table creation, and parameterized queries for
all operations.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

logger = logging.getLogger(__name__)

# SQL to bootstrap the intelligence core schema on first run.
_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    data_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id TEXT NOT NULL,
    from_type TEXT NOT NULL,
    to_id TEXT NOT NULL,
    to_type TEXT NOT NULL,
    relationship TEXT NOT NULL,
    strength_score REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_type, from_id);
CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_type, to_id);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    source TEXT NOT NULL,
    payload_json TEXT,
    priority TEXT DEFAULT 'normal',
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);

CREATE TABLE IF NOT EXISTS context_sessions (
    session_id TEXT NOT NULL,
    module TEXT NOT NULL,
    context_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, module)
);

CREATE INDEX IF NOT EXISTS idx_context_sessions_session ON context_sessions(session_id);

CREATE TABLE IF NOT EXISTS actions (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    entity_id TEXT,
    entity_type TEXT,
    title TEXT NOT NULL,
    description TEXT,
    why_matters TEXT,
    expected_outcome TEXT,
    source_modules_json TEXT,
    related_entities_json TEXT,
    urgency INTEGER DEFAULT 5,
    effort INTEGER DEFAULT 5,
    impact_score INTEGER DEFAULT 5,
    priority_score REAL DEFAULT 5.0,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result_json TEXT,
    executed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_actions_entity ON actions(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status);

CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    trigger_event_id TEXT,
    result_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
"""


@dataclass
class SQLiteConnectionPool:
    """A tiny thread-safe SQLite connection pool.

    Connections are created lazily up to ``max_size`` and returned to the pool
    after use.  Each connection is associated with the thread that checked it
    out, ensuring that the same ``sqlite3.Connection`` is never used by two
    threads concurrently.
    """

    db_path: str
    max_size: int = 10
    timeout: float = 30.0

    def __post_init__(self) -> None:
        self._pool: queue.Queue[sqlite3.Connection] = queue.Queue(maxsize=self.max_size)
        self._lock = threading.Lock()
        self._created = 0
        self._ensure_dir()
        self._bootstrap()

    def _ensure_dir(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.db_path))
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"created_intelligence_db_directory directory={directory}")

    def _create_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.timeout,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _bootstrap(self) -> None:
        with self.acquire() as conn:
            conn.executescript(_CREATE_TABLES_SQL)
            conn.commit()
        logger.info(f"intelligence_database_initialized db_path={self.db_path}")

    @contextmanager
    def acquire(self) -> Iterator[sqlite3.Connection]:
        """Acquire a connection from the pool."""
        conn: sqlite3.Connection | None = None
        try:
            try:
                conn = self._pool.get_nowait()
            except queue.Empty:
                with self._lock:
                    if self._created < self.max_size:
                        conn = self._create_connection()
                        self._created += 1
                    else:
                        conn = self._pool.get(timeout=self.timeout)
            yield conn
        finally:
            if conn is not None:
                self._pool.put(conn)

    def execute(
        self,
        sql: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> sqlite3.Cursor:
        """Execute a parameterized query and return the cursor."""
        with self.acquire() as conn:
            logger.debug(f"intelligence_db_execute sql={sql.strip().splitlines()[0]}")
            cursor = conn.execute(sql, parameters or ())
            conn.commit()
            return cursor

    def executescript(self, sql: str) -> sqlite3.Cursor:
        """Execute a SQL script."""
        with self.acquire() as conn:
            logger.debug("intelligence_db_executescript")
            cursor = conn.executescript(sql)
            conn.commit()
            return cursor

    def fetchone(
        self,
        sql: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch a single row as a dictionary."""
        with self.acquire() as conn:
            logger.debug(f"intelligence_db_fetchone sql={sql.strip().splitlines()[0]}")
            cursor = conn.execute(sql, parameters or ())
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetchall(
        self,
        sql: str,
        parameters: tuple[Any, ...] | dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all rows as dictionaries."""
        with self.acquire() as conn:
            logger.debug(f"intelligence_db_fetchall sql={sql.strip().splitlines()[0]}")
            cursor = conn.execute(sql, parameters or ())
            return [dict(row) for row in cursor.fetchall()]

    def close_all(self) -> None:
        """Close all pooled connections."""
        with self._lock:
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
            self._created = 0


def serialize_json(data: Any) -> str:
    """Serialize a value to JSON, handling datetimes and other objects."""
    return json.dumps(data, default=str)


def deserialize_json(text: str | None, default: Any = None) -> Any:
    """Deserialize JSON text, returning ``default`` for empty/missing values."""
    if text is None or text == "":
        return default
    return json.loads(text)
