"""Cash Flow Forecasting - Predict future cash flows for 3-6 months.

Uses historical transaction patterns and invoice data to forecast
future cash inflows and outflows with confidence intervals.
"""

from collections import defaultdict
from datetime import datetime, date, timedelta
from typing import Any, Optional
import random

from app.database import get_invoices, get_bank_transactions


class CashFlowForecaster:
    """Forecast future cash flows based on historical patterns."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.invoices = get_invoices(project_id)
        self.transactions = get_bank_transactions(project_id)

    def forecast(self, months: int = 6) -> dict:
        """Generate a cash flow forecast for the next N months.

        Uses:
        - Historical monthly averages from invoices
        - Bank transaction patterns
        - Seasonal adjustment factors
        - Conservative confidence intervals
        """
        # Analyze historical monthly patterns
        monthly_revenue = defaultdict(float)
        monthly_expenses = defaultdict(float)

        for inv in self.invoices:
            date_str = inv.get("invoice_date", "")
            try:
                dt = datetime.fromisoformat(date_str) if isinstance(date_str, str) else date_str
                month_key = dt.strftime("%Y-%m")
                monthly_revenue[month_key] += inv.get("total_amount", 0)
            except (ValueError, AttributeError):
                pass

        for tx in self.transactions:
            date_str = tx.get("transaction_date", "")
            try:
                dt = datetime.fromisoformat(date_str) if isinstance(date_str, str) else date_str
                month_key = dt.strftime("%Y-%m")
                monthly_expenses[month_key] += tx.get("debit", 0)
                monthly_revenue[month_key] += tx.get("credit", 0)
            except (ValueError, AttributeError):
                pass

        # Calculate averages
        avg_revenue = sum(monthly_revenue.values()) / max(len(monthly_revenue), 1)
        avg_expenses = sum(monthly_expenses.values()) / max(len(monthly_expenses), 1)

        # Growth trend (simple linear)
        sorted_months = sorted(monthly_revenue.keys())
        if len(sorted_months) >= 2:
            first_rev = monthly_revenue.get(sorted_months[0], avg_revenue)
            last_rev = monthly_revenue.get(sorted_months[-1], avg_revenue)
            growth_rate = (last_rev - first_rev) / max(first_rev, 1)
            # Limit growth rate to reasonable range
            growth_rate = max(-0.05, min(0.15, growth_rate / max(len(sorted_months), 1)))
        else:
            growth_rate = 0.02  # Assume 2% monthly growth

        # Generate forecast
        today = date.today()
        forecast_months = []
        cumulative_revenue = 0
        cumulative_expenses = 0

        for i in range(months):
            forecast_date = date(today.year + (today.month + i - 1) // 12,
                                ((today.month + i - 1) % 12) + 1, 1)

            # Apply seasonal factor
            seasonal = self._get_seasonal_factor(forecast_date.month)

            # Projected values with growth
            projected_revenue = avg_revenue * (1 + growth_rate) ** (i + 1) * seasonal
            projected_expenses = avg_expenses * (1 + growth_rate * 0.7) ** (i + 1) * seasonal

            # Confidence intervals (wider for further months)
            confidence_reduction = 1.0 - (i * 0.08)
            confidence_low = projected_revenue * (0.7 + (confidence_reduction * 0.2))
            confidence_high = projected_revenue * (1.3 - (confidence_reduction * 0.2))
            net_flow = projected_revenue - projected_expenses

            cumulative_revenue += projected_revenue
            cumulative_expenses += projected_expenses

            forecast_months.append({
                "month": forecast_date.strftime("%B %Y"),
                "month_key": forecast_date.strftime("%Y-%m"),
                "projected_revenue": round(projected_revenue, 2),
                "projected_expenses": round(projected_expenses, 2),
                "net_cash_flow": round(net_flow, 2),
                "confidence_interval_low": round(confidence_low, 2),
                "confidence_interval_high": round(confidence_high, 2),
                "seasonal_factor": round(seasonal, 2),
            })

        total_projected_revenue = sum(m["projected_revenue"] for m in forecast_months)
        total_projected_expenses = sum(m["projected_expenses"] for m in forecast_months)

        # Calculate health score
        months_positive = sum(1 for m in forecast_months if m["net_cash_flow"] > 0)
        health_score = round((months_positive / max(months, 1)) * 100, 1)

        return {
            "generated_at": datetime.now().isoformat(),
            "forecast_period": f"{months} months",
            "historical_months_analyzed": len(monthly_revenue),
            "avg_monthly_revenue": round(avg_revenue, 2),
            "avg_monthly_expenses": round(avg_expenses, 2),
            "monthly_growth_rate": round(growth_rate * 100, 1),
            "total_projected_revenue": round(total_projected_revenue, 2),
            "total_projected_expenses": round(total_projected_expenses, 2),
            "net_projected_cash_flow": round(total_projected_revenue - total_projected_expenses, 2),
            "health_score": health_score,
            "health_label": "Excellent" if health_score >= 80 else ("Good" if health_score >= 60 else "Needs Attention"),
            "forecast": forecast_months,
            "insights": self._generate_insights(forecast_months, avg_revenue, avg_expenses),
        }

    def _get_seasonal_factor(self, month: int) -> float:
        """Get seasonal adjustment factor based on Indian business patterns."""
        # Higher in festive/Q4 months (Oct-Mar), lower in Q1 (Apr-Jun)
        seasonal = {
            1: 1.10, 2: 1.05, 3: 1.15,   # Q4 - High
            4: 0.85, 5: 0.80, 6: 0.85,   # Q1 - Low
            7: 0.90, 8: 0.95, 9: 1.00,   # Q2 - Moderate
            10: 1.10, 11: 1.15, 12: 1.20, # Q3 - Festive
        }
        return seasonal.get(month, 1.0)

    def _generate_insights(self, forecast: list, avg_rev: float, avg_exp: float) -> list:
        """Generate actionable insights from the forecast."""
        insights = []

        total_net = sum(m["net_cash_flow"] for m in forecast)
        if total_net < 0:
            insights.append("🔴 Projected negative cash flow over forecast period. Consider reducing discretionary expenses or accelerating receivables.")
        elif total_net > 0 and all(m["net_cash_flow"] > 0 for m in forecast[:3]):
            insights.append("🟢 Strong positive cash flow projected. Consider investing surplus in growth initiatives or creating a reserve fund.")

        for m in forecast:
            if m["net_cash_flow"] < 0:
                insights.append(f"⚠️ {m['month']}: Expected cash deficit of ₹{abs(m['net_cash_flow']):,.0f}. Plan working capital in advance.")

        # Seasonal suggestions
        peak_month = max(forecast, key=lambda x: x["projected_revenue"])
        insights.append(f"📈 Peak revenue expected in {peak_month['month']} at ₹{peak_month['projected_revenue']:,.0f}. Prepare for increased working capital needs.")

        if avg_exp > avg_rev * 0.85:
            insights.append("💡 Expense-to-revenue ratio is high (>85%). Review cost structure for optimization opportunities.")

        return insights[:5]


def format_forecast_html(forecast_data: dict) -> str:
    """Format cash flow forecast as styled HTML."""
    health_color = {"Excellent": "#059669", "Good": "#D97706", "Needs Attention": "#DC2626"}
    hc = health_color.get(forecast_data.get("health_label", "Good"), "#6B7280")

    months_html = ""
    for i, m in enumerate(forecast_data.get("forecast", [])):
        flow_color = "#059669" if m["net_cash_flow"] >= 0 else "#DC2626"
        flow_icon = "📈" if m["net_cash_flow"] >= 0 else "📉"
        months_html += f"""
        <div class="forecast-month" style="animation-delay:{i * 0.05}s">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-weight:600;font-size:13px;">{m.get('month', '')}</span>
                <span style="font-size:15px;font-weight:700;color:{flow_color};">
                    {flow_icon} ₹{m.get('net_cash_flow', 0):,.0f}
                </span>
            </div>
            <div style="display:flex;gap:12px;margin-top:4px;font-size:11px;color:#6B7280;">
                <span>Revenue: ₹{m.get('projected_revenue', 0):,.0f}</span>
                <span>Expenses: ₹{m.get('projected_expenses', 0):,.0f}</span>
                <span>Range: ₹{m.get('confidence_interval_low', 0):,.0f} - ₹{m.get('confidence_interval_high', 0):,.0f}</span>
            </div>
            <div class="forecast-bar-container">
                <div class="forecast-bar" style="width:{min(abs(m.get('net_cash_flow', 0)) / max(abs(forecast_data.get('net_projected_cash_flow', 1)), 1) * 100, 100)}%;background:{flow_color};"></div>
            </div>
        </div>"""

    insights_html = ""
    for insight in forecast_data.get("insights", []):
        insights_html += f'<li style="padding:4px 0;font-size:12px;line-height:1.5;">{insight}</li>'

    return f"""
    <div style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div>
                <h3 style="margin:0;color:#1F4E79;">🔮 Cash Flow Forecast</h3>
                <p style="margin:2px 0 0;font-size:12px;color:#6B7280;">{forecast_data.get('forecast_period', '')} · Based on {forecast_data.get('historical_months_analyzed', 0)} months of history</p>
            </div>
            <div style="text-align:right;">
                <div style="font-size:11px;color:#6B7280;">Health Score</div>
                <div style="font-size:20px;font-weight:700;color:{hc};">{forecast_data.get('health_score', 0)}%</div>
                <div style="font-size:10px;color:{hc};">{forecast_data.get('health_label', '')}</div>
            </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px;">
            <div style="background:#F0F4F8;border-radius:6px;padding:8px;text-align:center;">
                <div style="font-size:10px;color:#6B7280;">Monthly Revenue</div>
                <div style="font-size:14px;font-weight:700;">₹{forecast_data.get('avg_monthly_revenue', 0):,.0f}</div>
            </div>
            <div style="background:#F0F4F8;border-radius:6px;padding:8px;text-align:center;">
                <div style="font-size:10px;color:#6B7280;">Growth Rate</div>
                <div style="font-size:14px;font-weight:700;color:#059669;">+{forecast_data.get('monthly_growth_rate', 0)}%</div>
            </div>
            <div style="background:#F0F4F8;border-radius:6px;padding:8px;text-align:center;">
                <div style="font-size:10px;color:#6B7280;">Total Revenue</div>
                <div style="font-size:14px;font-weight:700;">₹{forecast_data.get('total_projected_revenue', 0):,.0f}</div>
            </div>
            <div style="background:#F0F4F8;border-radius:6px;padding:8px;text-align:center;">
                <div style="font-size:10px;color:#6B7280;">Net Cash Flow</div>
                <div style="font-size:14px;font-weight:700;color:{'#059669' if forecast_data.get('net_projected_cash_flow', 0) >= 0 else '#DC2626'};">₹{forecast_data.get('net_projected_cash_flow', 0):,.0f}</div>
            </div>
        </div>

        <div style="margin-bottom:12px;">
            <h4 style="margin:0 0 6px;font-size:13px;color:#374151;">Monthly Projections</h4>
            {months_html}
        </div>

        {f'<div style="border-top:1px solid #E2E8F0;padding-top:8px;"><h4 style="margin:0 0 6px;font-size:13px;color:#374151;">💡 Insights</h4><ul style="margin:0;padding-left:20px;">{insights_html}</ul></div>' if insights_html else ''}
    </div>

    <style>
    .forecast-month {{
        background:#F9FAFB;border:1px solid #E2E8F0;border-radius:6px;padding:8px 12px;margin-bottom:6px;
        animation:fadeInUp 0.3s ease-out both;transition:all 0.2s;
    }}
    .forecast-month:hover {{border-color:#2E75B6;transform:translateX(4px);}}
    .forecast-bar-container {{height:4px;background:#E2E8F0;border-radius:2px;margin-top:6px;overflow:hidden;}}
    .forecast-bar {{height:100%;border-radius:2px;transition:width 0.5s ease-out;}}
    </style>"""
