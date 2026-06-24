"""Client Onboarding Checklist - Interactive widget for client setup workflow.

Provides a step-by-step onboarding checklist for new clients,
tracking progress through document collection, verification, and setup.
"""

from datetime import datetime, date
from typing import Any, Optional


# ================================================================
# ONBOARDING CHECKLIST DATA
# ================================================================

ONBOARDING_STEPS = [
    {
        "id": "step_1",
        "icon": "🤝",
        "title": "Client Information",
        "description": "Collect client details: name, address, contact information",
        "items": [
            {"id": "1a", "label": "Client Name & Business Name", "required": True},
            {"id": "1b", "label": "Registered Address & Contact", "required": True},
            {"id": "1c", "label": "Business Type (Proprietorship/Partnership/Pvt Ltd)", "required": False},
            {"id": "1d", "label": "Contact Person & Phone Number", "required": False},
        ]
    },
    {
        "id": "step_2",
        "icon": "📋",
        "title": "GST Registration",
        "description": "Verify and collect GST registration documents",
        "items": [
            {"id": "2a", "label": "GST Registration Certificate", "required": True},
            {"id": "2b", "label": "GSTIN (15-digit)", "required": True},
            {"id": "2c", "label": "GST Portal Login Credentials", "required": False},
            {"id": "2d", "label": "Composition / Regular Scheme Status", "required": False},
        ]
    },
    {
        "id": "step_3",
        "icon": "📄",
        "title": "Document Collection",
        "description": "Upload and verify business documents",
        "items": [
            {"id": "3a", "label": "PAN Card", "required": True},
            {"id": "3b", "label": "Aadhaar Card (Proprietor/Partners/Directors)", "required": True},
            {"id": "3c", "label": "Bank Statement (Last 6 months)", "required": True},
            {"id": "3d", "label": "Previous GST Returns (if applicable)", "required": False},
        ]
    },
    {
        "id": "step_4",
        "icon": "🧾",
        "title": "Invoice Setup",
        "description": "Configure invoice numbering and templates",
        "items": [
            {"id": "4a", "label": "Invoice Numbering Series", "required": True},
            {"id": "4b", "label": "Invoice Template / Format", "required": False},
            {"id": "4c", "label": "E-Invoice / E-Way Bill Setup", "required": False},
            {"id": "4d", "label": "HSN/SAC Code Mapping", "required": False},
        ]
    },
    {
        "id": "step_5",
        "icon": "🔐",
        "title": "Compliance Setup",
        "description": "Configure filing frequency and due dates",
        "items": [
            {"id": "5a", "label": "Filing Frequency (Monthly/Quarterly)", "required": True},
            {"id": "5b", "label": "Return Type (GSTR-1/3B/9)", "required": True},
            {"id": "5c", "label": "TDS Applicability", "required": False},
            {"id": "5d", "label": "Reverse Charge Applicability", "required": False},
        ]
    },
    {
        "id": "step_6",
        "icon": "✅",
        "title": "Final Review",
        "description": "Review all data and finalize onboarding",
        "items": [
            {"id": "6a", "label": "Verify All Documents Uploaded", "required": True},
            {"id": "6b", "label": "Test Invoice Generation", "required": False},
            {"id": "6c", "label": "Client Approval Confirmation", "required": False},
            {"id": "6d", "label": "Onboarding Complete", "required": True},
        ]
    },
]


