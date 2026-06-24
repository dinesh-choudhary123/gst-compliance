"""GST Tools - Tax Calculator and HSN/SAC Code Lookup.

Provides interactive tools:
1. GST Tax Calculator: Calculate GST amounts, splits, and reverse calculations
2. HSN/SAC Code Lookup: Searchable directory of common HSN and SAC codes
"""

from datetime import date
from typing import Optional


# ─── GST Tax Calculator ──────────────────────────────────────────

TAX_RATES = [
    {"rate": 0, "label": "0% (Nil Rated)", "cgst": 0, "sgst": 0, "igst": 0, "description": "Essential goods, fresh food"},
    {"rate": 5, "label": "5%", "cgst": 2.5, "sgst": 2.5, "igst": 5, "description": "Common use items, packaged food"},
    {"rate": 12, "label": "12%", "cgst": 6, "sgst": 6, "igst": 12, "description": "Standard goods, processed food"},
    {"rate": 18, "label": "18%", "cgst": 9, "sgst": 9, "igst": 18, "description": "Most goods and services (Standard)"},
    {"rate": 28, "label": "28%", "cgst": 14, "sgst": 14, "igst": 28, "description": "Luxury goods, demerit items"},
]


def build_tax_calculator_html() -> str:
    """Build the GST tax calculator HTML."""
    options_html = "".join(
        f'<option value="{r["rate"]}">{r["label"]}</option>' for r in TAX_RATES
    )

    return f"""
    <div class="tax-calculator-container">
        <div class="calc-header">
            <span class="calc-icon">🧮</span>
            <span>GST Tax Calculator</span>
        </div>

        <div class="calc-body">
            <div class="calc-row">
                <label class="calc-label">Amount (₹)</label>
                <input type="number" id="calc-amount" class="calc-input"
                       placeholder="Enter amount" value="10000" min="0" step="100">
            </div>

            <div class="calc-row">
                <label class="calc-label">Tax Rate</label>
                <select id="calc-rate" class="calc-input calc-select">
                    {options_html}
                </select>
            </div>

            <div class="calc-row">
                <label class="calc-label">Calculation Type</label>
                <select id="calc-type" class="calc-input calc-select">
                    <option value="inclusive">Amount INCLUDES GST</option>
                    <option value="exclusive">Amount EXCLUDES GST</option>
                </select>
            </div>

            <button onclick="calculateGST()" class="calc-btn animate-pulse">
                Calculate GST
            </button>

            <div id="calc-results" class="calc-results">
                <div class="calc-result-row">
                    <span class="calc-result-label">Taxable Amount</span>
                    <span id="calc-taxable" class="calc-result-value">₹8,474.58</span>
                </div>
                <div class="calc-result-row calc-result-divider"></div>
                <div class="calc-result-row">
                    <span class="calc-result-label">CGST (9%)</span>
                    <span id="calc-cgst" class="calc-result-value">₹762.71</span>
                </div>
                <div class="calc-result-row">
                    <span class="calc-result-label">SGST (9%)</span>
                    <span id="calc-sgst" class="calc-result-value">₹762.71</span>
                </div>
                <div class="calc-result-row">
                    <span class="calc-result-label">Total GST</span>
                    <span id="calc-total-tax" class="calc-result-value highlight">₹1,525.42</span>
                </div>
                <div class="calc-result-row calc-result-divider"></div>
                <div class="calc-result-row calc-result-total">
                    <span class="calc-result-label">Total (incl. GST)</span>
                    <span id="calc-total" class="calc-result-value calc-result-amount">₹10,000.00</span>
                </div>
            </div>
        </div>
    </div>

    <script>
    function calculateGST() {{
        var amount = parseFloat(document.getElementById('calc-amount').value) || 0;
        var rate = parseFloat(document.getElementById('calc-rate').value);
        var type = document.getElementById('calc-type').value;

        var taxable, totalTax, cgst, sgst, igst, total;
        var rateInfo = getRateInfo(rate);

        if (type === 'inclusive') {{
            // Amount includes GST
            taxable = amount / (1 + rate / 100);
            totalTax = amount - taxable;
        }} else {{
            // Amount excludes GST
            taxable = amount;
            totalTax = amount * rate / 100;
        }}

        if (rateInfo.cgst > 0) {{
            // Intra-state: split into CGST + SGST
            cgst = totalTax / 2;
            sgst = totalTax / 2;
            igst = 0;
        }} else {{
            // Inter-state: IGST only
            igst = totalTax;
            cgst = 0;
            sgst = 0;
        }}

        total = taxable + totalTax;

        document.getElementById('calc-taxable').textContent = '₹' + taxable.toFixed(2);
        document.getElementById('calc-cgst').textContent = '₹' + cgst.toFixed(2);
        document.getElementById('calc-sgst').textContent = '₹' + sgst.toFixed(2);
        document.getElementById('calc-total-tax').textContent = '₹' + totalTax.toFixed(2);
        document.getElementById('calc-total').textContent = '₹' + total.toFixed(2);
    }}

    function getRateInfo(rate) {{
        var rates = [
            {{rate: 0, cgst: 0, sgst: 0, igst: 0}},
            {{rate: 5, cgst: 2.5, sgst: 2.5, igst: 5}},
            {{rate: 12, cgst: 6, sgst: 6, igst: 12}},
            {{rate: 18, cgst: 9, sgst: 9, igst: 18}},
            {{rate: 28, cgst: 14, sgst: 14, igst: 28}},
        ];
        for (var i = 0; i < rates.length; i++) {{
            if (rates[i].rate === rate) {{
                return rates[i];
            }}
        }}
        return {{rate: 18, cgst: 9, sgst: 9, igst: 18}};
    }}

    // Initialize
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(calculateGST, 100);
        document.getElementById('calc-amount').addEventListener('input', calculateGST);
        document.getElementById('calc-rate').addEventListener('change', calculateGST);
        document.getElementById('calc-type').addEventListener('change', calculateGST);
    }});
    </script>
    """


