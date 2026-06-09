"""Main agent orchestrator that coordinates all AI agents.

Uses LangChain to create a structured, multi-step agentic workflow.
"""

import json
import re
from datetime import datetime
from typing import Any, Optional

from app.agents.extractor import DocumentExtractor
from app.agents.reconciler import ReconcilerAgent
from app.agents.itc_matcher import ITCMatcherAgent
from app.agents.gst_returns import GSTRReturnsAgent
from app.agents.anomaly import AnomalyDetector
from app.database import (
    save_chat_message,
    get_chat_history,
)
from app.ollama_client import TaxFlowOllama
from app.prompts import get_prompt


class AgentOrchestrator:
    """Orchestrates the multi-step agentic workflow."""

    def __init__(self, ollama_client: TaxFlowOllama):
        self.llm = ollama_client
        self.extractor = DocumentExtractor(ollama_client)
        self.reconciler = ReconcilerAgent(ollama_client)
        self.itc_matcher = ITCMatcherAgent(ollama_client)
        self.gst_returns = GSTRReturnsAgent(ollama_client)
        self.anomaly_detector = AnomalyDetector(ollama_client)
        self.current_project_id: Optional[str] = None

    def set_project(self, project_id: str):
        """Set the active project."""
        self.current_project_id = project_id

    def process_message(self, message: str, project_id: Optional[str] = None) -> dict[str, Any]:
        """Process a user message and return the response.

        This is the main entry point for the AI chat system.
        It determines the intent and delegates to the appropriate agent.
        """
        pid = project_id or self.current_project_id
        if not pid:
            return {
                "response": "Please select or create a project first to start working with documents.",
                "actions_taken": [],
            }

        # Save user message
        save_chat_message(pid, "user", message)

        # Detect intent
        intent = self._detect_intent(message)

        # Get chat history for context
        history = get_chat_history(pid, limit=20)

        actions_taken = []
        response = ""

        if intent == "analyze_documents":
            result = self._handle_document_analysis(pid, message)
            actions_taken = result.get("actions", [])
            response = result.get("response", "")

        elif intent == "reconcile":
            result = self._handle_reconciliation(pid, message)
            actions_taken = result.get("actions", [])
            response = result.get("response", "")

        elif intent == "itc_matching":
            result = self._handle_itc_matching(pid, message)
            actions_taken = result.get("actions", [])
            response = result.get("response", "")

        elif intent == "generate_gstr1":
            result = self._handle_gstr1(pid, message)
            actions_taken = result.get("actions", [])
            response = result.get("response", "")

        elif intent == "generate_gstr3b":
            result = self._handle_gstr3b(pid, message)
            actions_taken = result.get("actions", [])
            response = result.get("response", "")

        elif intent == "check_anomalies":
            result = self._handle_anomaly_check(pid, message)
            actions_taken = result.get("actions", [])
            response = result.get("response", "")

        elif intent == "financial_summary":
            result = self._handle_financial_summary(pid, message)
            actions_taken = result.get("actions", [])
            response = result.get("response", "")

        else:
            # General chat - use LLM directly with context
            response = self._handle_general_chat(pid, message, history)

        # Save assistant response
        save_chat_message(pid, "assistant", response, {"actions_taken": actions_taken})

        return {
            "response": response,
            "actions_taken": actions_taken,
        }

    def _detect_intent(self, message: str) -> str:
        """Detect the user's intent from their message."""
        msg_lower = message.lower()

        # Intent detection keywords
        intent_patterns = {
            "analyze_documents": [
                "analyze", "extract", "process", "upload", "document", "invoice",
                "read file", "check file", "what's in", "show me the data",
            ],
            "reconcile": [
                "reconcile", "reconcil", "match payment", "bank statement",
                "payment matching", "outstanding",
            ],
            "itc_matching": [
                "itc", "input tax credit", "credit matching", "itc eligible",
                "claim itc",
            ],
            "generate_gstr1": [
                "gstr-1", "gstr1", "gstr 1", "generate return", "outward supply",
            ],
            "generate_gstr3b": [
                "gstr-3b", "gstr3b", "gstr 3b", "summary return", "monthly return",
            ],
            "check_anomalies": [
                "anomaly", "flag", "issue", "problem", "error", "mismatch",
                "discrepancy", "suspicious", "unusual",
            ],
            "financial_summary": [
                "summary", "p&l", "profit", "loss", "financial", "overview",
                "dashboard", "report",
            ],
        }

        # Score each intent
        scores = {}
        for intent, patterns in intent_patterns.items():
            score = sum(1 for p in patterns if p in msg_lower)
            if score > 0:
                scores[intent] = score

        if scores:
            return max(scores, key=scores.get)
        return "general"

    def _handle_document_analysis(self, project_id: str, message: str) -> dict:
        """Handle document analysis requests."""
        from app.database import get_documents

        documents = get_documents(project_id)
        if not documents:
            return {
                "response": "No documents uploaded yet. Please upload invoices or bank statements first using the file upload area.",
                "actions": [],
            }

        # Process each unprocessed document
        actions = []
        all_results = []

        for doc in documents:
            if not doc["processed"]:
                result = self.extractor.process_document(
                    project_id=project_id,
                    document_id=doc["id"],
                    file_path=doc["file_path"],
                    filename=doc["filename"],
                    doc_type=doc["doc_type"],
                )
                all_results.append(result)
                actions.append(f"Extracted data from {doc['filename']}")

        # If no new documents to process, summarize what we have
        if not actions:
            # Get existing data for summary
            from app.database import get_invoices
            invoices = get_invoices(project_id)
            if invoices:
                total_taxable = sum(i["taxable_amount"] for i in invoices)
                total_tax = sum(i["cgst_amount"] + i["sgst_amount"] + i["igst_amount"] for i in invoices)
                actions.append(f"Analyzed {len(invoices)} existing invoices")

                response = self.llm.chat([
                    {"role": "system", "content": get_prompt("gst_analysis")},
                    {"role": "user", "content": f"""Summarize the following invoice data for the client project.
Number of invoices: {len(invoices)}
Total taxable amount: ₹{total_taxable:,.2f}
Total tax amount: ₹{total_tax:,.2f}
Invoices: {json.dumps(invoices, indent=2, default=str)[:4000]}

Provide a clear summary in plain text with key insights and any observations."""}
                ])
                return {"response": response, "actions": actions}

            return {
                "response": "Documents are uploaded but data extraction hasn't completed yet. Try uploading new documents.",
                "actions": [],
            }

        # Generate comprehensive response from extraction results
        invoices_found = [r for r in all_results if r.get("type") == "invoice"]
        transactions_found = [r for r in all_results if r.get("type") == "bank_transaction"]

        summary_parts = []
        if invoices_found:
            inv_count = len(invoices_found)
            total_amt = sum(r.get("total_amount", 0) for r in invoices_found)
            summary_parts.append(f"📄 Extracted {inv_count} invoice(s) totaling ₹{total_amt:,.2f}")
        if transactions_found:
            tx_count = len(transactions_found)
            summary_parts.append(f"🏦 Extracted {tx_count} bank transactions")

        response = self.llm.chat([
            {"role": "system", "content": get_prompt("gst_analysis")},
            {"role": "user", "content": f"""The following documents were just processed for a client project.
Results: {json.dumps(all_results, indent=2, default=str)[:5000]}

{' '.join(summary_parts)}

Provide a clear summary of what was extracted, key observations, and suggested next steps (like reconciliation or ITC matching)."""}
        ])

        return {"response": response, "actions": actions}

    def _handle_reconciliation(self, project_id: str, message: str) -> dict:
        """Handle bank reconciliation request."""
        result = self.reconciler.reconcile(project_id, message)
        return result

    def _handle_itc_matching(self, project_id: str, message: str) -> dict:
        """Handle ITC matching request."""
        result = self.itc_matcher.match_itc(project_id, message)
        return result

    def _handle_gstr1(self, project_id: str, message: str) -> dict:
        """Handle GSTR-1 generation request."""
        result = self.gst_returns.generate_gstr1(project_id, message)
        return result

    def _handle_gstr3b(self, project_id: str, message: str) -> dict:
        """Handle GSTR-3B generation request."""
        result = self.gst_returns.generate_gstr3b(project_id, message)
        return result

    def _handle_anomaly_check(self, project_id: str, message: str) -> dict:
        """Handle anomaly detection request."""
        result = self.anomaly_detector.detect(project_id, message)
        return result

    def _handle_financial_summary(self, project_id: str, message: str) -> dict:
        """Handle financial summary request."""
        from app.database import get_invoices, get_bank_transactions

        invoices = get_invoices(project_id)
        transactions = get_bank_transactions(project_id)

        summary_data = {
            "total_invoices": len(invoices),
            "total_taxable_amount": sum(i["taxable_amount"] for i in invoices),
            "total_tax": sum(i["cgst_amount"] + i["sgst_amount"] + i["igst_amount"] for i in invoices),
            "total_invoice_amount": sum(i["total_amount"] for i in invoices),
            "total_credits": sum(t["credit"] for t in transactions),
            "total_debits": sum(t["debit"] for t in transactions),
            "transaction_count": len(transactions),
        }

        response = self.llm.chat([
            {"role": "system", "content": "You are a financial analyst specializing in Indian business taxation."},
            {"role": "user", "content": f"""Generate a financial summary for this client based on the following data:
{json.dumps(summary_data, indent=2)}

Include: revenue overview, tax summary, cash flow indicators, and key recommendations."""}
        ])

        return {"response": response, "actions": [f"Generated financial summary from {summary_data['total_invoices']} invoices and {summary_data['transaction_count']} transactions"]}

    def _handle_general_chat(self, project_id: str, message: str, history: list[dict]) -> str:
        """Handle general conversation using LLM with context."""
        # Build context from project data
        from app.database import get_invoices, get_bank_transactions, get_anomalies, get_documents

        invoices = get_invoices(project_id)
        transactions = get_bank_transactions(project_id)
        anomalies = get_anomalies(project_id, unresolved_only=True)
        documents = get_documents(project_id)

        context = f"""
Current Project Context:
- Documents uploaded: {len(documents)}
- Invoices extracted: {len(invoices)}
- Bank transactions: {len(transactions)}
- Unresolved anomalies: {len(anomalies)}

Recent chat history:
"""
        for msg in history[-6:]:
            context += f"\n{msg['role'].upper()}: {msg['content'][:200]}"

        response = self.llm.chat([
            {"role": "system", "content": get_prompt("system")},
            {"role": "user", "content": f"Context:\n{context}\n\nUser message: {message}"}
        ])

        return response

    def generate_system_report(self, project_id: str, report_type: str = "comprehensive") -> str:
        """Generate a comprehensive system report."""
        from app.database import get_invoices, get_bank_transactions, get_anomalies, get_documents

        invoices = get_invoices(project_id)
        transactions = get_bank_transactions(project_id)
        anomalies = get_anomalies(project_id)
        documents = get_documents(project_id)

        data = {
            "project_id": project_id,
            "report_type": report_type,
            "documents": documents,
            "invoices": invoices,
            "transactions": transactions,
            "anomalies": anomalies,
            "generated_at": datetime.now().isoformat(),
        }

        response = self.llm.chat([
            {"role": "system", "content": get_prompt("system")},
            {"role": "user", "content": f"""Generate a {'comprehensive' if report_type == 'comprehensive' else 'summary'} report for the client based on this data:
{json.dumps(data, indent=2, default=str)[:6000]}

Include: document summary, invoice analysis, bank reconciliation status, ITC status, anomalies found, and recommendations."""}
        ])

        return response
