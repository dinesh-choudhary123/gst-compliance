"""Interactive Dashboard with Plotly charts for TaxFlow AI.

Provides beautiful, interactive visualizations of financial data
including revenue breakdowns, tax trends, ITC analysis, and anomaly distributions.
All charts are built with Plotly for interactivity (hover, zoom, click).
"""

import json
from datetime import datetime, timedelta
from typing import Any, Optional

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _HAS_PLOTLY = True
except ImportError:
    go = None
    make_subplots = None
    _HAS_PLOTLY = False


def build_dashboard_html(project_info: dict, invoices: list[dict],
                         transactions: list[dict], anomalies: list[dict],
                         documents: list[dict], gstr1_data: Optional[dict] = None,
                         gstr3b_data: Optional[dict] = None) -> str:
    """Build a complete dashboard HTML with embedded Plotly charts."""
    charts_html = ""

    # 1. Key Metrics Cards
    metrics_html = _build_metrics_cards(invoices, transactions, anomalies, documents)
    charts_html += metrics_html

    # 2. Revenue vs Tax Pie Chart
    pie_chart = _build_revenue_tax_pie(invoices)
    charts_html += pie_chart

    # 3. Invoice Amounts Bar Chart
    bar_chart = _build_invoice_bar_chart(invoices)
    charts_html += bar_chart

    # 4. Monthly Trend Line Chart
    trend_chart = _build_monthly_trend(invoices)
    charts_html += trend_chart

    # 5. ITC Eligibility Overview
    itc_chart = _build_itc_chart(invoices)
    charts_html += itc_chart

    # 6. Anomaly Severity Distribution
    anomaly_chart = _build_anomaly_chart(anomalies)
    charts_html += anomaly_chart

    # 7. Bank Transaction Summary
    tx_chart = _build_transaction_chart(transactions)
    charts_html += tx_chart

    # 8. Tax Rate Distribution
    rate_chart = _build_tax_rate_chart(invoices)
    charts_html += rate_chart

    return f"""
    <div class="dashboard-container">
        <div class="dashboard-grid">
            {charts_html}
        </div>
    </div>
    <script>
    // Make charts responsive
    function resizePlots() {{
        var plots = document.querySelectorAll('.js-plotly-plot');
        plots.forEach(function(p) {{
            try {{
                Plotly.Plots.resize(p);
            }} catch(e) {{}}
        }});
    }}
    window.addEventListener('resize', resizePlots);
    setTimeout(resizePlots, 500);
    </script>
    """


def _build_metrics_cards(invoices: list[dict], transactions: list[dict],
                         anomalies: list[dict], documents: list[dict]) -> str:
    """Build key metrics summary cards."""
    total_revenue = sum(i.get("total_amount", 0) for i in invoices)
    total_tax = sum(i.get("cgst_amount", 0) + i.get("sgst_amount", 0) +
                    i.get("igst_amount", 0) + i.get("cess_amount", 0) for i in invoices)
    total_credits = sum(t.get("credit", 0) for t in transactions)
    total_debits = sum(t.get("debit", 0) for t in transactions)
    high_anomalies = len([a for a in anomalies if a.get("severity") == "high"])
    resolved = len([a for a in anomalies if a.get("resolved")])
    invoice_count = len(invoices)
    tx_count = len(transactions)

    return f"""
    <div class="metrics-grid">
        <div class="metric-card metric-gradient-blue animate-scale-in" style="animation-delay:0.05s">
            <div class="metric-icon">💰</div>
            <div class="metric-value">₹{total_revenue:,.0f}</div>
            <div class="metric-label">Total Revenue</div>
            <div class="metric-trend">📊 {invoice_count} invoices</div>
        </div>
        <div class="metric-card metric-gradient-teal animate-scale-in" style="animation-delay:0.1s">
            <div class="metric-icon">🧾</div>
            <div class="metric-value">₹{total_tax:,.0f}</div>
            <div class="metric-label">Total Tax</div>
            <div class="metric-trend">{'CGST+SGST+IGST'}</div>
        </div>
        <div class="metric-card metric-gradient-purple animate-scale-in" style="animation-delay:0.15s">
            <div class="metric-icon">🏦</div>
            <div class="metric-value">₹{(total_credits - total_debits):,.0f}</div>
            <div class="metric-label">Net Cash Flow</div>
            <div class="metric-trend">{tx_count} transactions</div>
        </div>
        <div class="metric-card metric-gradient-amber animate-scale-in" style="animation-delay:0.2s">
            <div class="metric-icon">{'⚠️' if high_anomalies > 0 else '✅'}</div>
            <div class="metric-value">{len(anomalies)}</div>
            <div class="metric-label">Anomalies</div>
            <div class="metric-trend">{high_anomalies} high, {resolved} resolved</div>
        </div>
    </div>
    """


