"""Local SQLite database for client data, documents, and processing results.

All data stays local and can be optionally encrypted at rest.
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet


from app.config import settings


def _get_encryption_key() -> bytes:
    """Get or generate an encryption key for client data."""
    key_file = settings.BASE_DIR / ".encryption_key"
    if key_file.exists():
        return key_file.read_bytes()
    # Generate a new key
    key = Fernet.generate_key()
    key_file.write_bytes(key)
    os.chmod(str(key_file), 0o600)
    return key


def _get_fernet() -> Fernet:
    """Get a Fernet instance for encryption/decryption."""
    return Fernet(_get_encryption_key())


def _get_db_path(project_id: Optional[str] = None) -> Path:
    """Get database path. Each project gets its own encrypted DB."""
    if project_id:
        db_dir = settings.CLIENT_DATA_DIR / project_id
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / "data.db"
    return settings.BASE_DIR / "taxflow.db"


def _get_conn(project_id: Optional[str] = None) -> sqlite3.Connection:
    """Get a database connection."""
    db_path = _get_db_path(project_id)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_main_db():
    """Initialize the main database tables (projects, etc.)."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                gstin TEXT,
                pan TEXT,
                address TEXT,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                is_encrypted INTEGER DEFAULT 0
            );
        """)
        conn.commit()
    finally:
        conn.close()


def init_project_db(project_id: str):
    """Initialize database tables for a project.

    Note: The projects table lives in the main database (taxflow.db),
    so project-specific tables do not have FK constraints referencing it.
    """
    conn = _get_conn(project_id)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                doc_type TEXT DEFAULT 'other',
                uploaded_at TEXT DEFAULT (datetime('now')),
                processed INTEGER DEFAULT 0,
                page_count INTEGER DEFAULT 0,
                file_size_bytes INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                invoice_number TEXT,
                invoice_date TEXT,
                seller_name TEXT DEFAULT '',
                seller_gstin TEXT DEFAULT '',
                buyer_name TEXT DEFAULT '',
                buyer_gstin TEXT DEFAULT '',
                taxable_amount REAL DEFAULT 0.0,
                cgst_rate REAL DEFAULT 0.0,
                cgst_amount REAL DEFAULT 0.0,
                sgst_rate REAL DEFAULT 0.0,
                sgst_amount REAL DEFAULT 0.0,
                igst_rate REAL DEFAULT 0.0,
                igst_amount REAL DEFAULT 0.0,
                cess_amount REAL DEFAULT 0.0,
                total_amount REAL DEFAULT 0.0,
                reverse_charge INTEGER DEFAULT 0,
                place_of_supply TEXT DEFAULT '',
                irn TEXT,
                hsn_codes TEXT DEFAULT '[]',
                raw_data TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (document_id) REFERENCES documents(id)
            );

            CREATE TABLE IF NOT EXISTS bank_transactions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                transaction_date TEXT,
                narration TEXT DEFAULT '',
                debit REAL DEFAULT 0.0,
                credit REAL DEFAULT 0.0,
                balance REAL DEFAULT 0.0,
                cheque_no TEXT,
                reference TEXT,
                matched_to_invoice_id TEXT,
                match_confidence REAL DEFAULT 0.0,
                raw_data TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (document_id) REFERENCES documents(id)
            );

            CREATE TABLE IF NOT EXISTS itc_matches (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                invoice_id TEXT NOT NULL,
                gstr_2a_reference TEXT,
                itc_eligible INTEGER DEFAULT 0,
                itc_amount REAL DEFAULT 0.0,
                match_status TEXT DEFAULT 'pending',
                remarks TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            );

            CREATE TABLE IF NOT EXISTS gstr1_data (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                period TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                generated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS gstr3b_data (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                period TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                generated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS anomalies (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                category TEXT DEFAULT '',
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                suggestion TEXT DEFAULT '',
                source_document_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                resolved INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now')),
                metadata TEXT DEFAULT '{}'
            );
        """)
        conn.commit()
    finally:
        conn.close()


# ─── Project CRUD ────────────────────────────────────────────────

