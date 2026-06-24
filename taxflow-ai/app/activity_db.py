"""Activity feed database - tracks all user actions for the audit trail.

Stores activities like document uploads, processing results,
exports, and AI interactions in the main database.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Optional

from app.config import settings


def _get_db() -> sqlite3.Connection:
    """Get a connection to the main database."""
    db_path = settings.BASE_DIR / "taxflow.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_activity_db():
    """Initialize the activity tracking table."""
    conn = _get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                user_id TEXT,
                type TEXT NOT NULL DEFAULT 'info',
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                timestamp TEXT DEFAULT (datetime('now')),
                metadata TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_activities_project ON activities(project_id);
            CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp DESC);
        """)
        conn.commit()
    finally:
        conn.close()


def add_activity(project_id: str, activity_type: str, title: str,
                 description: str = "", metadata: dict = None,
                 user_id: str = "") -> str:
    """Add an activity record.

    Types: upload, process, extract, reconcile, export, chat,
           anomaly, project, auth, error, success, info
    """
    activity_id = str(uuid.uuid4())
    conn = _get_db()
    try:
        conn.execute(
            """INSERT INTO activities (id, project_id, user_id, type, title, description, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (activity_id, project_id or "", user_id, activity_type,
             title[:200], description[:500], json.dumps(metadata or {})),
        )
        conn.commit()
        return activity_id
    finally:
        conn.close()


def get_activities(project_id: Optional[str] = None, limit: int = 50,
                   offset: int = 0, activity_type: Optional[str] = None) -> list[dict]:
    """Get recent activities, optionally filtered by project or type."""
    conn = _get_db()
    try:
        where_clauses = []
        params = []

        if project_id:
            where_clauses.append("project_id = ?")
            params.append(project_id)
        if activity_type:
            where_clauses.append("type = ?")
            params.append(activity_type)

        where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        cursor = conn.execute(
            f"SELECT * FROM activities {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            try:
                d["metadata"] = json.loads(d.get("metadata", "{}"))
            except (json.JSONDecodeError, TypeError):
                d["metadata"] = {}
            results.append(d)
        return results
    finally:
        conn.close()


def get_recent_activities_summary(project_id: Optional[str] = None, hours: int = 24) -> dict:
    """Get a summary of recent activity counts."""
    conn = _get_db()
    try:
        if project_id:
            cursor = conn.execute(
                """SELECT type, COUNT(*) as count FROM activities
                   WHERE project_id = ? AND timestamp > datetime('now', ?)
                   GROUP BY type""",
                (project_id, f'-{hours} hours'),
            )
        else:
            cursor = conn.execute(
                """SELECT type, COUNT(*) as count FROM activities
                   WHERE timestamp > datetime('now', ?)
                   GROUP BY type""",
                (f'-{hours} hours',),
            )
        counts = {row["type"]: row["count"] for row in cursor.fetchall()}
        return {
            "total": sum(counts.values()),
            "by_type": counts,
            "period_hours": hours,
        }
    finally:
        conn.close()


def get_activity_timeline(project_id: str, days: int = 7) -> list[dict]:
    """Get activities grouped by day for timeline visualization."""
    conn = _get_db()
    try:
        cursor = conn.execute(
            """SELECT DATE(timestamp) as day, type, COUNT(*) as count
               FROM activities
               WHERE project_id = ? AND timestamp > datetime('now', ?)
               GROUP BY DATE(timestamp), type
               ORDER BY day DESC""",
            (project_id, f'-{days} days'),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def clear_activities(project_id: Optional[str] = None):
    """Clear activities for a project or all activities."""
    conn = _get_db()
    try:
        if project_id:
            conn.execute("DELETE FROM activities WHERE project_id = ?", (project_id,))
        else:
            conn.execute("DELETE FROM activities")
        conn.commit()
    finally:
        conn.close()
