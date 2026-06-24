"""GST Rule Knowledge Base with local RAG capabilities.

Provides a searchable knowledge base of GST rules, sections, notifications,
and judicial precedents using local embeddings for semantic search.
All data stays local - no external API calls.
"""

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.config import settings

# ================================================================
# GST KNOWLEDGE BASE DATA
# ================================================================

GST_RULES = [
    # Registration
    {"id": "sec22", "section": "Section 22", "title": "Person liable to be registered",
     "category": "Registration", "subcategory": "Liability",
     "content": "Every supplier making taxable supply of goods or services with aggregate turnover exceeding Rs. 40 lakhs (Rs. 20 lakhs for special category states) in a financial year is liable to be registered under GST.",
     "keywords": "registration, turnover, threshold, 40 lakhs, 20 lakhs, liable"},
    {"id": "sec23", "section": "Section 23", "title": "Persons not liable for registration",
     "category": "Registration", "subcategory": "Exemptions",
     "content": "Agriculturalists supplying produce out of cultivation, persons supplying only exempt goods/services, and persons under reverse charge are not liable for GST registration.",
     "keywords": "exempt, registration, agriculture, reverse charge, not liable"},
    {"id": "sec24", "section": "Section 24", "title": "Compulsory registration",
     "category": "Registration", "subcategory": "Compulsory",
     "content": "Inter-state suppliers, casual taxable persons, non-resident taxable persons, TDS deductors, e-commerce operators, and OIDAR service providers must register compulsorily regardless of turnover.",
     "keywords": "compulsory registration, inter-state, e-commerce, OIDAR, casual, non-resident"},
    
    # Supply
    {"id": "sec7", "section": "Section 7", "title": "Scope of supply",
     "category": "Supply", "subcategory": "Definition",
     "content": "Supply includes all forms of supply of goods or services made for consideration in the course of business. Schedule I activities without consideration are also treated as supply.",
     "keywords": "supply, scope, consideration, business, schedule I"},
    {"id": "sec8", "section": "Section 8", "title": "Composite and mixed supply",
     "category": "Supply", "subcategory": "Types",
     "content": "Composite supply is a supply comprising two or more goods/services naturally bundled. Mixed supply is two or more supplies made together for a single price. The principal supply determines the tax rate for composite supply.",
     "keywords": "composite supply, mixed supply, bundled, principal supply, tax rate"},
    {"id": "sch1", "section": "Schedule I", "title": "Activities treated as supply without consideration",
     "category": "Supply", "subcategory": "Deemed Supply",
     "content": "Permanent transfer of business assets, supply between related persons, and branch transfers between states are treated as supply even without consideration.",
     "keywords": "deemed supply, without consideration, branch transfer, related person, assets"},
    
    # Time & Value
    {"id": "sec31", "section": "Section 31", "title": "Tax invoice",
     "category": "Invoicing", "subcategory": "Invoice",
     "content": "A registered person supplying taxable goods must issue a tax invoice within 30 days. For continuous supply, invoice must be issued within 30 days of each event. E-invoicing is mandatory for aggregate turnover exceeding Rs. 5 crores.",
     "keywords": "tax invoice, 30 days, continuous supply, e-invoice, 5 crores"},
    {"id": "sec34", "section": "Section 34", "title": "Credit and debit notes",
     "category": "Invoicing", "subcategory": "Adjustments",
     "content": "A credit note can be issued if invoice value exceeds taxable value or tax charged exceeds tax payable. A debit note is issued for the reverse. Both must link to the original invoice.",
     "keywords": "credit note, debit note, adjustment, invoice correction, refund"},
    
    # Input Tax Credit
    {"id": "sec16", "section": "Section 16", "title": "Eligibility and conditions for taking ITC",
     "category": "ITC", "subcategory": "Eligibility",
     "content": "ITC can be claimed if: (a) possess tax invoice, (b) goods/services received, (c) tax charged actually paid to government, (d) return filed. ITC must be claimed by November 30th of the following FY or annual return filing date.",
     "keywords": "ITC eligibility, conditions, invoice, receipt, payment, deadline, November 30"},
    {"id": "sec17", "section": "Section 17", "title": "Apportionment of ITC and blocked credits",
     "category": "ITC", "subcategory": "Blocked Credit",
     "content": "ITC is blocked for: motor vehicles (capacity < 13 persons), food & beverages, beauty services, health services, membership fees, rent-a-cab, life/health insurance (if employer provides exemption). ITC for common inputs must be reversed proportionally.",
     "keywords": "blocked credit, section 17(5), motor vehicle, food, beverages, membership, proportional reversal"},
    {"id": "sec18", "section": "Section 18", "title": "ITC in special circumstances",
     "category": "ITC", "subcategory": "Special Cases",
     "content": "On switching from composition to regular scheme, ITC on stock held can be claimed. When exempt supply becomes taxable, ITC on inputs used in exempt supply can be claimed. On cancellation of registration, ITC must be reversed.",
     "keywords": "composition to regular, ITC on stock, exempt to taxable, cancellation reversal"},
    {"id": "rule42", "section": "Rule 42", "title": "ITC reversal for exempt supplies (Rule 42)",
     "category": "ITC", "subcategory": "Reversal",
     "content": "ITC attributable to exempt supplies must be reversed monthly. The reversal is calculated as: (Turnover of exempt supplies / Total turnover) × Total ITC. Common ITC is also reversed proportionally.",
     "keywords": "ITC reversal, rule 42, exempt supply, proportionate reversal, common credit"},
    {"id": "rule43", "section": "Rule 43", "title": "ITC reversal for capital goods",
     "category": "ITC", "subcategory": "Capital Goods",
     "content": "ITC on capital goods used in taxable and exempt supplies must be reversed at 5% per quarter for 5 years. Full ITC reversal is required if capital goods are disposed or used exclusively in exempt supply.",
     "keywords": "capital goods, reversal, 5%, quarterly, 5 years, exempt supply"},
    {"id": "note_180_days", "section": "Section 16(2)", "title": "ITC reversal for unpaid invoices (180 days)",
     "category": "ITC", "subcategory": "Time Limit",
     "content": "If payment is not made to the supplier within 180 days from invoice date, the ITC claimed must be reversed with interest. ITC can be reclaimed when payment is actually made.",
     "keywords": "180 days, ITC reversal, unpaid invoice, payment, reclaim, interest"},
    
    # Returns
    {"id": "sec37", "section": "Section 37", "title": "GSTR-1 - Furnishing details of outward supplies",
     "category": "Returns", "subcategory": "GSTR-1",
     "content": "GSTR-1 must be filed by the 11th of the following month. Contains details of all outward supplies (B2B, B2C, exports, credit/debit notes). Taxpayers with turnover up to Rs. 1.5 crores can file quarterly.",
     "keywords": "GSTR-1, outward supply, 11th, monthly, quarterly, 1.5 crores"},
    {"id": "sec39", "section": "Section 39", "title": "GSTR-3B - Monthly return",
     "category": "Returns", "subcategory": "GSTR-3B",
     "content": "GSTR-3B is a simplified monthly return due by the 20th of the following month. It contains summary of outward supplies, ITC claimed, and tax paid through cash/credit ledger.",
     "keywords": "GSTR-3B, monthly return, 20th, summary, tax payment, ITC"},
    {"id": "sec44", "section": "Section 44", "title": "GSTR-9 - Annual return",
     "category": "Returns", "subcategory": "Annual",
     "content": "GSTR-9 is an annual return consolidating all monthly/quarterly returns. Due by December 31st of the following financial year. Taxpayers with turnover up to Rs. 2 crores can file simplified GSTR-9.",
     "keywords": "GSTR-9, annual return, December 31, consolidation, simplified"},
    {"id": "sec45", "section": "Section 45", "title": "GSTR-10 - Final return",
     "category": "Returns", "subcategory": "Final",
     "content": "GSTR-10 (final return) must be filed within 3 months of cancellation or surrender of GST registration. It includes details of stock, outstanding liabilities, and pending ITC.",
     "keywords": "GSTR-10, final return, cancellation, surrender, 3 months"},
    
    # Payment
    {"id": "sec49", "section": "Section 49", "title": "Payment of tax",
     "category": "Payment", "subcategory": "Electronic Ledger",
     "content": "Every registered person maintains electronic liability, credit, and cash ledgers. Tax can be paid first from the credit ledger (ITC) starting from IGST. PMT-06 is the challan for tax payment.",
     "keywords": "payment, electronic ledger, liability, cash, credit, PMT-06, challan"},
    {"id": "sec50", "section": "Section 50", "title": "Interest on delayed payment",
     "category": "Payment", "subcategory": "Interest",
     "content": "Interest at 18% per annum must be paid if tax is paid after the due date. Interest is calculated from the day after the due date to the date of payment. Net liability (after ITC) determines interest amount.",
     "keywords": "interest, 18%, delayed payment, due date, net liability, interest calculation"},
    
    # Assessment
    {"id": "sec59", "section": "Section 59", "title": "Self-assessment",
     "category": "Assessment", "subcategory": "Self",
     "content": "Every registered person must self-assess the tax payable and file returns accordingly. Returns are accepted without scrutiny by the department initially but can be selected for audit.",
     "keywords": "self-assessment, self-assess, return, audit, scrutiny"},
    {"id": "sec73", "section": "Section 73", "title": "Determination of tax not paid/short paid (non-fraud)",
     "category": "Assessment", "subcategory": "Non-Fraud",
     "content": "For non-fraud cases of non-payment or short payment, show cause notice must be issued within 33 months. Tax with 18% interest is payable. Penalty is 10% of tax or Rs. 10,000, whichever is higher.",
     "keywords": "section 73, non-fraud, short payment, show cause, 33 months, 10% penalty"},
    {"id": "sec74", "section": "Section 74", "title": "Determination of tax (fraud cases)",
     "category": "Assessment", "subcategory": "Fraud",
     "content": "For fraud cases, show cause notice must be issued within 54 months. Penalty is 100% of tax amount. Voluntary payment before notice reduces penalty to 15%; after notice but before order reduces to 25%.",
     "keywords": "section 74, fraud, 54 months, 100% penalty, voluntary payment, reduced penalty"},
    
    # Penalties
    {"id": "sec122", "section": "Section 122", "title": "Penalty for certain offences",
     "category": "Penalty", "subcategory": "General",
     "content": "Penalty of Rs. 10,000 or 10% of tax (whichever is higher) for: issuing invoice without supply, claiming excess ITC, failing to collect tax, transporting goods without documents, failing to file returns within 30 days.",
     "keywords": "penalty, 10,000, 10%, offences, without supply, excess ITC, no documents"},
    {"id": "sec125", "section": "Section 125", "title": "General penalty",
     "category": "Penalty", "subcategory": "General",
     "content": "For any contravention not specifically penalized, a penalty of up to Rs. 25,000 may be imposed by the proper officer.",
     "keywords": "general penalty, 25,000, contravention, proper officer"},
    
    # E-Way Bill
    {"id": "eway_rules", "section": "Rule 138", "title": "E-way bill rules",
     "category": "Compliance", "subcategory": "E-Way Bill",
     "content": "E-way bill is required for movement of goods exceeding Rs. 50,000 in value (single consignment value). Valid for: 100km-1 day, 100-300km-3 days, 300-500km-5 days, 500-1000km-10 days, >1000km-15 days.",
     "keywords": "e-way bill, movement, 50,000, validity, distance, consignment"},
    
    # E-Invoice
    {"id": "einv_rules", "section": "Notification", "title": "E-invoicing system",
     "category": "Compliance", "subcategory": "E-Invoice",
     "content": "E-invoicing is mandatory for B2B invoices for taxpayers with aggregate turnover exceeding Rs. 5 crores. IRN (Invoice Reference Number) must be obtained from the Invoice Registration Portal (IRP).",
     "keywords": "e-invoice, IRN, 5 crores, IRP, B2B, mandatory, Invoice Registration Portal"},
    
    # Composition
    {"id": "comp_rules", "section": "Section 10", "title": "Composition scheme",
     "category": "Registration", "subcategory": "Composition",
     "content": "Composition scheme for taxpayers with turnover up to Rs. 1.5 crores (Rs. 75 lakhs for special category states). Tax rates: 1% for manufacturers/traders, 6% for restaurants. No ITC available. Quarterly returns and tax payment.",
     "keywords": "composition, 1.5 crores, 1%, 6%, no ITC, quarterly, manufacturers, traders, restaurants"},
    
    # TDS/TCS
    {"id": "sec51", "section": "Section 51", "title": "TDS under GST",
     "category": "Payment", "subcategory": "TDS",
     "content": "Government departments, PSUs, and specified entities must deduct TDS at 2% (1% CGST + 1% SGST or 2% IGST) on payments to suppliers exceeding Rs. 2.5 lakhs per contract. TDS must be deposited by the 10th of the following month.",
     "keywords": "TDS, 2%, government, PSU, 2.5 lakhs, contract, 10th"},
    {"id": "sec52", "section": "Section 52", "title": "TCS under GST",
     "category": "Payment", "subcategory": "TCS",
     "content": "E-commerce operators must collect TCS at 1% (0.5% CGST + 0.5% SGST or 1% IGST) on net taxable supplies. TCS must be deposited by the 10th of the following month. Details in GSTR-8.",
     "keywords": "TCS, 1%, e-commerce, 10th, GSTR-8, net supplies"},
    
    # Refunds
    {"id": "sec54", "section": "Section 54", "title": "Refund of tax",
     "category": "Refund", "subcategory": "General",
     "content": "Refund may be claimed within 2 years from the relevant date. For zero-rated supplies, refund can be claimed without payment of IGST under bond/LUT (refund of accumulated ITC) or with payment of IGST. 90% provisional refund within 7 days.",
     "keywords": "refund, 2 years, zero-rated, LUT, bond, provisional, 90%, 7 days"},
    {"id": "sec56", "section": "Section 56", "title": "Interest on delayed refunds",
     "category": "Refund", "subcategory": "Interest",
     "content": "If refund is not granted within 60 days from the date of application, interest at 6% per annum is payable from the date of application until the date of refund.",
     "keywords": "refund interest, 6%, 60 days, delayed refund"},
    
    # Demand & Recovery
    {"id": "sec73_demand", "section": "Section 73", "title": "Demand for non-fraud cases",
     "category": "Demand", "subcategory": "Non-Fraud",
     "content": "Demand notice under Section 73: Show cause notice must be issued within 33 months from the due date of return or date of erroneous refund. Tax + 18% interest + 10% penalty (minimum Rs. 10,000).",
     "keywords": "demand, section 73, 33 months, show cause, interest, penalty"},
    {"id": "sec74_demand", "section": "Section 74", "title": "Demand for fraud cases",
     "category": "Demand", "subcategory": "Fraud",
     "content": "Demand notice under Section 74: Show cause notice within 54 months. Tax + 18% interest + 100% penalty. If tax with interest paid within 30 days of notice, penalty reduces to 15%. If paid before order, penalty is 25%.",
     "keywords": "demand, section 74, fraud, 54 months, 100% penalty, voluntary payment"},
    
    # Advance Ruling
    {"id": "aar", "section": "Sections 95-106", "title": "Advance ruling",
     "category": "Advance Ruling", "subcategory": "Procedure",
     "content": "Advance ruling can be sought on classification, rate of tax, applicability of notification, ITC eligibility, place of supply, and registration liability. Application fee is Rs. 5,000 (CGST + SGST).",
     "keywords": "advance ruling, AAR, classification, rate, ITC, place of supply, 5,000"},
    
    # Appeals
    {"id": "sec107", "section": "Section 107", "title": "Appeal to Appellate Authority",
     "category": "Appeal", "subcategory": "First Appeal",
     "content": "Appeal against the adjudicating authority must be filed within 3 months from the date of the order. Pre-deposit of 10% of disputed tax is required. If additional tax of 10% is paid, further appeal can be made.",
     "keywords": "appeal, 3 months, 10% pre-deposit, appellate authority, adjudication"},
]