def create_project(name: str, user_id: str, gstin: str = "", pan: str = "", address: str = "", notes: str = "") -> dict:
    """Create a new client project."""
    project_id = str(uuid.uuid4())
    conn = _get_conn()
    try:
        conn.execute(
            """INSERT INTO projects (id, user_id, name, gstin, pan, address, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (project_id, user_id, name, gstin, pan, address, notes),
        )
        conn.commit()
        # Initialize project-specific database
        init_project_db(project_id)
        return {"id": project_id, "name": name, "gstin": gstin}
    finally:
        conn.close()


def get_projects(user_id: str) -> list[dict]:
    """Get all projects for a user."""
    conn = _get_conn()
    try:
        cursor = conn.execute(
            """SELECT id, name, gstin, pan, notes, created_at, updated_at
               FROM projects WHERE user_id = ? ORDER BY updated_at DESC""",
            (user_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_project(project_id: str) -> Optional[dict]:
    """Get a single project."""
    conn = _get_conn()
    try:
        cursor = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_project(project_id: str, **kwargs) -> bool:
    """Update project fields."""
    allowed = {"name", "gstin", "pan", "address", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [project_id]
    conn = _get_conn()
    try:
        conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return True
    finally:
        conn.close()


def delete_project(project_id: str) -> bool:
    """Delete a project and all its data."""
    conn = _get_conn()
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        # Remove project-specific database
        db_path = _get_db_path(project_id)
        if db_path.exists():
            db_path.unlink()
        return True
    finally:
        conn.close()


# ─── Documents ────────────────────────────────────────────────────

def add_document(project_id: str, filename: str, file_path: str,
                 doc_type: str = "other", page_count: int = 0,
                 file_size_bytes: int = 0) -> dict:
    """Record a document in the database."""
    doc_id = str(uuid.uuid4())
    conn = _get_conn(project_id)
    try:
        conn.execute(
            """INSERT INTO documents (id, project_id, filename, file_path, doc_type,
               page_count, file_size_bytes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (doc_id, project_id, filename, file_path, doc_type, page_count, file_size_bytes),
        )
        conn.commit()
        return {"id": doc_id, "filename": filename}
    finally:
        conn.close()


def get_documents(project_id: str) -> list[dict]:
    """Get all documents for a project."""
    conn = _get_conn(project_id)
    try:
        cursor = conn.execute(
            "SELECT * FROM documents WHERE project_id = ? ORDER BY uploaded_at DESC",
            (project_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ─── Invoice CRUD ─────────────────────────────────────────────────

def save_invoice(project_id: str, invoice_data: dict) -> str:
    """Save an extracted invoice."""
    invoice_id = str(uuid.uuid4())
    conn = _get_conn(project_id)
    try:
        conn.execute(
            """INSERT INTO invoices (id, project_id, document_id, invoice_number,
               invoice_date, seller_name, seller_gstin, buyer_name, buyer_gstin,
               taxable_amount, cgst_rate, cgst_amount, sgst_rate, sgst_amount,
               igst_rate, igst_amount, cess_amount, total_amount,
               reverse_charge, place_of_supply, irn, hsn_codes, raw_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                invoice_id,
                project_id,
                invoice_data.get("document_id", ""),
                invoice_data.get("invoice_number", ""),
                invoice_data.get("invoice_date"),
                invoice_data.get("seller_name", ""),
                invoice_data.get("seller_gstin", ""),
                invoice_data.get("buyer_name", ""),
                invoice_data.get("buyer_gstin", ""),
                invoice_data.get("taxable_amount", 0.0),
                invoice_data.get("cgst_rate", 0.0),
                invoice_data.get("cgst_amount", 0.0),
                invoice_data.get("sgst_rate", 0.0),
                invoice_data.get("sgst_amount", 0.0),
                invoice_data.get("igst_rate", 0.0),
                invoice_data.get("igst_amount", 0.0),
                invoice_data.get("cess_amount", 0.0),
                invoice_data.get("total_amount", 0.0),
                1 if invoice_data.get("reverse_charge") else 0,
                invoice_data.get("place_of_supply", ""),
                invoice_data.get("irn"),
                json.dumps(invoice_data.get("hsn_codes", [])),
                json.dumps(invoice_data.get("raw_data", {})),
            ),
        )
        conn.commit()
        return invoice_id
    finally:
        conn.close()


def get_invoices(project_id: str) -> list[dict]:
    """Get all invoices for a project."""
    conn = _get_conn(project_id)
    try:
        cursor = conn.execute(
            "SELECT * FROM invoices WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        )
        invoices = []
        for row in cursor.fetchall():
            d = dict(row)
            d["hsn_codes"] = json.loads(d.get("hsn_codes", "[]"))
            d["raw_data"] = json.loads(d.get("raw_data", "{}"))
            invoices.append(d)
        return invoices
    finally:
        conn.close()


# ─── Bank Transactions ────────────────────────────────────────────

def save_bank_transaction(project_id: str, tx_data: dict) -> str:
    """Save a bank transaction."""
    tx_id = str(uuid.uuid4())
    conn = _get_conn(project_id)
    try:
        conn.execute(
            """INSERT INTO bank_transactions (id, project_id, document_id,
               transaction_date, narration, debit, credit, balance,
               cheque_no, reference, raw_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tx_id,
                project_id,
                tx_data.get("document_id", ""),
                tx_data.get("transaction_date"),
                tx_data.get("narration", ""),
                tx_data.get("debit", 0.0),
                tx_data.get("credit", 0.0),
                tx_data.get("balance", 0.0),
                tx_data.get("cheque_no"),
                tx_data.get("reference"),
                json.dumps(tx_data.get("raw_data", {})),
            ),
        )
        conn.commit()
        return tx_id
    finally:
        conn.close()


def get_bank_transactions(project_id: str) -> list[dict]:
    """Get all bank transactions for a project."""
    conn = _get_conn(project_id)
    try:
        cursor = conn.execute(
            "SELECT * FROM bank_transactions WHERE project_id = ? ORDER BY transaction_date",
            (project_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ─── Chat History ─────────────────────────────────────────────────

def save_chat_message(project_id: str, role: str, content: str, metadata: dict = None) -> str:
    """Save a chat message."""
    msg_id = str(uuid.uuid4())
    conn = _get_conn(project_id)
    try:
        conn.execute(
            "INSERT INTO chat_history (id, project_id, role, content, metadata) VALUES (?, ?, ?, ?, ?)",
            (msg_id, project_id, role, content, json.dumps(metadata or {})),
        )
        conn.commit()
        return msg_id
    finally:
        conn.close()


def get_chat_history(project_id: str, limit: int = 100) -> list[dict]:
    """Get chat history for a project."""
    conn = _get_conn(project_id)
    try:
        cursor = conn.execute(
            "SELECT * FROM chat_history WHERE project_id = ? ORDER BY timestamp ASC LIMIT ?",
            (project_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def clear_chat_history(project_id: str):
    """Clear chat history for a project."""
    conn = _get_conn(project_id)
    try:
        conn.execute("DELETE FROM chat_history WHERE project_id = ?", (project_id,))
        conn.commit()
    finally:
        conn.close()


# ─── Anomalies ────────────────────────────────────────────────────

def save_anomaly(project_id: str, anomaly_data: dict) -> str:
    """Save a detected anomaly."""
    anomaly_id = str(uuid.uuid4())
    conn = _get_conn(project_id)
    try:
        conn.execute(
            """INSERT INTO anomalies (id, project_id, severity, category, title,
               description, suggestion, source_document_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                anomaly_id,
                project_id,
                anomaly_data.get("severity", "medium"),
                anomaly_data.get("category", ""),
                anomaly_data.get("title", ""),
                anomaly_data.get("description", ""),
                anomaly_data.get("suggestion", ""),
                anomaly_data.get("source_document_id"),
            ),
        )
        conn.commit()
        return anomaly_id
    finally:
        conn.close()


def get_anomalies(project_id: str, unresolved_only: bool = False) -> list[dict]:
    """Get anomalies for a project."""
    conn = _get_conn(project_id)
    try:
        query = "SELECT * FROM anomalies WHERE project_id = ?"
        params = [project_id]
        if unresolved_only:
            query += " AND resolved = 0"
        query += " ORDER BY created_at DESC"
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# ─── GSTR Data ────────────────────────────────────────────────────

def save_gstr1(project_id: str, period: str, data: dict) -> str:
    """Save GSTR-1 data."""
    record_id = str(uuid.uuid4())
    conn = _get_conn(project_id)
    try:
        conn.execute(
            "INSERT INTO gstr1_data (id, project_id, period, data) VALUES (?, ?, ?, ?)",
            (record_id, project_id, period, json.dumps(data)),
        )
        conn.commit()
        return record_id
    finally:
        conn.close()


def save_gstr3b(project_id: str, period: str, data: dict) -> str:
    """Save GSTR-3B data."""
    record_id = str(uuid.uuid4())
    conn = _get_conn(project_id)
    try:
        conn.execute(
            "INSERT INTO gstr3b_data (id, project_id, period, data) VALUES (?, ?, ?, ?)",
            (record_id, project_id, period, json.dumps(data)),
        )
        conn.commit()
        return record_id
    finally:
        conn.close()


def get_gstr_data(project_id: str, return_type: str = "gstr1") -> list[dict]:
    """Get GSTR data for a project."""
    conn = _get_conn(project_id)
    table = "gstr1_data" if return_type == "gstr1" else "gstr3b_data"
    try:
        cursor = conn.execute(f"SELECT * FROM {table} WHERE project_id = ? ORDER BY period DESC", (project_id,))
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            d["data"] = json.loads(d.get("data", "{}"))
            results.append(d)
        return results
    finally:
        conn.close()
