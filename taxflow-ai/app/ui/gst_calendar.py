"""GST Compliance Calendar - Important due dates and filing calendar.

Provides a visual calendar of GST compliance deadlines including:
- Monthly GSTR-1, GSTR-3B due dates
- Quarterly composition scheme dates
- Annual return due dates
- ITC reversal dates
- Days remaining countdown
"""

from datetime import datetime, date, timedelta
from typing import Optional


def build_calendar_html() -> str:
    """Build the complete GST compliance calendar HTML."""
    today = date.today()
    current_month = today.month
    current_year = today.year

    # Calculate all due dates
    deadlines = _get_all_deadlines(current_year)

    # Mark which ones are upcoming/overdue
    upcoming = []
    overdue = []
    completed = []

    for dl in deadlines:
        dl_date = dl["date"]
        if dl_date < today:
            overdue.append(dl)
        elif dl_date == today:
            upcoming.insert(0, dl)  # Due today, show first
        elif dl_date <= today + timedelta(days=30):
            upcoming.append(dl)
        else:
            completed.append(dl)

    # Build HTML
    html = f"""
    <div class="calendar-container">
        <div class="calendar-header">
            <div class="calendar-title">
                <span class="calendar-icon">📅</span>
                GST Compliance Calendar
            </div>
            <div class="calendar-date-display">
                {today.strftime('%B %Y')}
            </div>
        </div>

        <div class="calendar-summary-strip">
            <div class="calendar-stat calendar-stat-danger">
                <div class="calendar-stat-value">{len(overdue)}</div>
                <div class="calendar-stat-label">Overdue</div>
            </div>
            <div class="calendar-stat calendar-stat-warning">
                <div class="calendar-stat-value">{len(upcoming)}</div>
                <div class="calendar-stat-label">Due Soon</div>
            </div>
            <div class="calendar-stat calendar-stat-success">
                <div class="calendar-stat-value">{len(completed)}</div>
                <div class="calendar-stat-label">Upcoming</div>
            </div>
        </div>
    """

    # Overdue items
    if overdue:
        html += """
        <div class="calendar-section">
            <div class="calendar-section-title calendar-section-danger">🔴 Overdue</div>
        """
        for dl in sorted(overdue, key=lambda x: x["date"]):
            html += _deadline_card(dl, "overdue")
        html += "</div>"

    # Due this month / soon
    if upcoming:
        html += """
        <div class="calendar-section">
            <div class="calendar-section-title calendar-section-warning">🟡 Due Soon</div>
        """
        for dl in sorted(upcoming, key=lambda x: x["date"]):
            html += _deadline_card(dl, "upcoming")
        html += "</div>"

    # All deadlines (collapsed)
    html += """
        <div class="calendar-section">
            <div class="calendar-section-title calendar-section-info">📋 All Deadlines</div>
            <div class="calendar-all-list">
    """
    for dl in sorted(deadlines, key=lambda x: x["date"]):
        status = _get_status_class(dl["date"], today)
        html += _deadline_card(dl, status)

    html += """
            </div>
        </div>
    </div>
    """

    return html


def _deadline_card(deadline: dict, status: str) -> str:
    """Build a single deadline card."""
    dl_date = deadline["date"]
    days_remaining = (dl_date - date.today()).days

    if status == "overdue":
        badge = f"<span class='calendar-badge calendar-badge-danger'>⏰ Overdue by {abs(days_remaining)}d</span>"
        border = "calendar-item-border-danger"
    elif status == "upcoming":
        if days_remaining == 0:
            badge = "<span class='calendar-badge calendar-badge-warning'>🔔 Due Today!</span>"
        else:
            badge = f"<span class='calendar-badge calendar-badge-warning'>{days_remaining}d remaining</span>"
        border = "calendar-item-border-warning"
    else:
        badge = f"<span class='calendar-badge calendar-badge-info'>{days_remaining}d away</span>"
        border = "calendar-item-border-info"

    return f"""
    <div class="calendar-item {border} animate-fade-in">
        <div class="calendar-item-date">
            <div class="calendar-item-day">{dl_date.strftime('%d')}</div>
            <div class="calendar-item-month">{dl_date.strftime('%b')}</div>
        </div>
        <div class="calendar-item-content">
            <div class="calendar-item-title">{deadline['title']}</div>
            <div class="calendar-item-desc">{deadline['description']}</div>
            <div class="calendar-item-meta">
                <span class="calendar-item-form">{deadline['form']}</span>
                <span class="calendar-item-frequency">{deadline['frequency']}</span>
            </div>
        </div>
        <div class="calendar-item-badge">
            {badge}
        </div>
    </div>
    """


def _get_status_class(dl_date: date, today: date) -> str:
    """Get the status class for a deadline."""
    if dl_date < today:
        return "overdue"
    elif dl_date <= today + timedelta(days=30):
        return "upcoming"
    return "future"