def _build_revenue_tax_pie(invoices: list[dict]) -> str:
    """Build a pie chart showing revenue vs tax breakdown."""
    if not invoices:
        return _empty_chart("Revenue Breakdown", "Upload invoices to see revenue breakdown")

    total_taxable = sum(i.get("taxable_amount", 0) for i in invoices)
    total_cgst = sum(i.get("cgst_amount", 0) for i in invoices)
    total_sgst = sum(i.get("sgst_amount", 0) for i in invoices)
    total_igst = sum(i.get("igst_amount", 0) for i in invoices)
    total_cess = sum(i.get("cess_amount", 0) for i in invoices)

    # Only show non-zero values
    values = []
    labels = []
    colors = []

    if total_taxable > 0:
        values.append(total_taxable)
        labels.append("Taxable Amount")
        colors.append("#2E75B6")
    if total_cgst > 0:
        values.append(total_cgst)
        labels.append("CGST")
        colors.append("#4CAF50")
    if total_sgst > 0:
        values.append(total_sgst)
        labels.append("SGST")
        colors.append("#8BC34A")
    if total_igst > 0:
        values.append(total_igst)
        labels.append("IGST")
        colors.append("#FF9800")
    if total_cess > 0:
        values.append(total_cess)
        labels.append("Cess")
        colors.append("#F44336")

    if not values:
        return _empty_chart("Revenue Breakdown", "No tax data available")

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(size=12, family='Inter, sans-serif'),
        hovertemplate='<b>%{label}</b><br>₹%{value:,.2f}<br>%{percent}<extra></extra>',
    )])

    fig.update_layout(
        title=dict(
            text="💰 Revenue & Tax Breakdown",
            font=dict(size=16, family='Inter, sans-serif', color='#1F4E79'),
            x=0.5,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#1A202C'),
        margin=dict(l=20, r=20, t=60, b=20),
        height=350,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.1, xanchor='center', x=0.5),
        hoverlabel=dict(bgcolor='#FFFFFF', font_size=13),
    )

    return _chart_card("pie-chart", fig)