# ================================================================
# EMBEDDING & SEARCH ENGINE
# ================================================================

class GSTKnowledgeBase:
    """Local knowledge base for GST rules with embedding-based semantic search."""

    def __init__(self):
        self.rules = GST_RULES
        self.embeddings_cache: dict[str, list[float]] = {}
        self._init_db()

    def _init_db(self):
        """Initialize the knowledge base database."""
        db_path = settings.BASE_DIR / "taxflow.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS gst_knowledge (
                    id TEXT PRIMARY KEY,
                    rule_id TEXT UNIQUE,
                    section TEXT,
                    title TEXT,
                    category TEXT,
                    subcategory TEXT,
                    content TEXT,
                    keywords TEXT,
                    embedding TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_knowledge_category ON gst_knowledge(category);
                CREATE INDEX IF NOT EXISTS idx_knowledge_rule_id ON gst_knowledge(rule_id);
            """)
            conn.commit()

            # Populate if empty
            cursor = conn.execute("SELECT COUNT(*) as c FROM gst_knowledge")
            if cursor.fetchone()["c"] == 0:
                for rule in self.rules:
                    conn.execute(
                        """INSERT INTO gst_knowledge (id, rule_id, section, title, category, subcategory, content, keywords)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (str(uuid.uuid4()), rule["id"], rule["section"], rule["title"],
                         rule["category"], rule["subcategory"], rule["content"], rule["keywords"])
                    )
                conn.commit()
        finally:
            conn.close()

    def _simple_embed(self, text: str) -> list[float]:
        """Generate a simple TF-IDF-like embedding vector."""
        # Use cached embedding if available
        cache_key = text[:100]
        if cache_key in self.embeddings_cache:
            return self.embeddings_cache[cache_key]

        # Tokenize and create a simple frequency vector
        words = re.findall(r'\w+', text.lower())
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1

        # Create vector from word frequencies (using hash features)
        vector = [0.0] * 128
        for word, freq in word_freq.items():
            hash_val = hash(word) % 128
            tf = 1.0 + (freq / max(word_freq.values()))
            vector[hash_val] += tf

        # Normalize
        magnitude = sum(v ** 2 for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        self.embeddings_cache[cache_key] = vector
        return vector

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a ** 2 for a in vec1) ** 0.5
        mag2 = sum(b ** 2 for b in vec2) ** 0.5
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)

    def search(self, query: str, category: Optional[str] = None,
               top_k: int = 5) -> list[dict]:
        """Search the knowledge base for relevant rules.

        Uses a combination of keyword matching and semantic similarity.
        """
        query_vec = self._simple_embed(query)
        query_words = set(re.findall(r'\w+', query.lower()))

        results = []

        for rule in self.rules:
            # Category filter
            if category and rule["category"].lower() != category.lower():
                continue

            # Keyword matching score
            keyword_score = 0
            rule_keywords = set(rule["keywords"].lower().split(", "))
            overlap = query_words & rule_keywords
            keyword_score = len(overlap) / max(len(query_words | rule_keywords), 1)

            # Semantic similarity score
            content_vec = self._simple_embed(rule["content"])
            semantic_score = self._cosine_similarity(query_vec, content_vec)

            # Combined score (weighted)
            combined = (keyword_score * 0.6) + (semantic_score * 0.4)

            results.append({
                **rule,
                "score": round(combined, 4),
                "keyword_score": round(keyword_score, 4),
                "semantic_score": round(semantic_score, 4),
            })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]

    def search_by_category(self, category: str) -> list[dict]:
        """Get all rules in a category."""
        return [r for r in self.rules if r["category"].lower() == category.lower()]

    def get_categories(self) -> list[str]:
        """Get all unique categories."""
        cats = set()
        for r in self.rules:
            cats.add(r["category"])
        return sorted(cats)

    def get_subcategories(self, category: str) -> list[str]:
        """Get subcategories within a category."""
        subs = set()
        for r in self.rules:
            if r["category"].lower() == category.lower():
                subs.add(r["subcategory"])
        return sorted(subs)

    def format_rag_context(self, query: str, top_k: int = 3) -> str:
        """Format search results as a context string for RAG."""
        results = self.search(query, top_k=top_k)
        if not results:
            return ""

        context_parts = ["Relevant GST Rules and Provisions:"]
        for r in results:
            context_parts.append(f"\n**{r['section']} - {r['title']}**")
            context_parts.append(f"Category: {r['category']} > {r['subcategory']}")
            context_parts.append(f"Relevance: {r['score']:.0%}")
            context_parts.append(r['content'])

        return "\n".join(context_parts)

    def generate_compliance_report(self) -> str:
        """Generate a comprehensive compliance reference HTML."""
        html = """
        <div class="kg-container">
            <div class="calc-header">
                <span class="calc-icon">📚</span>
                <span>GST Knowledge Base</span>
            </div>
        """

        categories = self.get_categories()
        for cat in categories:
            rules = self.search_by_category(cat)
            html += f"""
            <div class="kg-section">
                <h3 class="kg-category-title">{cat}</h3>
            """
            for rule in rules:
                html += f"""
                <div class="kg-card">
                    <div class="kg-card-header">
                        <span class="kg-section-label">{rule['section']}</span>
                        <span class="kg-subcategory">{rule['subcategory']}</span>
                    </div>
                    <div class="kg-card-title">{rule['title']}</div>
                    <div class="kg-card-content">{rule['content'][:200]}{'...' if len(rule['content']) > 200 else ''}</div>
                </div>
                """
            html += "</div>"

        html += "</div>"
        return html


# ================================================================
# SINGLETON INSTANCE
# ================================================================

_knowledge_base: Optional[GSTKnowledgeBase] = None


def get_knowledge_base() -> GSTKnowledgeBase:
    """Get or create the singleton knowledge base instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = GSTKnowledgeBase()
    return _knowledge_base


def search_gst_rules(query: str, category: Optional[str] = None, top_k: int = 5) -> list[dict]:
    """Convenience function to search GST rules."""
    kb = get_knowledge_base()
    return kb.search(query, category, top_k)


def get_rag_context(query: str, top_k: int = 3) -> str:
    """Get RAG context for an LLM query."""
    kb = get_knowledge_base()
    return kb.format_rag_context(query, top_k)
