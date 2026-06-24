"""Activity Feed / Audit Trail module.

Tracks and displays all user actions within the application
including document uploads, processing, exports, and AI operations.
"""

from datetime import datetime, timedelta
from typing import Any, Optional
import json


def build_activity_feed_html(activities: list[dict]) -> str:
    """Build the activity feed HTML from a list of activity records."""
    if not activities:
        return """
        <div class="activity-empty">
            <div class="activity-empty-icon">📋</div>
            <div class="activity-empty-text">No activity yet.<br>Start by uploading documents or chatting with the AI.</div>
        </div>
        """

    html = '<div class="activity-timeline">'

    for i, activity in enumerate(activities):
        html += _build_activity_item(activity, i)

    html += "</div>"
    return html


def _build_activity_item(activity: dict, index: int) -> str:
    """Build a single activity timeline item."""
    activity_type = activity.get("type", "info")
    title = activity.get("title", "")
    description = activity.get("description", "")
    timestamp = activity.get("timestamp", "")
    metadata = activity.get("metadata", {})

    # Determine icon and color based on type
    type_config = {
        "upload": {"icon": "📤", "color": "activity-blue"},
        "process": {"icon": "⚙️", "color": "activity-purple"},
        "extract": {"icon": "🔍", "color": "activity-teal"},
        "reconcile": {"icon": "🔄", "color": "activity-green"},
        "export": {"icon": "📊", "color": "activity-amber"},
        "chat": {"icon": "💬", "color": "activity-blue"},
        "anomaly": {"icon": "⚠️", "color": "activity-red"},
        "project": {"icon": "📁", "color": "activity-indigo"},
        "auth": {"icon": "🔐", "color": "activity-gray"},
        "error": {"icon": "❌", "color": "activity-red"},
        "success": {"icon": "✅", "color": "activity-green"},
        "info": {"icon": "ℹ️", "color": "activity-blue"},
    }

    config = type_config.get(activity_type, type_config["info"])
    icon = config["icon"]
    color = config["color"]

    # Format time
    time_ago = _format_time_ago(timestamp)

    # Build metadata details
    details_html = ""
    if metadata:
        detail_lines = []
        for key, value in metadata.items():
            if isinstance(value, (int, float)):
                if key in ("total_amount", "amount"):
                    detail_lines.append(f"₹{value:,.2f}")
                else:
                    detail_lines.append(f"{value}")
            elif isinstance(value, str) and value:
                detail_lines.append(f"{value[:50]}")

        if detail_lines:
            details_html = f'<div class="activity-details">{" · ".join(detail_lines[:3])}</div>'

    # Animation delay
    delay = f"{index * 0.05}s"

    return f"""
    <div class="activity-item animate-slide-in-left" style="animation-delay:{delay}">
        <div class="activity-dot {color}"></div>
        <div class="activity-content">
            <div class="activity-header">
                <span class="activity-icon">{icon}</span>
                <span class="activity-title">{title}</span>
                <span class="activity-time">{time_ago}</span>
            </div>
            <div class="activity-description">{description}</div>
            {details_html}
        </div>
    </div>
    """


def _format_time_ago(timestamp_str: str) -> str:
    """Format a timestamp as a human-readable 'time ago' string."""
    if not timestamp_str:
        return ""

    try:
        if isinstance(timestamp_str, str):
            dt = datetime.fromisoformat(timestamp_str)
        else:
            dt = timestamp_str

        now = datetime.now()
        diff = now - dt

        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            mins = int(diff.total_seconds() / 60)
            return f"{mins}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}d ago"
        else:
            return dt.strftime("%d %b")
    except (ValueError, TypeError):
        return timestamp_str[:16] if timestamp_str else ""


def build_quick_stats_html(documents: list[dict], invoices: list[dict],
                           transactions: list[dict], anomalies: list[dict],
                           projects_count: int = 0) -> str:
    """Build quick statistics overview for the activity panel."""
    total_processed = len(invoices) + len(transactions)
    high_anomalies = len([a for a in anomalies if a.get("severity") == "high"])

    return f"""
    <div class="quick-stats">
        <div class="quick-stat-item">
            <div class="quick-stat-value">{len(documents)}</div>
            <div class="quick-stat-label">Documents</div>
        </div>
        <div class="quick-stat-item">
            <div class="quick-stat-value">{total_processed}</div>
            <div class="quick-stat-label">Data Points</div>
        </div>
        <div class="quick-stat-item">
            <div class="quick-stat-value">{len(invoices)}</div>
            <div class="quick-stat-label">Invoices</div>
        </div>
        <div class="quick-stat-item">
            <div class="quick-stat-value">{high_anomalies}</div>
            <div class="quick-stat-label">Issues</div>
        </div>
    </div>
    """