def _build_invoice_bar_chart(invoices: list[dict]) -> str:
    """Build a bar chart of invoice amounts."""
    if not invoices:
        return _empty_chart("Invoice Amounts", "Upload invoices to see amounts")

    # Top 10 invoices by amount
    sorted_invs = sorted(invoices, key=lambda x: x.get("total_amount", 0), reverse=True)[:10]
    sorted_invs.reverse()  # For horizontal bar, bottom to top

    names = [inv.get("invoice_number", f"#{i+1}")[:15] for i, inv in enumerate(sorted_invs)]
    amounts = [inv.get("total_amount", 0) for inv in sorted_invs]
    taxable = [inv.get("taxable_amount", 0) for inv in sorted_invs]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names,
        x=amounts,
        name='Total Amount',
        orientation='h',
        marker=dict(
            color=[_amount_to_color(a) for a in amounts],
            line=dict(color='rgba(255,255,255,0.3)', width=1),
        ),
        hovertemplate='<b>%{y}</b><br>Total: ₹%{x:,.2f}<extra></extra>',
    ))

    fig.update_layout(
        title=dict(text="🧾 Top Invoice Amounts", font=dict(size=16, family='Inter', color='#1F4E79'), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#1F4E79'),
        xaxis=dict(title="Amount (₹)", tickprefix="₹", gridcolor='rgba(128,128,128,0.15)'),
        yaxis=dict(title="", gridcolor='rgba(128,128,128,0.15)'),
        margin=dict(l=100, r=20, t=60, b=30),
        height=350,
        hoverlabel=dict(bgcolor='#FFFFFF', font_size=13),
        bargap=0.3,
    )

    return _chart_card("bar-chart", fig)


def _build_monthly_trend(invoices: list[dict]) -> str:
    """Build a line chart showing monthly trends."""
    if not invoices:
        return _empty_chart("Monthly Trends", "Upload invoices to see monthly trends")

    monthly_data = {}
    for inv in invoices:
        date_str = inv.get("invoice_date", "")
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str) if isinstance(date_str, str) else date_str
                month_key = dt.strftime("%b %Y")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {"taxable": 0.0, "tax": 0.0, "total": 0.0, "count": 0}
                monthly_data[month_key]["taxable"] += inv.get("taxable_amount", 0)
                monthly_data[month_key]["tax"] += inv.get("cgst_amount", 0) + inv.get("sgst_amount", 0) + inv.get("igst_amount", 0)
                monthly_data[month_key]["total"] += inv.get("total_amount", 0)
                monthly_data[month_key]["count"] += 1
            except (ValueError, TypeError):
                pass

    if not monthly_data:
        return _empty_chart("Monthly Trends", "No dated invoices available")

    months = sorted(monthly_data.keys())
    totals = [monthly_data[m]["total"] for m in months]
    taxes = [monthly_data[m]["tax"] for m in months]
    counts = [monthly_data[m]["count"] for m in months]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=months,
        y=totals,
        name='Revenue',
        marker_color='#2E75B6',
        opacity=0.7,
        hovertemplate='<b>%{x}</b><br>Revenue: ₹%{y:,.2f}<extra></extra>',
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=months,
        y=taxes,
        name='Tax',
        mode='lines+markers',
        line=dict(color='#FF9800', width=3),
        marker=dict(size=8, color='#FF9800', line=dict(width=2, color='white')),
        hovertemplate='<b>%{x}</b><br>Tax: ₹%{y:,.2f}<extra></extra>',
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=months,
        y=counts,
        name='Invoice Count',
        mode='lines+markers',
        line=dict(color='#4CAF50', width=2, dash='dot'),
        marker=dict(size=6, color='#4CAF50'),
        hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>',
    ), secondary_y=True)

    fig.update_layout(
        title=dict(text="📈 Monthly Financial Trends", font=dict(size=16, family='Inter', color='#1F4E79'), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#1F4E79'),
        legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5),
        margin=dict(l=20, r=20, t=60, b=30),
        height=350,
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#FFFFFF', font_size=12),
        xaxis=dict(gridcolor='rgba(128,128,128,0.15)'),
        yaxis=dict(title="Amount (₹)", gridcolor='rgba(128,128,128,0.15)'),
        yaxis2=dict(title="Count", gridcolor='rgba(128,128,128,0.1)'),
    )

    return _chart_card("trend-chart", fig)