def _get_all_deadlines(year: int) -> list[dict]:
    """Get all GST compliance deadlines for a given year."""
    deadlines = []

    # Helper to get nth day of month, or next working day
    def get_date(month: int, day: int) -> date:
        d = date(year, month, day)
        # If weekend, move to next Monday
        while d.weekday() >= 5:
            d += timedelta(days=1)
        return d

    for month in range(1, 13):
        # GSTR-1: Monthly - 11th of next month
        if month < 12:
            d = get_date(month + 1, 11)
        else:
            d = get_date(1, 11) if year < 2025 else date(year + 1, 1, 11)
            while d.weekday() >= 5:
                d += timedelta(days=1)
        deadlines.append({
            "date": d if month < 12 else date(year + 1, 1, 11) if month == 12 else d,
            "title": f"GSTR-1 Filing - {date(year, month, 1).strftime('%B %Y')}",
            "description": "Details of outward supplies of goods or services (Monthly)",
            "form": "GSTR-1",
            "frequency": "Monthly",
        })

        # GSTR-3B: Monthly - 20th of next month
        if month < 12:
            d = get_date(month + 1, 20)
        else:
            d = date(year + 1, 1, 20)
            while d.weekday() >= 5:
                d += timedelta(days=1)
        deadlines.append({
            "date": d,
            "title": f"GSTR-3B Filing - {date(year, month, 1).strftime('%B %Y')}",
            "description": "Monthly summary return and payment of taxes",
            "form": "GSTR-3B",
            "frequency": "Monthly",
        })

        # GSTR-2A (dynamic): 12th of next month
        if month < 12:
            d = get_date(month + 1, 12)
        else:
            d = date(year + 1, 1, 12)
            while d.weekday() >= 5:
                d += timedelta(days=1)
        deadlines.append({
            "date": d,
            "title": f"GSTR-2A Available - {date(year, month, 1).strftime('%B %Y')}",
            "description": "Auto-drafted purchase data from suppliers' GSTR-1",
            "form": "GSTR-2A",
            "frequency": "Monthly",
        })

    # Quarterly deadlines for QRMP scheme
    for q_month in [1, 4, 7, 10]:
        # GSTR-1 Quarterly: 13th of month after quarter
        if q_month + 2 <= 12:
            d = get_date(q_month + 2, 13)
        else:
            d = date(year + 1, 1, 13)
            while d.weekday() >= 5:
                d += timedelta(days=1)
        deadlines.append({
            "date": d if q_month + 2 <= 12 else date(year + 1, 1, 13),
            "title": f"GSTR-1 (Quarterly) - Q{((q_month - 1) // 3) + 1} {year}",
            "description": "Quarterly return for composition dealers / QRMP scheme",
            "form": "GSTR-1 (Q)",
            "frequency": "Quarterly",
        })

        # PMT-06: Monthly tax payment for QRMP
        for m in range(q_month, q_month + 3):
            if m <= 12:
                d = get_date(m, 25)
                deadlines.append({
                    "date": d,
                    "title": f"PMT-06 Tax Payment - {date(year, m, 1).strftime('%B %Y')}",
                    "description": "Monthly tax payment for QRMP scheme taxpayers",
                    "form": "PMT-06",
                    "frequency": "Monthly (QRMP)",
                })

    # Annual returns
    # GSTR-9: 31st December of next year
    deadlines.append({
        "date": date(year + 1, 12, 31),
        "title": f"GSTR-9 Annual Return - FY {year}-{year+1}",
        "description": "Annual consolidated GST return",
        "form": "GSTR-9",
        "frequency": "Annual",
    })

    # GSTR-9C: 31st December of next year (now merged with GSTR-9)
    deadlines.append({
        "date": date(year + 1, 12, 31),
        "title": f"GSTR-9C Audit - FY {year}-{year+1}",
        "description": "Self-certified reconciliation statement (merged with GSTR-9)",
        "form": "GSTR-9C",
        "frequency": "Annual",
    })

    # GSTR-10: Final return within 3 months of cancellation
    # (Not adding fixed date as it depends on cancellation date)

    # ITC reversal deadline: Due date of September following the year
    deadlines.append({
        "date": date(year + 1, 9, 20),
        "title": f"ITC Reversal Deadline - FY {year}-{year+1}",
        "description": "Last date to reverse ITC for invoices not paid within 180 days",
        "form": "GSTR-3B",
        "frequency": "Annual (ITC)",
    })

    # E-invoice compliance (ongoing - not a hard deadline)
    import datetime as dt_module
    _today = dt_module.date.today()
    deadlines.append({
        "date": _today + dt_module.timedelta(days=1),
        "title": "E-Invoice Generation (if applicable)",
        "description": "Continuous compliance - Generate IRN for all B2B invoices",
        "form": "E-Invoice",
        "frequency": "Ongoing",
    })

    return deadlines


def get_next_deadline() -> Optional[dict]:
    """Get the nearest upcoming deadline."""
    deadlines = _get_all_deadlines(date.today().year)
    today = date.today()

    for dl in sorted(deadlines, key=lambda x: x["date"]):
        if dl["date"] >= today:
            return dl
    return None


def get_urgent_deadlines(days: int = 7) -> list[dict]:
    """Get deadlines due within the specified number of days."""
    deadlines = _get_all_deadlines(date.today().year)
    today = date.today()
    cutoff = today + timedelta(days=days)

    return [
        dl for dl in sorted(deadlines, key=lambda x: x["date"])
        if today <= dl["date"] <= cutoff
    ]
