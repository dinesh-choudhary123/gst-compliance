"""Pydantic models for TaxFlow AI."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseModel):
    id: str
    username: str
    password_hash: str
    role: UserRole = UserRole.USER
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True


class ClientProject(BaseModel):
    id: str
    user_id: str
    name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: str = ""


class DocumentType(str, Enum):
    INVOICE = "invoice"
    BANK_STATEMENT = "bank_statement"
    GSTR_1 = "gstr1"
    GSTR_3B = "gstr3b"
    E_WAY_BILL = "e_way_bill"
    OTHER = "other"


class Document(BaseModel):
    id: str
    project_id: str
    filename: str
    file_path: str
    doc_type: DocumentType = DocumentType.OTHER
    uploaded_at: datetime = Field(default_factory=datetime.now)
    processed: bool = False
    page_count: int = 0
    file_size_bytes: int = 0


class Invoice(BaseModel):
    """Extracted invoice data."""
    id: str
    project_id: str
    document_id: str
    invoice_number: str
    invoice_date: Optional[datetime] = None
    seller_name: str = ""
    seller_gstin: str = ""
    buyer_name: str = ""
    buyer_gstin: str = ""
    hsn_codes: list[dict] = Field(default_factory=list)  # [{code, description, quantity, rate, amount}]
    taxable_amount: float = 0.0
    cgst_rate: float = 0.0
    cgst_amount: float = 0.0
    sgst_rate: float = 0.0
    sgst_amount: float = 0.0
    igst_rate: float = 0.0
    igst_amount: float = 0.0
    cess_amount: float = 0.0
    total_amount: float = 0.0
    reverse_charge: bool = False
    place_of_supply: str = ""
    irn: Optional[str] = None
    raw_data: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class BankTransaction(BaseModel):
    """Extracted bank transaction."""
    id: str
    project_id: str
    document_id: str
    transaction_date: datetime
    narration: str = ""
    debit: float = 0.0
    credit: float = 0.0
    balance: float = 0.0
    cheque_no: Optional[str] = None
    reference: Optional[str] = None
    matched_to_invoice_id: Optional[str] = None
    match_confidence: float = 0.0
    raw_data: dict = Field(default_factory=dict)


class ITCMatch(BaseModel):
    """ITC matching result."""
    id: str
    project_id: str
    invoice_id: str
    gstr_2a_reference: Optional[str] = None
    itc_eligible: bool = False
    itc_amount: float = 0.0
    match_status: str = "pending"  # matched, mismatch, missing
    remarks: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class GSTR1Data(BaseModel):
    """GSTR-1 return data."""
    period: str  # MMYYYY
    project_id: str
    invoices: list[dict] = Field(default_factory=list)
    b2b_invoices: list[dict] = Field(default_factory=list)
    b2c_invoices: list[dict] = Field(default_factory=list)
    credit_notes: list[dict] = Field(default_factory=list)
    debit_notes: list[dict] = Field(default_factory=list)
    exports: list[dict] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)


class GSTR3BData(BaseModel):
    """GSTR-3B return data."""
    period: str  # MMYYYY
    project_id: str
    turnover: dict = Field(default_factory=dict)
    itc_claimed: dict = Field(default_factory=dict)
    tax_payable: dict = Field(default_factory=dict)
    interest: dict = Field(default_factory=dict)
    summary: dict = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)


class Anomaly(BaseModel):
    """Detected anomaly/issue."""
    id: str
    project_id: str
    severity: str = "medium"  # high, medium, low
    category: str = ""  # gst_mismatch, missing_invoice, itc_issue, etc.
    title: str
    description: str
    suggestion: str = ""
    source_document_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    resolved: bool = False


class ChatMessage(BaseModel):
    """Chat message in the UI."""
    id: str
    project_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)


class ProcessingResult(BaseModel):
    """Result of a document processing operation."""
    success: bool
    message: str
    data: dict = Field(default_factory=dict)
    anomalies: list[Anomaly] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
