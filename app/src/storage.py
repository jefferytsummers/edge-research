"""
SQLite storage adapter for Newport Demo application.

Provides persistence for feeds, protocols, and alerts.
"""
import asyncio
import json
import logging
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import (
    Alert,
    AlertLevel,
    ProtocolRules,
    Severity,
    StreamConfig,
)

logger = logging.getLogger(__name__)

# Database schema version for migrations
SCHEMA_VERSION = 1

# Default database path
DEFAULT_DB_PATH = "/app/data/config.db"


class StorageAdapter:
    """SQLite storage adapter for application data."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize storage adapter.

        Args:
            db_path: Path to SQLite database file. Defaults to /app/data/config.db
        """
        self.db_path = db_path or os.environ.get("DB_PATH", DEFAULT_DB_PATH)
        self._ensure_db_dir()
        self._init_schema()

    def _ensure_db_dir(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
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

    def _init_schema(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Schema version table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            """)

            # Check current schema version
            cursor.execute("SELECT MAX(version) FROM schema_version")
            current_version = cursor.fetchone()[0] or 0

            if current_version < SCHEMA_VERSION:
                self._apply_migrations(cursor, current_version)

    def _apply_migrations(self, cursor: sqlite3.Cursor, from_version: int):
        """Apply schema migrations."""
        logger.info(f"Migrating database from version {from_version} to {SCHEMA_VERSION}")

        if from_version < 1:
            # Initial schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feeds (
                    stream_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_uri TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    protocols_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS protocols (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    green_rules TEXT NOT NULL,
                    yellow_rules TEXT NOT NULL,
                    red_rules TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    stream_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    acknowledged INTEGER NOT NULL DEFAULT 0,
                    resolved_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_stream ON alerts(stream_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged)
            """)

            cursor.execute("""
                INSERT INTO schema_version (version, applied_at) VALUES (1, ?)
            """, (datetime.utcnow().isoformat(),))

            # Insert default protocols
            cursor.execute("""
                INSERT OR IGNORE INTO protocols (id, green_rules, yellow_rules, red_rules, updated_at)
                VALUES (1, ?, ?, ?, ?)
            """, (
                "Reading, watching TV, sleeping normally in bed, eating meals, sitting calmly, exercising normally",
                "Out of camera view, crouching in corners, minor injuries, pacing erratically, signs of distress",
                "Unconscious on ground, severe injury, room is empty/resident has left, self-harm behavior, medical emergency",
                datetime.utcnow().isoformat(),
            ))

        logger.info(f"Database migrated to version {SCHEMA_VERSION}")

    # Feed operations

    def get_feeds(self) -> List[StreamConfig]:
        """Get all configured feeds."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT stream_id, name, source_uri, enabled, protocols_json
                FROM feeds ORDER BY created_at
            """)
            rows = cursor.fetchall()

        feeds = []
        for row in rows:
            protocols = None
            if row["protocols_json"]:
                protocols_data = json.loads(row["protocols_json"])
                protocols = ProtocolRules(**protocols_data)

            feeds.append(StreamConfig(
                stream_id=row["stream_id"],
                name=row["name"],
                source_uri=row["source_uri"],
                enabled=bool(row["enabled"]),
                protocols=protocols,
            ))

        return feeds

    def get_feed(self, stream_id: str) -> Optional[StreamConfig]:
        """Get a single feed by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT stream_id, name, source_uri, enabled, protocols_json
                FROM feeds WHERE stream_id = ?
            """, (stream_id,))
            row = cursor.fetchone()

        if not row:
            return None

        protocols = None
        if row["protocols_json"]:
            protocols_data = json.loads(row["protocols_json"])
            protocols = ProtocolRules(**protocols_data)

        return StreamConfig(
            stream_id=row["stream_id"],
            name=row["name"],
            source_uri=row["source_uri"],
            enabled=bool(row["enabled"]),
            protocols=protocols,
        )

    def add_feed(self, name: str, source_uri: str, protocols: Optional[ProtocolRules] = None) -> StreamConfig:
        """Add a new feed."""
        stream_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        protocols_json = json.dumps(protocols.model_dump()) if protocols else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feeds (stream_id, name, source_uri, enabled, protocols_json, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?, ?)
            """, (stream_id, name, source_uri, protocols_json, now, now))

        return StreamConfig(
            stream_id=stream_id,
            name=name,
            source_uri=source_uri,
            enabled=True,
            protocols=protocols,
        )

    def update_feed(self, stream_id: str, **updates) -> Optional[StreamConfig]:
        """Update a feed."""
        feed = self.get_feed(stream_id)
        if not feed:
            return None

        # Build update query
        set_clauses = []
        params = []

        if "name" in updates:
            set_clauses.append("name = ?")
            params.append(updates["name"])

        if "source_uri" in updates:
            set_clauses.append("source_uri = ?")
            params.append(updates["source_uri"])

        if "enabled" in updates:
            set_clauses.append("enabled = ?")
            params.append(1 if updates["enabled"] else 0)

        if "protocols" in updates:
            protocols = updates["protocols"]
            protocols_json = json.dumps(protocols.model_dump()) if protocols else None
            set_clauses.append("protocols_json = ?")
            params.append(protocols_json)

        if set_clauses:
            set_clauses.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(stream_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE feeds SET {', '.join(set_clauses)} WHERE stream_id = ?
                """, params)

        return self.get_feed(stream_id)

    def delete_feed(self, stream_id: str) -> bool:
        """Delete a feed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feeds WHERE stream_id = ?", (stream_id,))
            return cursor.rowcount > 0

    # Protocol operations

    def get_protocols(self) -> ProtocolRules:
        """Get current protocol rules."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT green_rules, yellow_rules, red_rules FROM protocols WHERE id = 1
            """)
            row = cursor.fetchone()

        if row:
            return ProtocolRules(
                green_rules=row["green_rules"],
                yellow_rules=row["yellow_rules"],
                red_rules=row["red_rules"],
            )

        # Return defaults if not found
        return ProtocolRules(
            green_rules="Reading, watching TV, sleeping normally in bed, eating meals, sitting calmly, exercising normally",
            yellow_rules="Out of camera view, crouching in corners, minor injuries, pacing erratically, signs of distress",
            red_rules="Unconscious on ground, severe injury, room is empty/resident has left, self-harm behavior, medical emergency",
        )

    def save_protocols(self, protocols: ProtocolRules) -> ProtocolRules:
        """Save protocol rules."""
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO protocols (id, green_rules, yellow_rules, red_rules, updated_at)
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    green_rules = excluded.green_rules,
                    yellow_rules = excluded.yellow_rules,
                    red_rules = excluded.red_rules,
                    updated_at = excluded.updated_at
            """, (protocols.green_rules, protocols.yellow_rules, protocols.red_rules, now))

        return protocols

    # Alert operations

    def get_alerts(self, include_resolved: bool = False, limit: int = 100) -> List[Alert]:
        """Get alerts, optionally including resolved ones."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if include_resolved:
                cursor.execute("""
                    SELECT id, stream_id, level, title, message, severity, timestamp, acknowledged, resolved_at
                    FROM alerts ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT id, stream_id, level, title, message, severity, timestamp, acknowledged, resolved_at
                    FROM alerts WHERE resolved_at IS NULL ORDER BY timestamp DESC LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()

        alerts = []
        for row in rows:
            alerts.append(Alert(
                id=row["id"],
                stream_id=row["stream_id"],
                level=AlertLevel(row["level"]),
                title=row["title"],
                message=row["message"],
                severity=Severity(row["severity"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
                acknowledged=bool(row["acknowledged"]),
            ))

        return alerts

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get a single alert by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, stream_id, level, title, message, severity, timestamp, acknowledged, resolved_at
                FROM alerts WHERE id = ?
            """, (alert_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return Alert(
            id=row["id"],
            stream_id=row["stream_id"],
            level=AlertLevel(row["level"]),
            title=row["title"],
            message=row["message"],
            severity=Severity(row["severity"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            acknowledged=bool(row["acknowledged"]),
        )

    def create_alert(
        self,
        stream_id: str,
        level: AlertLevel,
        title: str,
        message: str,
        severity: Severity,
    ) -> Alert:
        """Create a new alert."""
        alert_id = str(uuid.uuid4())
        now = datetime.utcnow()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (id, stream_id, level, title, message, severity, timestamp, acknowledged, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (alert_id, stream_id, level.value, title, message, severity.value, now.isoformat(), now.isoformat()))

        return Alert(
            id=alert_id,
            stream_id=stream_id,
            level=level,
            title=title,
            message=message,
            severity=severity,
            timestamp=now,
            acknowledged=False,
        )

    def acknowledge_alert(self, alert_id: str) -> Optional[Alert]:
        """Acknowledge an alert."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alerts SET acknowledged = 1 WHERE id = ?
            """, (alert_id,))

            if cursor.rowcount == 0:
                return None

        return self.get_alert(alert_id)

    def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Resolve an alert."""
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alerts SET resolved_at = ? WHERE id = ?
            """, (now, alert_id))

            if cursor.rowcount == 0:
                return None

        return self.get_alert(alert_id)

    def get_unacknowledged_count(self) -> int:
        """Get count of unacknowledged alerts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM alerts WHERE acknowledged = 0 AND resolved_at IS NULL
            """)
            return cursor.fetchone()[0]


# Global storage instance
_storage: Optional[StorageAdapter] = None


def get_storage() -> StorageAdapter:
    """Get or create the global storage adapter."""
    global _storage
    if _storage is None:
        _storage = StorageAdapter()
    return _storage


def init_storage(db_path: Optional[str] = None) -> StorageAdapter:
    """Initialize storage with optional custom path."""
    global _storage
    _storage = StorageAdapter(db_path)
    return _storage
