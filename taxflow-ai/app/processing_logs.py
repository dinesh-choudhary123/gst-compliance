"""Processing History and Logs Viewer for document processing operations.

Tracks all processing operations with timestamps, details,
and provides a searchable log viewer UI.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from app.database import _get_conn, _get_db_path
from app.config import settings


# ================================================================
# PROCESSING LOGS DATABASE
# ================================================================

def init_processing_logs_db():
    """Initialize the processing logs database table."""
    db_path = settings.BASE_DIR / "taxflow.db"
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS processing_logs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                filename TEXT DEFAULT '',
                details TEXT DEFAULT '',
                error_message TEXT DEFAULT '',
                duration_ms INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_logs_project ON processing_logs(project_id);
            CREATE INDEX IF NOT EXISTS idx_logs_created ON processing_logs(created_at DESC);
        """)
        conn.commit()
    finally:
        conn.close()


def add_processing_log(project_id: str, operation: str, status: str = "pending",
                       filename: str = "", details: str = "", duration_ms: int = 0) -> str:
    """Add a processing log entry."""
    import uuid, sqlite3
    log_id = str(uuid.uuid4())
    db_path = settings.BASE_DIR / "taxflow.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """INSERT INTO processing_logs (id, project_id, operation, status, filename, details, duration_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (log_id, project_id, operation, status, filename, details, duration_ms),
        )
        conn.commit()
        return log_id
    finally:
        conn.close()