def build_onboarding_html(project_id: str, project_info: Optional[dict] = None) -> str:
    """Build the onboarding checklist HTML.

    Tracks completion status per project in localStorage for simplicity.
    In a production environment, this would be persisted to the database.
    """
    project_name = project_info.get("name", "Client") if project_info else "Client"

    steps_html = ""
    total_items = 0
    for step in ONBOARDING_STEPS:
        items_html = ""
        step_items = step.get("items", [])
        for item in step_items:
            total_items += 1
            item_id = f"{project_id}_{item['id']}"
            required_badge = '<span style="color:#DC2626;font-size:10px;">*Required</span>' if item.get("required") else ""
            items_html += f"""
            <label style="display:flex;align-items:center;gap:8px;padding:4px 0;cursor:pointer;font-size:12px;color:#374151;">
                <input type="checkbox" class="onboarding-checkbox" data-item-id="{item_id}"
                       onchange="updateOnboardingProgress('{project_id}')"
                       style="width:16px;height:16px;accent-color:#2E75B6;cursor:pointer;">
                <span style="flex:1;">{item['label']}</span>
                {required_badge}
            </label>"""

        steps_html += f"""
        <div class="onboarding-step" style="margin-bottom:12px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <span style="font-size:20px;">{step['icon']}</span>
                <div>
                    <div style="font-size:13px;font-weight:600;color:#1F4E79;">{step['title']}</div>
                    <div style="font-size:11px;color:#6B7280;">{step['description']}</div>
                </div>
            </div>
            <div style="padding-left:8px;border-left:2px solid #E2E8F0;margin-left:10px;">
                {items_html}
            </div>
        </div>"""

    html = f"""
    <div style="background:white;border-radius:12px;border:1px solid #E2E8F0;padding:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <div>
                <h3 style="margin:0;color:#1F4E79;">📋 Client Onboarding</h3>
                <p style="margin:2px 0 0;font-size:12px;color:#6B7280;">{project_name}</p>
            </div>
            <div style="text-align:right;">
                <div style="font-size:11px;color:#6B7280;">Progress</div>
                <div style="font-size:24px;font-weight:700;color:#2E75B6;" id="onboarding-progress-pct-{project_id}">0%</div>
                <div style="font-size:10px;color:#6B7280;" id="onboarding-items-count-{project_id}">0/{total_items}</div>
            </div>
        </div>

        <!-- Progress bar -->
        <div style="height:6px;background:#E2E8F0;border-radius:3px;margin-bottom:16px;overflow:hidden;">
            <div id="onboarding-bar-{project_id}" style="height:100%;width:0%;background:linear-gradient(90deg,#2E75B6,#4CAF50);border-radius:3px;transition:width 0.5s ease-out;"></div>
        </div>

        {steps_html}

        <div style="text-align:center;margin-top:16px;padding-top:12px;border-top:1px solid #E2E8F0;">
            <button onclick="saveOnboarding('{project_id}')" style="background:linear-gradient(135deg,#059669,#10B981);color:white;border:none;padding:8px 24px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.3s;"
                    onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                💾 Save Progress
            </button>
            <span id="onboarding-save-msg" style="margin-left:8px;font-size:11px;color:#6B7280;"></span>
        </div>
    </div>

    <script>
    function updateOnboardingProgress(pid) {{
        var checkboxes = document.querySelectorAll('.onboarding-checkbox');
        var total = checkboxes.length;
        var checked = 0;
        checkboxes.forEach(function(cb) {{
            if (cb.checked) checked++;
        }});
        var pct = total > 0 ? Math.round((checked / total) * 100) : 0;

        var bar = document.getElementById('onboarding-bar-' + pid);
        var pctDisplay = document.getElementById('onboarding-progress-pct-' + pid);
        var countDisplay = document.getElementById('onboarding-items-count-' + pid);

        if (bar) bar.style.width = pct + '%';
        if (pctDisplay) pctDisplay.textContent = pct + '%';
        if (countDisplay) countDisplay.textContent = checked + '/' + total;
    }}

    function saveOnboarding(pid) {{
        var checkboxes = document.querySelectorAll('.onboarding-checkbox');
        var data = {{}};
        checkboxes.forEach(function(cb) {{
            data[cb.getAttribute('data-item-id')] = cb.checked;
        }});
        try {{
            localStorage.setItem('taxflow_onboarding_' + pid, JSON.stringify(data));
            document.getElementById('onboarding-save-msg').textContent = '✅ Saved!';
            setTimeout(function() {{
                document.getElementById('onboarding-save-msg').textContent = '';
            }}, 2000);
        }} catch(e) {{
            document.getElementById('onboarding-save-msg').textContent = '❌ Save failed';
        }}
    }}

    // Restore saved state
    try {{
        var saved = localStorage.getItem('taxflow_onboarding_' + '');
        // Note: In real usage, project_id is passed; for demo we use generic
        var savedData = localStorage.getItem('taxflow_onboarding_' + '{project_id}');
        if (savedData) {{
            var data = JSON.parse(savedData);
            document.querySelectorAll('.onboarding-checkbox').forEach(function(cb) {{
                var itemId = cb.getAttribute('data-item-id');
                if (data[itemId]) {{ cb.checked = true; }}
            }});
            updateOnboardingProgress('{project_id}');
        }}
    }} catch(e) {{}}
    </script>"""

    return html


def get_onboarding_stats(project_id: str) -> dict:
    """Get onboarding completion statistics (would read from DB in production)."""
    return {
        "total_steps": len(ONBOARDING_STEPS),
        "total_items": sum(len(s.get("items", [])) for s in ONBOARDING_STEPS),
        "required_items": sum(
            len([i for i in s.get("items", []) if i.get("required")])
            for s in ONBOARDING_STEPS
        ),
    }