# ─── HSN/SAC Code Lookup ────────────────────────────────────────

HSN_CODES = [
    {"code": "01", "description": "Live animals", "gst": "5%"},
    {"code": "02", "description": "Meat and edible meat offal", "gst": "0%"},
    {"code": "03", "description": "Fish and crustaceans", "gst": "0%"},
    {"code": "04", "description": "Dairy produce, birds' eggs, honey", "gst": "5%"},
    {"code": "07", "description": "Edible vegetables and tubers", "gst": "0%"},
    {"code": "08", "description": "Edible fruit and nuts", "gst": "0%"},
    {"code": "09", "description": "Coffee, tea, spices", "gst": "5%"},
    {"code": "10", "description": "Cereals", "gst": "0%"},
    {"code": "15", "description": "Animal/vegetable fats and oils", "gst": "5%"},
    {"code": "17", "description": "Sugars and sugar confectionery", "gst": "5%"},
    {"code": "18", "description": "Cocoa and cocoa preparations", "gst": "18%"},
    {"code": "19", "description": "Cereal preparations, bread, pastry", "gst": "18%"},
    {"code": "20", "description": "Vegetable, fruit preparations", "gst": "12%"},
    {"code": "21", "description": "Miscellaneous edible preparations", "gst": "18%"},
    {"code": "22", "description": "Beverages, spirits and vinegar", "gst": "28%"},
    {"code": "24", "description": "Tobacco and manufactured substitutes", "gst": "28%"},
    {"code": "25", "description": "Salt, cement, plastering materials", "gst": "5%"},
    {"code": "27", "description": "Mineral fuels, oils, waxes", "gst": "5%"},
    {"code": "28", "description": "Inorganic chemicals, compounds", "gst": "18%"},
    {"code": "29", "description": "Organic chemicals", "gst": "18%"},
    {"code": "30", "description": "Pharmaceutical products", "gst": "12%"},
    {"code": "32", "description": "Tanning/dyeing extracts, paints", "gst": "18%"},
    {"code": "33", "description": "Essential oils, perfumes, cosmetics", "gst": "18%"},
    {"code": "34", "description": "Soap, waxes, cleaning preparations", "gst": "18%"},
    {"code": "38", "description": "Chemical products (miscellaneous)", "gst": "18%"},
    {"code": "39", "description": "Plastics and articles thereof", "gst": "18%"},
    {"code": "40", "description": "Rubber and articles thereof", "gst": "18%"},
    {"code": "41", "description": "Raw hides, skins, leather", "gst": "5%"},
    {"code": "42", "description": "Leather articles, travel goods", "gst": "18%"},
    {"code": "43", "description": "Fur skins and artificial fur", "gst": "12%"},
    {"code": "44", "description": "Wood and wood articles", "gst": "12%"},
    {"code": "48", "description": "Paper and paperboard", "gst": "12%"},
    {"code": "49", "description": "Printed books, newspapers, stamps", "gst": "0%"},
    {"code": "50", "description": "Silk", "gst": "5%"},
    {"code": "51", "description": "Wool, animal hair, yarn", "gst": "5%"},
    {"code": "52", "description": "Cotton", "gst": "5%"},
    {"code": "53", "description": "Vegetable textile fibers", "gst": "5%"},
    {"code": "54", "description": "Man-made filaments", "gst": "12%"},
    {"code": "55", "description": "Man-made staple fibers", "gst": "12%"},
    {"code": "56", "description": "Wadding, felt, textile articles", "gst": "12%"},
    {"code": "57", "description": "Carpets and floor coverings", "gst": "12%"},
    {"code": "58", "description": "Special woven fabrics", "gst": "12%"},
    {"code": "59", "description": "Impregnated/coated textiles", "gst": "12%"},
    {"code": "60", "description": "Knitted or crocheted fabrics", "gst": "12%"},
    {"code": "61", "description": "Apparel (knitted/crocheted)", "gst": "12%"},
    {"code": "62", "description": "Apparel (not knitted)", "gst": "12%"},
    {"code": "63", "description": "Textile made-up articles", "gst": "12%"},
    {"code": "64", "description": "Footwear", "gst": "5%"},
    {"code": "68", "description": "Stone, plaster, cement articles", "gst": "18%"},
    {"code": "69", "description": "Ceramic products", "gst": "18%"},
    {"code": "70", "description": "Glass and glassware", "gst": "18%"},
    {"code": "71", "description": "Pearls, precious stones, metals", "gst": "3%"},
    {"code": "72", "description": "Iron and steel", "gst": "18%"},
    {"code": "73", "description": "Articles of iron/steel", "gst": "18%"},
    {"code": "74", "description": "Copper and articles thereof", "gst": "18%"},
    {"code": "76", "description": "Aluminum and articles thereof", "gst": "18%"},
    {"code": "82", "description": "Tools, implements, cutlery", "gst": "18%"},
    {"code": "84", "description": "Machinery, mechanical appliances", "gst": "18%"},
    {"code": "85", "description": "Electrical machinery, electronics", "gst": "18%"},
    {"code": "86", "description": "Railway/tramway locomotives", "gst": "12%"},
    {"code": "87", "description": "Vehicles (not railway)", "gst": "28%"},
    {"code": "88", "description": "Aircraft, spacecraft", "gst": "5%"},
    {"code": "90", "description": "Medical/surgical instruments", "gst": "12%"},
    {"code": "91", "description": "Clocks and watches", "gst": "18%"},
    {"code": "94", "description": "Furniture, bedding, lighting", "gst": "18%"},
    {"code": "95", "description": "Toys, games, sports equipment", "gst": "18%"},
    {"code": "96", "description": "Miscellaneous manufactured articles", "gst": "12%"},
    {"code": "97", "description": "Works of art, antiques", "gst": "12%"},
    {"code": "98", "description": "Project imports", "gst": "5%"},
    {"code": "99", "description": "Services (SAC)", "gst": "18%"},
]