def update_processing_log(log_id: str, status: str, error_message: str = "", duration_ms: int = 0):
    """Update a processing log entry."""
    import sqlite3
    db_path = settings.BASE_DIR / "taxflow.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """UPDATE processing_logs SET status = ?, error_message = ?, duration_ms = ?,
               completed_at = datetime('now') WHERE id = ?""",
            (status, error_message, duration_ms, log_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_processing_logs(project_id: Optional[str] = None, limit: int = 100,
                        offset: int = 0, operation: Optional[str] = None,
                        status: Optional[str] = None) -> list[dict]:
    """Get processing logs with optional filters."""
    import sqlite3
    db_path = settings.BASE_DIR / "taxflow.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        where_parts = []
        params = []

        if project_id:
            where_parts.append("project_id = ?")
            params.append(project_id)
        if operation:
            where_parts.append("operation = ?")
            params.append(operation)
        if status:
            where_parts.append("status = ?")
            params.append(status)

        where = "WHERE " + " AND ".join(where_parts) if where_parts else ""

        cursor = conn.execute(
            f"SELECT * FROM processing_logs {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_logs_summary(project_id: str) -> dict:
    """Get summary statistics of processing logs."""
    import sqlite3
    db_path = settings.BASE_DIR / "taxflow.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            """SELECT status, COUNT(*) as count FROM processing_logs
               WHERE project_id = ? GROUP BY status""",
            (project_id,),
        )
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        cursor = conn.execute(
            """SELECT operation, COUNT(*) as count, AVG(duration_ms) as avg_ms
               FROM processing_logs WHERE project_id = ?
               GROUP BY operation ORDER BY count DESC LIMIT 10""",
            (project_id,),
        )
        operation_stats = [dict(row) for row in cursor.fetchall()]

        cursor = conn.execute(
            """SELECT COUNT(*) as total FROM processing_logs WHERE project_id = ?""",
            (project_id,),
        )
        total = cursor.fetchone()["total"]

        return {
            "total_logs": total,
            "by_status": status_counts,
            "by_operation": operation_stats,
        }
    finally:
        conn.close()


# ================================================================
# LOGS VIEWER HTML
# ================================================================

def build_logs_viewer_html(project_id: str, limit: int = 50) -> str:
    """Build an HTML viewer for processing logs."""
    logs = get_processing_logs(project_id, limit=limit)
    summary = get_logs_summary(project_id)

    if not logs:
        return """
        <div style="text-align:center;padding:40px;color:#9CA3AF;">
            <div style="font-size:48px;margin-bottom:12px;">📋</div>
            <p>No processing history yet.<br>Upload and process documents to see logs here.</p>
        </div>"""

    status_icons = {
        "completed": "✅", "pending": "⏳", "processing": "🔄",
        "failed": "❌", "error": "❌", "warning": "⚠️",
    }
    status_colors = {
        "completed": "#059669", "pending": "#D97706", "processing": "#2E75B6",
        "failed": "#DC2626", "error": "#DC2626", "warning": "#D97706",
    }

    # Summary cards
    total = summary.get("total_logs", len(logs))
    status_counts = summary.get("by_status", {})
    success_rate = round((status_counts.get("completed", 0) / max(total, 1)) * 100, 1)

    avg_ms = 0
    if summary.get("by_operation"):
        avg_ms = sum(
            (s.get("avg_ms", 0) or 0) for s in summary["by_operation"]
        ) / max(len(summary["by_operation"]), 1)

    html = f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;">
        <div style="background:#F0F4F8;border-radius:6px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:#1F4E79;">{total}</div>
            <div style="font-size:10px;color:#6B7280;">Total Operations</div>
        </div>
        <div style="background:#F0F4F8;border-radius:6px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:#059669;">{success_rate}%</div>
            <div style="font-size:10px;color:#6B7280;">Success Rate</div>
        </div>
        <div style="background:#F0F4F8;border-radius:6px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:#2E75B6;">{avg_ms:.0f}ms</div>
            <div style="font-size:10px;color:#6B7280;">Avg Response Time</div>
        </div>
        <div style="background:#F0F4F8;border-radius:6px;padding:8px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:#D97706;">{status_counts.get('pending', 0)}</div>
            <div style="font-size:10px;color:#6B7280;">Pending</div>
        </div>
    </div>"""

    # Log entries
    html += '<div style="max-height:400px;overflow-y:auto;">'
    for log in logs:
        icon = status_icons.get(log.get("status", ""), "📄")
        color = status_colors.get(log.get("status", ""), "#6B7280")

        created = log.get("created_at", "")
        try:
            dt = datetime.fromisoformat(created)
            time_ago = "Just now"
            diff = datetime.now() - dt
            if diff < timedelta(minutes=1):
                time_ago = "Just now"
            elif diff < timedelta(hours=1):
                time_ago = f"{int(diff.total_seconds() / 60)}m ago"
            elif diff < timedelta(days=1):
                time_ago = f"{int(diff.total_seconds() / 3600)}h ago"
            else:
                time_ago = dt.strftime("%d %b %H:%M")
        except (ValueError, TypeError):
            time_ago = created[:16] if created else ""

        duration = log.get("duration_ms", 0)
        duration_str = f"{duration}ms" if duration else ""

        error = log.get("error_message", "")
        error_html = f'<div style="font-size:10px;color:#DC2626;margin-top:2px;">{error[:100]}</div>' if error else ""

        html += f"""
        <div style="display:flex;gap:8px;padding:8px 12px;background:white;border:1px solid #E2E8F0;border-radius:6px;margin-bottom:4px;transition:all 0.2s;">
            <div style="font-size:18px;">{icon}</div>
            <div style="flex:1;min-width:0;">
                <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                    <span style="font-size:12px;font-weight:600;color:#374151;">{log.get('operation', '')}</span>
                    <span style="font-size:10px;background:{color}15;color:{color};padding:1px 6px;border-radius:4px;font-weight:500;">{log.get('status', '')}</span>
                    <span style="font-size:10px;color:#9CA3AF;">{time_ago}</span>
                    {f'<span style="font-size:10px;color:#6B7280;">{duration_str}</span>' if duration_str else ''}
                </div>
                {f'<div style="font-size:11px;color:#6B7280;">{log.get("details", "")[:100]}</div>' if log.get("details") else ''}
                {error_html}
            </div>
        </div>"""

    html += "</div>"

    return html


# ================================================================
# CONTEXT MANAGER FOR TIMING OPERATIONS
# ================================================================

import time
import uuid
from contextlib import contextmanager


@contextmanager
def track_processing(project_id: str, operation: str, filename: str = ""):
    """Context manager to track processing operations automatically.

    Usage:
        with track_processing(project_id, "extract_invoice", "invoice.pdf") as log_id:
            result = process_invoice(...)
    """
    log_id = add_processing_log(project_id, operation, "processing", filename)
    start_time = time.time()
    try:
        yield log_id
        duration = int((time.time() - start_time) * 1000)
        update_processing_log(log_id, "completed", duration_ms=duration)
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        update_processing_log(log_id, "failed", str(e), duration)
        raise
