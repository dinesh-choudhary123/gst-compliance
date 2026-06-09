"""CSS styles for the TaxFlow AI Gradio UI with full dark/light/system theme support."""

CUSTOM_CSS = """
/* ============================================================
   THEME VARIABLES
   ============================================================ */
:root,
[data-theme="light"] {
    /* Backgrounds */
    --bg-page: #F0F4F8;
    --bg-card: #FFFFFF;
    --bg-sidebar: #1a2332;
    --bg-input: #FFFFFF;
    --bg-hover: #F7FAFC;
    --bg-chat-user: linear-gradient(135deg, #1F4E79 0%, #2E75B6 100%);
    --bg-chat-assistant: #F7FAFC;
    --bg-hero: linear-gradient(-45deg, #1F4E79, #2E75B6, #1a2332, #153559);
    --bg-header: linear-gradient(135deg, #1F4E79 0%, #2E75B6 100%);

    /* Text */
    --text-primary: #1A202C;
    --text-secondary: #4A5568;
    --text-muted: #9CA3AF;
    --text-on-dark: #FFFFFF;
    --text-on-dark-muted: #CBD5E0;
    --text-link: #2E75B6;

    /* Borders */
    --border-color: #E2E8F0;
    --border-light: rgba(255,255,255,0.06);
    --border-focus: #2E75B6;

    /* Shadows */
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
    --shadow-lg: 0 10px 40px rgba(0,0,0,0.12);
    --shadow-xl: 0 25px 80px rgba(0,0,0,0.3);

    /* Colors */
    --primary: #1F4E79;
    --primary-light: #2E75B6;
    --primary-dark: #153559;
    --accent: #4CAF50;
    --accent-warm: #FF9800;
    --danger: #F44336;
    --info: #2196F3;

    /* Sizing */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    --radius-full: 9999px;

    /* Transitions */
    --transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 0.5s cubic-bezier(0.4, 0, 0.2, 1);

    /* Gradio variable overrides */
    --body-background-fill: var(--bg-page);
    --block-background-fill: var(--bg-card);
    --block-border-color: var(--border-color);
    --input-background-fill: var(--bg-input);
    --input-text-color: var(--text-primary);
    --input-placeholder-color: var(--text-muted);
    --body-text-color: var(--text-primary);
    --body-text-color-subdued: var(--text-secondary);
    --button-primary-background-fill: var(--primary);
    --button-primary-text-color: white;
    --button-secondary-background-fill: transparent;
    --button-secondary-text-color: var(--text-primary);
    --shadow-drop: var(--shadow-sm);
    --block-label-text-color: var(--text-secondary);
    --block-title-text-color: var(--text-primary);
    --checkbox-label-text-color: var(--text-primary);
    --table-border-color: var(--border-color);
    --table-row-background-fill: var(--bg-card);
    --table-row-alt-background-fill: #F9FAFB;
    --table-text-color: var(--text-primary);
    --table-head-text-color: white;
}

/* ============================================================
   DARK THEME
   ============================================================ */
[data-theme="dark"] {
    --bg-page: #0F172A;
    --bg-card: #1E293B;
    --bg-sidebar: #0B1121;
    --bg-input: #334155;
    --bg-hover: #1E293B;
    --bg-chat-user: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%);
    --bg-chat-assistant: #1E293B;
    --bg-hero: linear-gradient(-45deg, #0F172A, #1E293B, #0B1121, #1E3A5F);
    --bg-header: linear-gradient(135deg, #0F172A 0%, #1E3A5F 100%);

    --text-primary: #F1F5F9;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --text-on-dark: #FFFFFF;
    --text-on-dark-muted: #CBD5E0;
    --text-link: #60A5FA;

    --border-color: #334155;
    --border-light: rgba(255,255,255,0.06);
    --border-focus: #60A5FA;

    --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.4);
    --shadow-lg: 0 10px 40px rgba(0,0,0,0.5);
    --shadow-xl: 0 25px 80px rgba(0,0,0,0.6);

    --primary: #2563EB;
    --primary-light: #3B82F6;
    --primary-dark: #1D4ED8;

    --body-background-fill: #0F172A;
    --block-background-fill: #1E293B;
    --block-border-color: #334155;
    --input-background-fill: #334155;
    --input-text-color: #F1F5F9;
    --input-placeholder-color: #64748B;
    --body-text-color: #F1F5F9;
    --body-text-color-subdued: #94A3B8;
    --button-primary-background-fill: #2563EB;
    --button-secondary-text-color: #F1F5F9;
    --shadow-drop: 0 1px 3px rgba(0,0,0,0.3);
    --block-label-text-color: #94A3B8;
    --block-title-text-color: #F1F5F9;
    --checkbox-label-text-color: #F1F5F9;
    --table-border-color: #334155;
    --table-row-background-fill: #1E293B;
    --table-row-alt-background-fill: #1a2538;
    --table-text-color: #F1F5F9;
}

/* ============================================================
   BASE STYLES
   ============================================================ */
* {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    box-sizing: border-box;
}

body {
    background: var(--bg-page) !important;
    color: var(--text-primary);
    margin: 0;
    padding: 0;
    transition: background var(--transition), color var(--transition);
}

.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
}

/* Apply theme variables to Gradio's internal elements */
.gradio-container,
.gr-box,
.gr-form,
.gr-panel,
.gr-accordion,
.gr-tabs {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
}

/* ============================================================
   ANIMATIONS
   ============================================================ */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(24px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-12px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-30px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes slideInRight {
    from { opacity: 0; transform: translateX(30px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}

@keyframes borderGlow {
    0%, 100% { border-color: var(--border-focus); box-shadow: 0 0 8px rgba(46, 117, 182, 0.1); }
    50% { border-color: rgba(46, 117, 182, 0.6); box-shadow: 0 0 20px rgba(46, 117, 182, 0.2); }
}

.animate-fade-in-up { animation: fadeInUp 0.5s ease-out both; }
.animate-fade-in-down { animation: fadeInDown 0.4s ease-out both; }
.animate-fade-in { animation: fadeIn 0.3s ease-out both; }
.animate-slide-in-left { animation: slideInLeft 0.4s ease-out both; }
.animate-slide-in-right { animation: slideInRight 0.4s ease-out both; }
.animate-scale-in { animation: scaleIn 0.3s ease-out both; }
.animate-float { animation: float 3s ease-in-out infinite; }
.animate-pulse { animation: pulse 2s ease-in-out infinite; }

/* ============================================================
   THEME TOGGLE
   ============================================================ */
.theme-toggle-btn {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: var(--radius-full) !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    color: white !important;
    cursor: pointer !important;
    transition: all var(--transition) !important;
    backdrop-filter: blur(10px) !important;
    min-width: 110px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    font-weight: 500 !important;
}

.theme-toggle-btn:hover {
    background: rgba(255,255,255,0.2) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}

.theme-toggle-btn:active {
    transform: translateY(0) !important;
}

/* ============================================================
   LOGIN SCREEN
   ============================================================ */
.login-container {
    min-height: 100vh !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: var(--bg-hero) !important;
    background-size: 400% 400% !important;
    animation: gradientShift 15s ease infinite !important;
    padding: 20px !important;
    margin: 0 !important;
    position: relative !important;
    overflow: hidden !important;
}

.login-container::before {
    content: '';
    position: absolute;
    width: 600px;
    height: 600px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(46, 117, 182, 0.08) 0%, transparent 70%);
    top: -200px;
    right: -200px;
    animation: float 6s ease-in-out infinite;
}

.login-container::after {
    content: '';
    position: absolute;
    width: 400px;
    height: 400px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(76, 175, 80, 0.05) 0%, transparent 70%);
    bottom: -100px;
    left: -100px;
    animation: float 6s ease-in-out infinite reverse;
}

.login-card-wrapper {
    background: var(--bg-card) !important;
    backdrop-filter: blur(20px) !important;
    border-radius: var(--radius-xl) !important;
    padding: 40px !important;
    width: 420px !important;
    max-width: 100% !important;
    box-shadow: var(--shadow-xl) !important;
    animation: fadeInUp 0.6s ease-out !important;
    border: 1px solid var(--border-color) !important;
    position: relative !important;
    z-index: 1 !important;
}

/* Override Gradio component colors inside login */
.login-card-wrapper .gr-box,
.login-card-wrapper .gr-form,
.login-card-wrapper .gr-panel,
.login-card-wrapper label,
.login-card-wrapper span,
.login-card-wrapper .gr-text-input,
.login-card-wrapper input,
.login-card-wrapper textarea {
    color: var(--text-primary) !important;
    background: var(--bg-input) !important;
    border-color: var(--border-color) !important;
}

.login-card-wrapper .gr-tabs {
    background: transparent !important;
}

.login-card-wrapper .tab-nav button {
    color: var(--text-secondary) !important;
}

.login-card-wrapper .tab-nav button.selected {
    color: var(--primary) !important;
}

.login-icon {
    font-size: 56px;
    margin-bottom: 8px;
    display: inline-block;
    animation: float 3s ease-in-out infinite;
}

.login-title {
    color: var(--text-primary);
    font-size: 28px;
    font-weight: 700;
    margin: 0;
}

.login-subtitle {
    color: var(--text-secondary);
    font-size: 14px;
    margin: 4px 0 0 0;
}

.login-security-badge {
    margin-top: 24px;
    padding: 12px 16px;
    background: var(--bg-hover);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    font-size: 12px;
    color: var(--text-secondary);
    text-align: center;
    transition: all var(--transition);
}

.login-security-badge:hover {
    border-color: var(--primary-light);
    box-shadow: 0 2px 8px rgba(46, 117, 182, 0.08);
}

/* ============================================================
   HEADER
   ============================================================ */
.header-container {
    background: var(--bg-header) !important;
    background-size: 200% 200% !important;
    animation: gradientShift 8s ease infinite !important;
    padding: 14px 28px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    border-bottom: 3px solid var(--accent) !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15) !important;
    position: relative !important;
    z-index: 100 !important;
}

.header-title {
    color: white !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
}

.header-title-icon {
    font-size: 26px;
    animation: float 3s ease-in-out infinite;
}

.header-subtitle {
    color: rgba(255,255,255,0.75) !important;
    font-size: 12px !important;
    margin: 1px 0 0 0 !important;
    font-weight: 400 !important;
}

.header-status {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    transition: all var(--transition);
}

.status-dot.online {
    background: #4CAF50;
    box-shadow: 0 0 10px rgba(76, 175, 80, 0.6);
    animation: pulse 2s infinite;
}

.status-dot.offline {
    background: #F44336;
    box-shadow: 0 0 10px rgba(244, 67, 54, 0.6);
}

.status-text {
    color: white !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}

/* ============================================================
   SIDEBAR — All components on dark background
   ============================================================ */
.sidebar-container {
    background: var(--bg-sidebar) !important;
    border-radius: 0 !important;
    padding: 0 !important;
    min-height: calc(100vh - 80px);
    position: relative !important;
}

/* Fix ALL Gradio component colors inside the dark sidebar */
.sidebar-container label,
.sidebar-container span,
.sidebar-container .gr-box,
.sidebar-container .gr-form,
.sidebar-container .gr-panel,
.sidebar-container input,
.sidebar-container textarea,
.sidebar-container select,
.sidebar-container option,
.sidebar-container .gr-dropdown,
.sidebar-container .gr-text-input,
.sidebar-container .gr-number-input,
.sidebar-container .gr-checkbox,
.sidebar-container .gr-radio,
.sidebar-container .gr-slider,
.sidebar-container .gr-markdown,
.sidebar-container .gr-markdown p,
.sidebar-container .gr-markdown h1,
.sidebar-container .gr-markdown h2,
.sidebar-container .gr-markdown h3,
.sidebar-container .gr-markdown strong,
.sidebar-container .gr-markdown em,
.sidebar-container .gr-markdown a,
.sidebar-container .prose,
.sidebar-container .prose p,
.sidebar-container .prose h1,
.sidebar-container .prose h2,
.sidebar-container .prose h3 {
    color: var(--text-on-dark) !important;
}

/* Input fields in sidebar */
.sidebar-container input,
.sidebar-container textarea,
.sidebar-container select,
.sidebar-container .gr-text-input input,
.sidebar-container .gr-number-input input {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.12) !important;
    color: white !important;
    border-radius: var(--radius-sm) !important;
}

.sidebar-container input::placeholder,
.sidebar-container textarea::placeholder {
    color: rgba(255,255,255,0.4) !important;
}

.sidebar-container input:focus,
.sidebar-container textarea:focus {
    border-color: var(--primary-light) !important;
    box-shadow: 0 0 0 3px rgba(46, 117, 182, 0.2) !important;
    background: rgba(255,255,255,0.12) !important;
}

/* Dropdown in sidebar */
.sidebar-container .gr-dropdown {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.12) !important;
    color: white !important;
    border-radius: var(--radius-sm) !important;
}

.sidebar-container .gr-dropdown .gr-dropdown-label {
    color: var(--text-on-dark-muted) !important;
}

.sidebar-container .gr-dropdown .options,
.sidebar-container .gr-dropdown .dropdown-list {
    background: var(--bg-sidebar) !important;
    border-color: rgba(255,255,255,0.12) !important;
}

.sidebar-container .gr-dropdown .options .item,
.sidebar-container .gr-dropdown .dropdown-list .item {
    color: var(--text-on-dark) !important;
    background: transparent !important;
}

.sidebar-container .gr-dropdown .options .item:hover,
.sidebar-container .gr-dropdown .dropdown-list .item:hover {
    background: rgba(255,255,255,0.08) !important;
    color: white !important;
}

/* ============================================================
   SIDEBAR BUTTONS — Bold & Bright
   ============================================================ */
/* Base sidebar button - bold text */
.sidebar-container button {
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 0.5px !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 20px !important;
    cursor: pointer !important;
    transition: all var(--transition) !important;
    text-transform: none !important;
    position: relative !important;
    overflow: hidden !important;
    color: white !important;
    border: 1.5px solid rgba(255,255,255,0.15) !important;
}

/* ➕ New button - bright emerald gradient */
#btn-new-project button {
    background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    box-shadow: 0 4px 15px rgba(5, 150, 105, 0.4) !important;
    padding: 10px 24px !important;
}

#btn-new-project button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(5, 150, 105, 0.55) !important;
    background: linear-gradient(135deg, #047857 0%, #059669 100%) !important;
}

/* 🗑️ Delete button - bright red gradient */
#btn-delete-project button {
    background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4) !important;
}

#btn-delete-project button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(220, 38, 38, 0.55) !important;
    background: linear-gradient(135deg, #B91C1C 0%, #DC2626 100%) !important;
}

/* 🔄 Refresh & 🚪 Logout buttons - frosted glass bright */
#btn-refresh button, #btn-logout button {
    background: rgba(255,255,255,0.12) !important;
    border: 1.5px solid rgba(255,255,255,0.25) !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 9px 18px !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
}

#btn-refresh button:hover, #btn-logout button:hover {
    background: rgba(255,255,255,0.22) !important;
    border-color: rgba(255,255,255,0.45) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.25) !important;
}

/* Create Project button inside accordion - bright blue gradient */
.sidebar-container .gr-accordion button.gr-button-primary {
    background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%) !important;
    border: none !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    padding: 12px 24px !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important;
    width: 100% !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.15) !important;
}

.sidebar-container .gr-accordion button.gr-button-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(37, 99, 235, 0.55) !important;
    background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
}

/* Make the accordion header stand out but NOT blue gradient */
.sidebar-container .gr-accordion .gr-accordion-header {
    font-weight: 700 !important;
    font-size: 14px !important;
    color: white !important;
    background: rgba(255,255,255,0.06) !important;
    padding: 10px 16px !important;
}

/* Labels in sidebar */
.sidebar-container .gr-label,
.sidebar-container label {
    color: var(--text-on-dark-muted) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}

/* Markdown in sidebar */
.sidebar-container .gr-markdown,
.sidebar-container .prose {
    color: var(--text-on-dark) !important;
}

/* Accordion in sidebar */
.sidebar-container .gr-accordion {
    background: rgba(255,255,255,0.04) !important;
    border-color: rgba(255,255,255,0.08) !important;
}

.sidebar-container .gr-accordion .gr-accordion-header {
    color: var(--text-on-dark) !important;
}

/* Section headings in sidebar */
.sidebar-section-title {
    color: var(--text-on-dark-muted) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    padding: 12px 16px 8px !important;
    border-bottom: 1px solid var(--border-light) !important;
}

.sidebar-item {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 14px !important;
    margin: 4px 16px !important;
    color: var(--text-on-dark) !important;
    font-size: 13px !important;
    transition: all var(--transition) !important;
    cursor: pointer !important;
    position: relative !important;
    overflow: hidden !important;
}

.sidebar-item:hover {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(46, 117, 182, 0.3) !important;
    transform: translateX(4px) !important;
}

.sidebar-item .item-label {
    font-weight: 600 !important;
    color: white !important;
    margin-bottom: 2px !important;
}

.sidebar-item .item-desc {
    color: var(--text-on-dark-muted) !important;
    font-size: 11px !important;
}

.sidebar-stat {
    text-align: center !important;
    padding: 10px !important;
    transition: all var(--transition) !important;
    border-radius: var(--radius-sm) !important;
    flex: 1 !important;
}

.sidebar-stat:hover {
    background: rgba(255,255,255,0.05) !important;
    transform: translateY(-2px) !important;
}

.stat-value {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: white !important;
    line-height: 1.2 !important;
}

.stat-label {
    font-size: 10px !important;
    color: var(--text-on-dark-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    margin-top: 2px !important;
}

/* ============================================================
   CHAT AREA
   ============================================================ */
.chat-container {
    background: var(--bg-card) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-lg) !important;
    border: 1px solid var(--border-color) !important;
    margin: 16px !important;
    overflow: hidden !important;
    transition: all var(--transition) !important;
}

.message-user,
[data-testid="user"] {
    background: var(--bg-chat-user) !important;
    color: white !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 12px 18px !important;
    max-width: 80% !important;
    margin-left: auto !important;
    font-size: 14px !important;
    line-height: 1.5 !important;
    box-shadow: 0 2px 8px rgba(31, 78, 121, 0.2) !important;
}

.message-assistant,
[data-testid="bot"] {
    background: var(--bg-chat-assistant) !important;
    color: var(--text-primary) !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: 12px 18px !important;
    max-width: 85% !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    border: 1px solid var(--border-color) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Chat input */
.chat-input-wrapper input,
.chat-input-wrapper textarea,
.gr-text-input input,
input[placeholder*="Ask about"] {
    border-radius: var(--radius-full) !important;
    border: 2px solid var(--border-color) !important;
    padding: 12px 20px !important;
    font-size: 14px !important;
    transition: all var(--transition) !important;
    background: var(--bg-input) !important;
    color: var(--text-primary) !important;
}

.chat-input-wrapper input:focus,
.gr-text-input input:focus,
input[placeholder*="Ask about"]:focus {
    border-color: var(--primary-light) !important;
    box-shadow: 0 0 0 4px rgba(46, 117, 182, 0.12) !important;
}

.chat-input-wrapper input::placeholder,
input[placeholder*="Ask about"]::placeholder {
    color: var(--text-muted) !important;
    font-style: italic;
}

/* Send button */
.send-btn {
    background: var(--bg-chat-user) !important;
    border-radius: 50% !important;
    width: 46px !important;
    height: 46px !important;
    min-width: 46px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 2px 8px rgba(31, 78, 121, 0.3) !important;
    transition: all var(--transition) !important;
    cursor: pointer !important;
    border: none !important;
    font-size: 20px !important;
    color: white !important;
}

.send-btn:hover {
    transform: scale(1.12) !important;
    box-shadow: 0 4px 16px rgba(31, 78, 121, 0.4) !important;
}

.send-btn:active {
    transform: scale(0.92) !important;
}

/* ============================================================
   BUTTONS
   ============================================================ */
button.gr-button-primary,
button.lg.primary {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: all var(--transition) !important;
    color: white !important;
    position: relative !important;
    overflow: hidden !important;
    cursor: pointer !important;
}

button.gr-button-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(31, 78, 121, 0.3) !important;
}

button.gr-button-primary:active {
    transform: translateY(0) !important;
}

button.gr-button-secondary {
    background: transparent !important;
    border: 2px solid var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
    padding: 8px 18px !important;
    transition: all var(--transition) !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
    cursor: pointer !important;
}

button.gr-button-secondary:hover {
    border-color: var(--primary-light) !important;
    color: var(--primary-light) !important;
    background: rgba(46, 117, 182, 0.04) !important;
    transform: translateY(-1px) !important;
}

/* ============================================================
   TABS
   ============================================================ */
.tabs {
    border: none !important;
}

.gr-tabs,
.gr-tabs .tab-nav {
    background: transparent !important;
}

.gr-tabs .tab-nav {
    border-bottom: 2px solid var(--border-color) !important;
    gap: 2px !important;
    padding: 0 16px !important;
}

.gr-tabs .tab-nav button {
    border: none !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    padding: 12px 20px !important;
    font-weight: 500 !important;
    border-radius: 0 !important;
    transition: all var(--transition) !important;
    font-size: 14px !important;
    position: relative !important;
}

.gr-tabs .tab-nav button::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 50%;
    width: 0;
    height: 2px;
    background: var(--primary);
    transition: all var(--transition);
    transform: translateX(-50%);
}

.gr-tabs .tab-nav button:hover {
    color: var(--primary) !important;
    background: rgba(46, 117, 182, 0.04) !important;
}

.gr-tabs .tab-nav button:hover::after {
    width: 60%;
}

.gr-tabs .tab-nav button.selected {
    color: var(--primary) !important;
    font-weight: 600 !important;
}

.gr-tabs .tab-nav button.selected::after {
    width: 80%;
}

/* ============================================================
   FILE UPLOAD
   ============================================================ */
.file-upload,
.gr-file {
    border: 2px dashed var(--border-color) !important;
    border-radius: var(--radius-lg) !important;
    padding: 32px !important;
    text-align: center !important;
    transition: all var(--transition) !important;
    background: var(--bg-card) !important;
    cursor: pointer !important;
    position: relative !important;
}

.file-upload:hover,
.gr-file:hover {
    border-color: var(--primary-light) !important;
    background: var(--bg-hover) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(46, 117, 182, 0.12) !important;
}

/* ============================================================
   DATAFRAME / TABLE
   ============================================================ */
.gr-dataframe {
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
}

.gr-dataframe table {
    font-size: 13px !important;
    border-collapse: collapse !important;
}

.gr-dataframe thead th {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%) !important;
    color: white !important;
    padding: 12px 14px !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

.gr-dataframe tbody td {
    padding: 10px 14px !important;
    border-bottom: 1px solid var(--border-color) !important;
    transition: background var(--transition-fast) !important;
    color: var(--text-primary) !important;
}

.gr-dataframe tbody tr:hover td {
    background: var(--bg-hover) !important;
}

/* ============================================================
   DROPDOWN (General)
   ============================================================ */
.gr-dropdown {
    border-radius: var(--radius-sm) !important;
    border: 2px solid var(--border-color) !important;
    transition: all var(--transition) !important;
}

.gr-dropdown:focus-within {
    border-color: var(--border-focus) !important;
    box-shadow: 0 0 0 3px rgba(46, 117, 182, 0.12) !important;
}

/* ============================================================
   ACCORDION
   ============================================================ */
.gr-accordion {
    border: 1px solid var(--border-color) !important;
    border-radius: var(--radius-sm) !important;
    margin: 8px 16px !important;
    overflow: hidden !important;
    transition: all var(--transition) !important;
}

.gr-accordion:hover {
    border-color: rgba(46, 117, 182, 0.3) !important;
}

/* ============================================================
   FOOTER
   ============================================================ */
.footer-text {
    text-align: center !important;
    padding: 16px !important;
    color: var(--text-muted) !important;
    font-size: 12px !important;
    border-top: 1px solid var(--border-color) !important;
}

/* ============================================================
   TOOLTIP / INFO BOX
   ============================================================ */
.info-tip {
    background: rgba(46, 117, 182, 0.08) !important;
    border-left: 3px solid var(--primary-light) !important;
    border-radius: var(--radius-sm) !important;
    padding: 12px 16px !important;
    font-size: 13px !important;
    color: var(--text-secondary) !important;
    margin: 8px 0 !important;
}

/* ============================================================
   MARKDOWN OVERRIDES (global)
   ============================================================ */
.gr-markdown,
.gr-markdown p,
.prose,
.prose p {
    color: var(--text-primary) !important;
}

.gr-markdown h1,
.gr-markdown h2,
.gr-markdown h3,
.gr-markdown h4,
.gr-markdown strong,
.prose h1,
.prose h2,
.prose h3,
.prose strong {
    color: var(--text-primary) !important;
}

/* ============================================================
   SCROLLBAR
   ============================================================ */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* ============================================================
   RESPONSIVE
   ============================================================ */
@media (max-width: 768px) {
    .header-container {
        padding: 12px 16px !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
    }
    .header-title { font-size: 18px !important; }
    .header-status { gap: 8px !important; }
    .sidebar-container { min-height: auto !important; }
    .login-card-wrapper { padding: 28px 20px !important; width: 100% !important; margin: 12px !important; }
    .message-user, .message-assistant { max-width: 90% !important; }
    .theme-toggle-btn { min-width: 40px !important; }
}

/* ============================================================
   TRANSITIONS FOR THEME SWITCHING
   ============================================================ */
.gradio-container,
.gr-box,
.gr-form,
.gr-panel,
.gr-tabs,
.gr-tab-nav,
.gr-accordion,
.gr-dataframe,
input,
textarea,
select,
button,
label,
.gr-markdown,
.prose,
[data-testid="user"],
[data-testid="bot"] {
    transition: background var(--transition), color var(--transition), border-color var(--transition), box-shadow var(--transition) !important;
}
"""