SAC_CODES = [
    {"code": "9961", "description": "Food serving services (Restaurant)", "gst": "5%"},
    {"code": "9962", "description": "Accommodation services (Hotel)", "gst": "12%"},
    {"code": "9963", "description": "Real estate services", "gst": "18%"},
    {"code": "9964", "description": "Transport services (Goods)", "gst": "5%"},
    {"code": "9965", "description": "Transport services (Passenger)", "gst": "5%"},
    {"code": "9966", "description": "Support transport services", "gst": "18%"},
    {"code": "9967", "description": "Telecommunication services", "gst": "18%"},
    {"code": "9968", "description": "Financial/insurance services", "gst": "18%"},
    {"code": "9969", "description": "IT/software services", "gst": "18%"},
    {"code": "9971", "description": "Legal services", "gst": "18%"},
    {"code": "9972", "description": "Accounting/audit services", "gst": "18%"},
    {"code": "9973", "description": "R&D services", "gst": "18%"},
    {"code": "9974", "description": "Advertising/market research", "gst": "18%"},
    {"code": "9981", "description": "Education services", "gst": "0%"},
    {"code": "9982", "description": "Healthcare services", "gst": "0%"},
    {"code": "9983", "description": "Creative/entertainment services", "gst": "18%"},
    {"code": "9985", "description": "Repair/maintenance services", "gst": "18%"},
    {"code": "9986", "description": "Personal/household services", "gst": "18%"},
    {"code": "9991", "description": "Membership organization services", "gst": "18%"},
    {"code": "9992", "description": "Waste management services", "gst": "18%"},
    {"code": "9997", "description": "Grooming/beauty services", "gst": "18%"},
    {"code": "9998", "description": "Business exhibition services", "gst": "18%"},
]