def _build_itc_chart(invoices: list[dict]) -> str:
    """Build ITC eligibility overview chart."""
    if not invoices:
        return _empty_chart("ITC Overview", "Upload invoices to see ITC analysis")

    # Analyze ITC eligibility
    eligible_count = 0
    ineligible_count = 0
    eligible_amount = 0
    ineligible_amount = 0

    for inv in invoices:
        seller_gstin = inv.get("seller_gstin", "")
        total_tax = inv.get("cgst_amount", 0) + inv.get("sgst_amount", 0) + inv.get("igst_amount", 0) + inv.get("cess_amount", 0)

        # Simple ITC check
        if seller_gstin and len(seller_gstin) == 15 and total_tax > 0:
            eligible_count += 1
            eligible_amount += total_tax
        else:
            ineligible_count += 1
            ineligible_amount += total_tax

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("ITC Eligibility (Count)", "ITC Amount (₹)"),
        specs=[[{"type": "pie"}, {"type": "pie"}]],
    )

    fig.add_trace(go.Pie(
        labels=["Eligible", "Ineligible"],
        values=[eligible_count, ineligible_count],
        marker=dict(colors=["#4CAF50", "#F44336"]),
        textinfo='label+value',
        textposition='outside',
        hole=0.4,
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>',
    ), row=1, col=1)

    fig.add_trace(go.Pie(
        labels=["Eligible ITC", "Ineligible ITC"],
        values=[eligible_amount, ineligible_amount],
        marker=dict(colors=["#4CAF50", "#F44336"]),
        textinfo='label+percent',
        textposition='outside',
        hole=0.4,
        hovertemplate='<b>%{label}</b><br>₹%{value:,.2f}<br>%{percent}<extra></extra>',
    ), row=1, col=2)

    fig.update_layout(
        title=dict(text="✅ ITC Eligibility Overview", font=dict(size=16, family='Inter', color='#1F4E79'), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#1F4E79'),
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
        height=350,
        hoverlabel=dict(bgcolor='#FFFFFF', font_size=12),
    )

    return _chart_card("itc-chart", fig)


def _build_anomaly_chart(anomalies: list[dict]) -> str:
    """Build anomaly severity distribution chart."""
    if not anomalies:
        return _empty_chart("Anomaly Distribution", "No anomalies detected! ✅")

    severity_counts = {"high": 0, "medium": 0, "low": 0}
    category_counts = {}

    for a in anomalies:
        sev = a.get("severity", "medium")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

        cat = a.get("category", "other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("By Severity", "By Category"),
        specs=[[{"type": "bar"}, {"type": "bar"}]],
    )

    severities = list(severity_counts.keys())
    sev_values = list(severity_counts.values())
    sev_colors = [{"high": "#F44336", "medium": "#FF9800", "low": "#4CAF50"}.get(s, "#9E9E9E") for s in severities]

    fig.add_trace(go.Bar(
        x=severities,
        y=sev_values,
        marker_color=sev_colors,
        text=sev_values,
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>',
    ), row=1, col=1)

    categories = list(category_counts.keys())
    cat_values = list(category_counts.values())

    fig.add_trace(go.Bar(
        x=categories,
        y=cat_values,
        marker_color='#2E75B6',
        text=cat_values,
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>',
    ), row=1, col=2)

    fig.update_layout(
        title=dict(text="⚠️ Anomaly Distribution", font=dict(size=16, family='Inter', color='#1F4E79'), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#1F4E79'),
        margin=dict(l=20, r=20, t=60, b=30),
        height=350,
        hoverlabel=dict(bgcolor='#FFFFFF', font_size=12),
        showlegend=False,
        xaxis=dict(gridcolor='rgba(128,128,128,0.15)'),
        yaxis=dict(gridcolor='rgba(128,128,128,0.15)'),
        xaxis2=dict(gridcolor='rgba(128,128,128,0.15)'),
        yaxis2=dict(gridcolor='rgba(128,128,128,0.15)'),
    )

    return _chart_card("anomaly-chart", fig)


def _build_transaction_chart(transactions: list[dict]) -> str:
    """Build a bank transaction summary chart."""
    if not transactions:
        return _empty_chart("Bank Transactions", "Upload bank statements to see transaction analysis")

    credits = [t.get("credit", 0) for t in transactions if t.get("credit", 0) > 0]
    debits = [t.get("debit", 0) for t in transactions if t.get("debit", 0) > 0]

    total_credit = sum(credits)
    total_debit = sum(debits)
    net = total_credit - total_debit

    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="number+gauge+delta",
        value=total_credit,
        delta={'reference': total_debit, 'position': 'top'},
        gauge={
            'axis': {'range': [None, max(total_credit, total_debit) * 1.2]},
            'bar': {'color': "#4CAF50"},
            'steps': [{'range': [0, total_debit], 'color': '#FFEBEE'}],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': total_debit},
        },
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "💰 Credits vs Debits"},
        number={'prefix': "₹", 'font': {'size': 24}},
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#1F4E79'),
        margin=dict(l=40, r=40, t=80, b=40),
        height=300,
    )

    return _chart_card("tx-chart", fig)