THEME_TOGGLE_JS = """
function toggleTheme() {
    const root = document.documentElement;
    const current = root.getAttribute('data-theme') || 'light';
    const themes = ['light', 'dark', 'system'];
    const labels = {'light': '☀️ Light', 'dark': '🌙 Dark', 'system': '💻 System'};
    
    function updateToggleButtons(mode) {
        const btns = document.querySelectorAll('.theme-toggle-btn');
        btns.forEach(function(btn) {
            btn.innerHTML = (labels[mode] || '☀️ Light') + ' ▼';
        });
    }
    
    const idx = themes.indexOf(current);
    const next = themes[(idx + 1) % themes.length];
    
    if (next === 'system') {
        root.removeAttribute('data-theme');
        const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        root.setAttribute('data-theme', isDark ? 'dark' : 'light');
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                const saved = localStorage.getItem('theme');
                if (!saved || saved === 'system') {
                    root.setAttribute('data-theme', e.matches ? 'dark' : 'light');
                }
            });
        }
    } else {
        root.setAttribute('data-theme', next);
    }
    
    localStorage.setItem('theme', next);
    updateToggleButtons(next);
    return labels[next];
}

(function() {
    const root = document.documentElement;
    const saved = localStorage.getItem('theme') || 'system';
    const labels = {'light': '☀️ Light', 'dark': '🌙 Dark', 'system': '💻 System'};
    
    function applyTheme(theme) {
        if (theme === 'system') {
            root.removeAttribute('data-theme');
            const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            root.setAttribute('data-theme', isDark ? 'dark' : 'light');
            if (window.matchMedia) {
                window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                    const t = localStorage.getItem('theme');
                    if (!t || t === 'system') {
                        root.setAttribute('data-theme', e.matches ? 'dark' : 'light');
                    }
                });
            }
        } else {
            root.setAttribute('data-theme', theme);
        }
        const btns = document.querySelectorAll('.theme-toggle-btn');
        btns.forEach(function(btn) {
            btn.innerHTML = (labels[theme] || '☀️ Light') + ' ▼';
        });
    }
    
    applyTheme(saved);
})();
"""
