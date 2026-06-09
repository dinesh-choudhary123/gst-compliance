"""JSON report generation for data export."""

import json
from datetime import datetime
from typing import Any, Optional


def generate_json_report(data: dict, output_path: str, pretty: bool = True) -> str:
    """Export data as JSON file."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "taxflow_ai_version": "1.0.0",
        "data": data,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2 if pretty else None, default=str, ensure_ascii=False)

    return output_path


def export_invoices_json(invoices: list[dict], output_path: str) -> str:
    """Export invoices as JSON."""
    return generate_json_report({
        "report_type": "invoices",
        "count": len(invoices),
        "invoices": invoices,
    }, output_path)


def export_transactions_json(transactions: list[dict], output_path: str) -> str:
    """Export bank transactions as JSON."""
    return generate_json_report({
        "report_type": "bank_transactions",
        "count": len(transactions),
        "transactions": transactions,
    }, output_path)


def export_anomalies_json(anomalies: list[dict], output_path: str) -> str:
    """Export anomalies as JSON."""
    return generate_json_report({
        "report_type": "anomalies",
        "count": len(anomalies),
        "anomalies": anomalies,
    }, output_path)


def export_comprehensive_json(
    invoices: list[dict],
    transactions: list[dict],
    anomalies: list[dict],
    gstr1: Optional[dict] = None,
    gstr3b: Optional[dict] = None,
    output_path: str = "",
) -> str:
    """Export comprehensive report as JSON."""
    if not output_path:
        output_path = f"/tmp/taxflow_comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    data = {
        "report_type": "comprehensive",
        "invoices": {
            "count": len(invoices),
            "data": invoices,
        },
        "transactions": {
            "count": len(transactions),
            "data": transactions,
        },
        "anomalies": {
            "count": len(anomalies),
            "data": anomalies,
        },
    }

    if gstr1:
        data["gstr1"] = gstr1
    if gstr3b:
        data["gstr3b"] = gstr3b

    return generate_json_report(data, output_path)