def _build_tax_rate_chart(invoices: list[dict]) -> str:
    """Build a tax rate distribution chart."""
    if not invoices:
        return _empty_chart("Tax Rate Distribution", "Upload invoices to see rate distribution")

    rate_data = {}
    for inv in invoices:
        taxable = inv.get("taxable_amount", 0)
        if taxable <= 0:
            continue
        total_tax = inv.get("cgst_amount", 0) + inv.get("sgst_amount", 0) + inv.get("igst_amount", 0)
        rate = round((total_tax / taxable) * 100, 1)
        rate_key = f"{rate:.0f}%"
        if rate_key not in rate_data:
            rate_data[rate_key] = {"count": 0, "amount": 0, "tax": 0}
        rate_data[rate_key]["count"] += 1
        rate_data[rate_key]["amount"] += taxable
        rate_data[rate_key]["tax"] += total_tax

    sorted_rates = sorted(rate_data.items(), key=lambda x: float(x[0].replace("%", "")))
    rates = [r[0] for r in sorted_rates]
    counts = [r[1]["count"] for r in sorted_rates]
    amounts = [r[1]["amount"] for r in sorted_rates]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=rates,
        y=amounts,
        name='Taxable Amount',
        marker_color='#2E75B6',
        text=[f"₹{a:,.0f}" for a in amounts],
        textposition='outside',
        textfont=dict(size=10),
        hovertemplate='<b>%{x}</b><br>Taxable: ₹%{y:,.2f}<br>Count: %{customdata}<extra></extra>',
        customdata=counts,
    ))

    fig.add_trace(go.Scatter(
        x=rates,
        y=counts,
        name='Invoice Count',
        mode='lines+markers',
        yaxis='y2',
        line=dict(color='#FF9800', width=2),
        marker=dict(size=8, color='#FF9800'),
        hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>',
    ))

    fig.update_layout(
        title=dict(text="📊 Tax Rate Distribution", font=dict(size=16, family='Inter', color='#1F4E79'), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#1F4E79'),
        margin=dict(l=20, r=40, t=60, b=30),
        height=350,
        legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5),
        hoverlabel=dict(bgcolor='#FFFFFF', font_size=12),
        xaxis=dict(title="Tax Rate", gridcolor='rgba(128,128,128,0.15)'),
        yaxis=dict(title="Amount (₹)", gridcolor='rgba(128,128,128,0.15)'),
        yaxis2=dict(title="Count", overlaying='y', side='right', gridcolor='rgba(128,128,128,0.1)'),
        bargap=0.3,
    )

    return _chart_card("rate-chart", fig)


def _chart_card(chart_id: str, fig: go.Figure) -> str:
    """Wrap a Plotly figure in a styled card."""
    config = {
        'displayModeBar': False,
        'responsive': True,
        'scrollZoom': False,
    }
    chart_html = fig.to_html(
        include_plotlyjs='cdn',
        full_html=False,
        config=config,
        div_id=chart_id,
        default_height='350px',
    )
    return f"""
    <div class="chart-card animate-fade-in-up" style="animation-delay:0.2s">
        {chart_html}
    </div>
    """


def _empty_chart(title: str, message: str) -> str:
    """Return an empty chart placeholder."""
    return f"""
    <div class="chart-card chart-empty animate-fade-in-up">
        <div class="chart-empty-content">
            <div class="chart-empty-icon">📊</div>
            <div class="chart-empty-title">{title}</div>
            <div class="chart-empty-message">{message}</div>
        </div>
    </div>
    """


def _amount_to_color(amount: float) -> str:
    """Map amount to a color gradient."""
    if amount > 100000:
        return '#F44336'
    elif amount > 50000:
        return '#FF9800'
    elif amount > 10000:
        return '#4CAF50'
    return '#2E75B6'