# Build the rate info data for the calculator script
RATE_INFO_JS_DATA = "var rateInfoData = " + str([
    {"rate": r["rate"], "cgst": r["cgst"], "sgst": r["sgst"], "igst": r["igst"]}
    for r in TAX_RATES
]).replace("'", "") + ";"


def build_hsn_lookup_html() -> str:
    """Build the HSN/SAC code lookup HTML."""
    hsn_rows = "".join(
        f'<tr><td>{h["code"]}</td><td>{h["description"]}</td><td class="gst-rate">{h["gst"]}</td></tr>'
        for h in HSN_CODES
    )

    sac_rows = "".join(
        f'<tr><td>{s["code"]}</td><td>{s["description"]}</td><td class="gst-rate">{s["gst"]}</td></tr>'
        for s in SAC_CODES
    )

    return f"""
    <div class="hsn-lookup-container">
        <div class="calc-header">
            <span class="calc-icon">🔍</span>
            <span>HSN/SAC Code Lookup</span>
        </div>

        <div class="hsn-search-bar">
            <input type="text" id="hsn-search-input" class="calc-input"
                   placeholder="Search by code or description..." oninput="searchHSN()">
            <span class="hsn-search-icon">🔍</span>
        </div>

        <div class="hsn-tabs">
            <button class="hsn-tab active" onclick="switchHSNTab('hsn', this)">📦 HSN (Goods)</button>
            <button class="hsn-tab" onclick="switchHSNTab('sac', this)">🔧 SAC (Services)</button>
        </div>

        <div id="hsn-table-container" class="hsn-table-container">
            <table class="hsn-table">
                <thead>
                    <tr><th>Code</th><th>Description</th><th>GST Rate</th></tr>
                </thead>
                <tbody id="hsn-tbody">
                    {hsn_rows}
                </tbody>
            </table>
        </div>

        <div id="sac-table-container" class="hsn-table-container" style="display:none;">
            <table class="hsn-table">
                <thead>
                    <tr><th>SAC Code</th><th>Description</th><th>GST Rate</th></tr>
                </thead>
                <tbody id="sac-tbody">
                    {sac_rows}
                </tbody>
            </table>
        </div>
    </div>

    <script>
    {RATE_INFO_JS_DATA}

    function searchHSN() {{
        var query = document.getElementById('hsn-search-input').value.toLowerCase();
        var tables = ['hsn-tbody', 'sac-tbody'];

        tables.forEach(function(tbodyId) {{
            var tbody = document.getElementById(tbodyId);
            if (!tbody) return;
            var rows = tbody.getElementsByTagName('tr');

            for (var i = 0; i < rows.length; i++) {{
                var text = rows[i].textContent.toLowerCase();
                rows[i].style.display = text.includes(query) ? '' : 'none';
            }}
        }});
    }}

    function switchHSNTab(tab, btn) {{
        // Update tabs
        var tabs = document.querySelectorAll('.hsn-tab');
        tabs.forEach(function(t) {{ t.classList.remove('active'); }});
        btn.classList.add('active');

        // Show/hide tables
        document.getElementById('hsn-table-container').style.display = tab === 'hsn' ? 'block' : 'none';
        document.getElementById('sac-table-container').style.display = tab === 'sac' ? 'block' : 'none';
    }}
    </script>
    """
