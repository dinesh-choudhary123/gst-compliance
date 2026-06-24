"""CSS styles for the TaxFlow AI Gradio UI with full dark/light/system theme support.

Includes styles for:
- Theme variables (light/dark)
- Base layout and typography
- Login screen with particles
- Header, sidebar, chat
- Dashboard metrics and charts
- GST Calendar
- Tax Calculator
- HSN/SAC Lookup
- Activity Feed
- Loading animations and skeletons
- Toast notifications
- Micro-interactions
"""

# ================================================================
# THEME TOGGLE JS
# ================================================================

THEME_TOGGLE_JS = """
function toggleTheme() {
    const root = document.documentElement;
    const current = root.getAttribute('data-theme') || 'light';
    const themes = ['light', 'dark', 'system'];
    const labels = {'light': '\u2600\ufe0f Light', 'dark': '\U0001f319 Dark', 'system': '\U0001f4bb System'};

    function updateToggleButtons(mode) {
        const btns = document.querySelectorAll('.theme-toggle-btn');
        btns.forEach(function(btn) {
            btn.innerHTML = (labels[mode] || '\u2600\ufe0f Light') + ' \u25bc';
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
    const labels = {'light': '\u2600\ufe0f Light', 'dark': '\U0001f319 Dark', 'system': '\U0001f4bb System'};

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
            btn.innerHTML = (labels[theme] || '\u2600\ufe0f Light') + ' \u25bc';
        });
    }

    applyTheme(saved);
})();
"""

# ================================================================
# PARTICLE BACKGROUND CSS
# ================================================================

PARTICLE_BG_CSS = """
#particle-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
    opacity: 0.5;
}
.login-container #particle-canvas {
    opacity: 0.4;
}
"""

# ================================================================
# DASHBOARD STYLES
# ================================================================

DASHBOARD_CSS = """
.dashboard-container {
    padding: 12px 0;
    animation: fadeIn 0.5s ease-out;
}
.dashboard-grid {
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 8px;
}
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 20px 18px;
    position: relative;
    overflow: hidden;
    transition: all var(--transition);
    cursor: default;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    opacity: 0;
    transition: opacity var(--transition);
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}
.metric-card:hover::before {
    opacity: 1;
}
.metric-gradient-blue::before { background: linear-gradient(90deg, #2E75B6, #4E9EEA); }
.metric-gradient-teal::before { background: linear-gradient(90deg, #059669, #10B981); }
.metric-gradient-purple::before { background: linear-gradient(90deg, #7C3AED, #A78BFA); }
.metric-gradient-amber::before { background: linear-gradient(90deg, #D97706, #F59E0B); }
.metric-icon { font-size: 28px; margin-bottom: 8px; }
.metric-value { font-size: 24px; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.metric-label { font-size: 12px; color: var(--text-secondary); margin-top: 2px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
.metric-trend { font-size: 11px; color: var(--text-muted); margin-top: 6px; padding-top: 6px; border-top: 1px solid var(--border-color); }
.chart-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 12px; transition: all var(--transition); }
.chart-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.chart-empty { display: flex; align-items: center; justify-content: center; min-height: 200px; }
.chart-empty-content { text-align: center; padding: 40px; }
.chart-empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.5; }
.chart-empty-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.chart-empty-message { font-size: 13px; color: var(--text-muted); }
[data-theme="dark"] .js-plotly-plot .plotly .main-svg { background: transparent !important; }
[data-theme="dark"] .js-plotly-plot .plotly .text-point { fill: #F1F5F9 !important; }
@media (max-width: 768px) { .metrics-grid { grid-template-columns: repeat(2, 1fr); } .metric-value { font-size: 20px; } }
@media (max-width: 480px) { .metrics-grid { grid-template-columns: 1fr; } }
"""

# ================================================================
# CALENDAR STYLES
# ================================================================

CALENDAR_CSS = """
.calendar-container { padding: 8px 0; animation: fadeIn 0.5s ease-out; }
.calendar-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); margin-bottom: 16px; }
.calendar-title { font-size: 18px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
.calendar-icon { font-size: 24px; animation: float 3s ease-in-out infinite; }
.calendar-date-display { font-size: 14px; color: var(--text-secondary); font-weight: 500; }
.calendar-summary-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.calendar-stat { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 16px; text-align: center; transition: all var(--transition); }
.calendar-stat:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.calendar-stat-danger { border-left: 3px solid #F44336; }
.calendar-stat-warning { border-left: 3px solid #FF9800; }
.calendar-stat-success { border-left: 3px solid #4CAF50; }
.calendar-stat-value { font-size: 28px; font-weight: 700; }
.calendar-stat-danger .calendar-stat-value { color: #F44336; }
.calendar-stat-warning .calendar-stat-value { color: #FF9800; }
.calendar-stat-success .calendar-stat-value { color: #4CAF50; }
.calendar-stat-label { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
.calendar-section { margin-bottom: 16px; }
.calendar-section-title { font-size: 14px; font-weight: 600; padding: 8px 12px; border-radius: var(--radius-sm); margin-bottom: 8px; }
.calendar-section-danger { color: #F44336; background: rgba(244, 67, 54, 0.08); }
.calendar-section-warning { color: #FF9800; background: rgba(255, 152, 0, 0.08); }
.calendar-section-info { color: var(--primary-light); background: rgba(46, 117, 182, 0.08); }
.calendar-item { display: flex; align-items: center; gap: 16px; padding: 12px 16px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); margin-bottom: 6px; transition: all var(--transition); cursor: default; }
.calendar-item:hover { transform: translateX(4px); box-shadow: var(--shadow-sm); }
.calendar-item-border-danger { border-left: 3px solid #F44336; }
.calendar-item-border-warning { border-left: 3px solid #FF9800; }
.calendar-item-border-info { border-left: 3px solid var(--primary-light); }
.calendar-item-date { text-align: center; min-width: 50px; }
.calendar-item-day { font-size: 22px; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.calendar-item-month { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; }
.calendar-item-content { flex: 1; }
.calendar-item-title { font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 2px; }
.calendar-item-desc { font-size: 11px; color: var(--text-secondary); margin-bottom: 4px; }
.calendar-item-meta { display: flex; gap: 8px; }
.calendar-item-form { font-size: 10px; font-weight: 600; color: white; background: var(--primary); padding: 2px 8px; border-radius: 4px; }
.calendar-item-frequency { font-size: 10px; color: var(--text-muted); background: var(--bg-hover); padding: 2px 8px; border-radius: 4px; }
.calendar-item-badge { min-width: 110px; text-align: right; }
.calendar-badge { font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: var(--radius-full); white-space: nowrap; }
.calendar-badge-danger { color: #F44336; background: rgba(244, 67, 54, 0.1); }
.calendar-badge-warning { color: #FF9800; background: rgba(255, 152, 0, 0.1); }
.calendar-badge-info { color: var(--primary-light); background: rgba(46, 117, 182, 0.1); }
.calendar-all-list { max-height: 400px; overflow-y: auto; }
.calendar-all-list::-webkit-scrollbar { width: 4px; }
.calendar-all-list::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 2px; }
@media (max-width: 768px) { .calendar-summary-strip { grid-template-columns: repeat(3, 1fr); gap: 8px; } .calendar-item { flex-wrap: wrap; } .calendar-item-badge { width: 100%; text-align: center; min-width: unset; } }
"""

# ================================================================
# TAX CALCULATOR STYLES
# ================================================================

TAX_CALCULATOR_CSS = """
.tax-calculator-container { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow: hidden; max-width: 500px; margin: 0 auto; }
.calc-header { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%); color: white; padding: 16px 20px; font-size: 16px; font-weight: 700; display: flex; align-items: center; gap: 8px; }
.calc-icon { font-size: 22px; }
.calc-body { padding: 20px; }
.calc-row { margin-bottom: 16px; }
.calc-label { display: block; font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
.calc-input { width: 100%; padding: 10px 14px; border: 2px solid var(--border-color); border-radius: var(--radius-sm); font-size: 14px; background: var(--bg-input); color: var(--text-primary); transition: all var(--transition); box-sizing: border-box; }
.calc-input:focus { border-color: var(--primary-light); outline: none; box-shadow: 0 0 0 3px rgba(46, 117, 182, 0.12); }
.calc-select { appearance: none; -webkit-appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 8L1 3h10z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 32px; }
.calc-btn { width: 100%; padding: 12px; background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%); color: white; border: none; border-radius: var(--radius-sm); font-size: 15px; font-weight: 600; cursor: pointer; transition: all var(--transition); margin-bottom: 20px; }
.calc-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(46, 117, 182, 0.3); }
.calc-btn:active { transform: translateY(0); }
.calc-results { background: var(--bg-hover); border-radius: var(--radius-sm); padding: 16px; border: 1px solid var(--border-color); }
.calc-result-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; }
.calc-result-label { font-size: 13px; color: var(--text-secondary); }
.calc-result-value { font-size: 13px; font-weight: 600; color: var(--text-primary); font-family: 'JetBrains Mono', 'SF Mono', monospace; }
.calc-result-value.highlight { color: var(--accent); font-size: 15px; }
.calc-result-divider { height: 1px; background: var(--border-color); margin: 4px 0; padding: 0 !important; }
.calc-result-total { margin-top: 4px; }
.calc-result-amount { font-size: 18px; font-weight: 700; color: var(--primary-light); }
"""

# ================================================================
# HSN LOOKUP STYLES
# ================================================================

HSN_LOOKUP_CSS = """
.hsn-lookup-container { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow: hidden; max-width: 600px; margin: 0 auto; }
.hsn-search-bar { position: relative; margin: 16px 20px; }
.hsn-search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); font-size: 16px; }
.hsn-search-bar .calc-input { padding-left: 36px; }
.hsn-tabs { display: flex; gap: 4px; padding: 0 20px; margin-bottom: 12px; }
.hsn-tab { flex: 1; padding: 10px 16px; background: var(--bg-hover); border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; font-weight: 500; color: var(--text-secondary); transition: all var(--transition); }
.hsn-tab:hover { border-color: var(--primary-light); color: var(--primary-light); }
.hsn-tab.active { background: var(--primary); border-color: var(--primary); color: white; }
.hsn-table-container { padding: 0 20px 20px; }
.hsn-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.hsn-table th { background: var(--bg-hover); color: var(--text-secondary); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; padding: 10px 12px; text-align: left; border-bottom: 2px solid var(--border-color); position: sticky; top: 0; z-index: 1; }
.hsn-table td { padding: 8px 12px; border-bottom: 1px solid var(--border-color); color: var(--text-primary); transition: background var(--transition-fast); }
.hsn-table tbody tr:hover td { background: var(--bg-hover); }
.hsn-table .gst-rate { font-weight: 600; color: var(--accent); }
.hsn-table-container { max-height: 400px; overflow-y: auto; }
.hsn-table-container::-webkit-scrollbar { width: 4px; }
.hsn-table-container::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 2px; }
"""

# ================================================================
# ACTIVITY FEED STYLES
# ================================================================

ACTIVITY_FEED_CSS = """
.activity-timeline { position: relative; padding: 0 !important; }
.activity-timeline::before { content: ''; position: absolute; left: 18px; top: 0; bottom: 0; width: 2px; background: var(--border-color); }
.activity-item { position: relative; display: flex; gap: 16px; padding: 12px 0 12px 36px; margin-left: 0; }
.activity-dot { position: absolute; left: 11px; top: 16px; width: 16px; height: 16px; border-radius: 50%; border: 3px solid var(--bg-page); z-index: 1; }
.activity-dot.activity-blue { background: #2E75B6; }
.activity-dot.activity-green { background: #4CAF50; }
.activity-dot.activity-red { background: #F44336; }
.activity-dot.activity-amber { background: #FF9800; }
.activity-dot.activity-purple { background: #7C3AED; }
.activity-dot.activity-teal { background: #059669; }
.activity-dot.activity-indigo { background: #6366F1; }
.activity-dot.activity-gray { background: #9CA3AF; }
.activity-content { flex: 1; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 12px 16px; transition: all var(--transition); }
.activity-content:hover { box-shadow: var(--shadow-sm); border-color: var(--primary-light); }
.activity-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.activity-icon { font-size: 16px; }
.activity-title { font-size: 13px; font-weight: 600; color: var(--text-primary); flex: 1; }
.activity-time { font-size: 11px; color: var(--text-muted); white-space: nowrap; }
.activity-description { font-size: 12px; color: var(--text-secondary); line-height: 1.4; }
.activity-details { font-size: 11px; color: var(--text-muted); margin-top: 6px; padding-top: 6px; border-top: 1px solid var(--border-color); }
.activity-empty { text-align: center; padding: 60px 20px; color: var(--text-muted); }
.activity-empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.5; }
.activity-empty-text { font-size: 14px; line-height: 1.6; }
.quick-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 16px; }
.quick-stat-item { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 12px 8px; text-align: center; transition: all var(--transition); }
.quick-stat-item:hover { transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.quick-stat-value { font-size: 20px; font-weight: 700; color: var(--primary-light); }
.quick-stat-label { font-size: 10px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
@media (max-width: 480px) { .quick-stats { grid-template-columns: repeat(2, 1fr); } }
"""

# ================================================================
# LOADING ANIMATIONS & SKELETONS
# ================================================================

LOADING_CSS = """
.skeleton { background: linear-gradient(90deg, var(--bg-hover) 25%, var(--border-color) 50%, var(--bg-hover) 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: var(--radius-sm); }
.skeleton-line { height: 12px; margin-bottom: 8px; width: 100%; }
.skeleton-line:last-child { width: 60%; }
.skeleton-card { height: 120px; margin-bottom: 12px; }
.skeleton-circle { width: 40px; height: 40px; border-radius: 50%; }
.loading-spinner { display: inline-block; width: 24px; height: 24px; border: 3px solid var(--border-color); border-top-color: var(--primary-light); border-radius: 50%; animation: spin 0.8s linear infinite; }
.loading-dots { display: flex; gap: 6px; align-items: center; justify-content: center; padding: 20px; }
.loading-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--primary-light); animation: loadingDot 1.4s ease-in-out infinite both; }
.loading-dot:nth-child(1) { animation-delay: -0.32s; }
.loading-dot:nth-child(2) { animation-delay: -0.16s; }
.loading-dot:nth-child(3) { animation-delay: 0s; }
@keyframes loadingDot { 0%, 80%, 100% { transform: scale(0); opacity: 0.5; } 40% { transform: scale(1); opacity: 1; } }
.gradient-border { position: relative; border-radius: var(--radius-md); overflow: hidden; }
.gradient-border::before { content: ''; position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px; background: linear-gradient(45deg, var(--primary), var(--accent), var(--primary-light), var(--accent-warm)); background-size: 400% 400%; animation: gradientShift 3s ease infinite; z-index: -1; border-radius: calc(var(--radius-md) + 2px); }
.gradient-border > * { background: var(--bg-card); border-radius: var(--radius-md); position: relative; z-index: 1; margin: 2px; }
.toast-container { position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; }
.toast { display: flex; align-items: center; gap: 10px; padding: 12px 18px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-sm); box-shadow: var(--shadow-lg); animation: slideInRight 0.3s ease-out, fadeOut 0.3s ease-in 3s forwards; max-width: 400px; }
.toast-success { border-left: 4px solid #4CAF50; }
.toast-error { border-left: 4px solid #F44336; }
.toast-warning { border-left: 4px solid #FF9800; }
.toast-info { border-left: 4px solid #2E75B6; }
.toast-icon { font-size: 18px; }
.toast-message { font-size: 13px; color: var(--text-primary); flex: 1; }
.toast-close { cursor: pointer; opacity: 0.5; font-size: 16px; transition: opacity var(--transition-fast); }
.toast-close:hover { opacity: 1; }
@keyframes fadeOut { to { opacity: 0; transform: translateX(100px); } }
.glow-effect { position: relative; }
.glow-effect::after { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(46, 117, 182, 0.05) 0%, transparent 70%); animation: pulse 3s ease-in-out infinite; pointer-events: none; z-index: 0; }
.stagger-item:nth-child(1) { animation-delay: 0.0s; }
.stagger-item:nth-child(2) { animation-delay: 0.05s; }
.stagger-item:nth-child(3) { animation-delay: 0.1s; }
.stagger-item:nth-child(4) { animation-delay: 0.15s; }
.stagger-item:nth-child(5) { animation-delay: 0.2s; }
.stagger-item:nth-child(6) { animation-delay: 0.25s; }
.stagger-item:nth-child(7) { animation-delay: 0.3s; }
.stagger-item:nth-child(8) { animation-delay: 0.35s; }
.stagger-item:nth-child(9) { animation-delay: 0.4s; }
.stagger-item:nth-child(10) { animation-delay: 0.45s; }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
.animate-bounce { animation: bounce 0.6s ease infinite; }
@keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-5px); } 75% { transform: translateX(5px); } }
.animate-shake { animation: shake 0.4s ease; }
.ripple-btn { position: relative; overflow: hidden; }
.ripple-btn::after { content: ''; position: absolute; border-radius: 50%; background: rgba(255,255,255,0.3); width: 100px; height: 100px; margin-top: -50px; margin-left: -50px; top: 50%; left: 50%; transform: scale(0); opacity: 0; }
.ripple-btn:active::after { animation: ripple 0.6s ease-out; }
@keyframes ripple { to { transform: scale(4); opacity: 0; } }
.typing-indicator { display: flex; align-items: center; gap: 4px; padding: 8px 16px; background: var(--bg-chat-assistant); border: 1px solid var(--border-color); border-radius: 18px 18px 18px 4px; max-width: fit-content; }
.typing-indicator .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-muted); animation: typingBounce 1.4s ease-in-out infinite both; }
.typing-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator .dot:nth-child(2) { animation-delay: -0.16s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0s; }
@keyframes typingBounce { 0%, 60%, 100% { transform: translateY(0); opacity: 0.4; } 30% { transform: translateY(-8px); opacity: 1; } }
"""

# ================================================================
# MAIN CUSTOM CSS - ALL STYLES COMBINED
# ================================================================

CUSTOM_CSS = """
/* ============================================================
   THEME VARIABLES
   ============================================================ */
:root,
[data-theme="light"] {
    --bg-page: #F0F4F8;
    --bg-card: #FFFFFF;
    --bg-sidebar: #1a2332;
    --bg-input: #FFFFFF;
    --bg-hover: #F7FAFC;
    --bg-chat-user: linear-gradient(135deg, #1F4E79 0%, #2E75B6 100%);
    --bg-chat-assistant: #F7FAFC;
    --bg-hero: linear-gradient(-45deg, #1F4E79, #2E75B6, #1a2332, #153559);
    --bg-header: linear-gradient(135deg, #1F4E79 0%, #2E75B6 100%);
    --text-primary: #1A202C;
    --text-secondary: #4A5568;
    --text-muted: #9CA3AF;
    --text-on-dark: #FFFFFF;
    --text-on-dark-muted: #CBD5E0;
    --text-link: #2E75B6;
    --border-color: #E2E8F0;
    --border-light: rgba(255,255,255,0.06);
    --border-focus: #2E75B6;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
    --shadow-lg: 0 10px 40px rgba(0,0,0,0.12);
    --shadow-xl: 0 25px 80px rgba(0,0,0,0.3);
    --primary: #1F4E79;
    --primary-light: #2E75B6;
    --primary-dark: #153559;
    --accent: #4CAF50;
    --accent-warm: #FF9800;
    --danger: #F44336;
    --info: #2196F3;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    --radius-full: 9999px;
    --transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 0.5s cubic-bezier(0.4, 0, 0.2, 1);
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
* { font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif; box-sizing: border-box; }
body { background: var(--bg-page) !important; color: var(--text-primary); margin: 0; padding: 0; transition: background var(--transition), color var(--transition); }
.gradio-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; background: transparent !important; }
.gradio-container, .gr-box, .gr-form, .gr-panel, .gr-accordion, .gr-tabs { background: var(--bg-card) !important; color: var(--text-primary) !important; }

/* ============================================================
   ANIMATIONS
   ============================================================ */
@keyframes fadeInUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeInDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideInLeft { from { opacity: 0; transform: translateX(-30px); } to { opacity: 1; transform: translateX(0); } }
@keyframes slideInRight { from { opacity: 0; transform: translateX(30px); } to { opacity: 1; transform: translateX(0); } }
@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
@keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-8px); } }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
@keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
@keyframes borderGlow { 0%, 100% { border-color: var(--border-focus); box-shadow: 0 0 8px rgba(46, 117, 182, 0.1); } 50% { border-color: rgba(46, 117, 182, 0.6); box-shadow: 0 0 20px rgba(46, 117, 182, 0.2); } }
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
.theme-toggle-btn { background: rgba(255,255,255,0.12) !important; border: 1px solid rgba(255,255,255,0.15) !important; border-radius: var(--radius-full) !important; padding: 6px 14px !important; font-size: 13px !important; color: white !important; cursor: pointer !important; transition: all var(--transition) !important; backdrop-filter: blur(10px) !important; min-width: 110px !important; display: flex !important; align-items: center !important; justify-content: center !important; gap: 6px !important; font-weight: 500 !important; }
.theme-toggle-btn:hover { background: rgba(255,255,255,0.2) !important; transform: translateY(-1px) !important; box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important; }
.theme-toggle-btn:active { transform: translateY(0) !important; }

/* ============================================================
   LOGIN SCREEN
   ============================================================ */
.login-container { min-height: 100vh !important; display: flex !important; align-items: center !important; justify-content: center !important; background: var(--bg-hero) !important; background-size: 400% 400% !important; animation: gradientShift 15s ease infinite !important; padding: 20px !important; margin: 0 !important; position: relative !important; overflow: hidden !important; }
.login-container::before { content: ''; position: absolute; width: 600px; height: 600px; border-radius: 50%; background: radial-gradient(circle, rgba(46, 117, 182, 0.08) 0%, transparent 70%); top: -200px; right: -200px; animation: float 6s ease-in-out infinite; }
.login-container::after { content: ''; position: absolute; width: 400px; height: 400px; border-radius: 50%; background: radial-gradient(circle, rgba(76, 175, 80, 0.05) 0%, transparent 70%); bottom: -100px; left: -100px; animation: float 6s ease-in-out infinite reverse; }
.login-card-wrapper { background: var(--bg-card) !important; backdrop-filter: blur(20px) !important; border-radius: var(--radius-xl) !important; padding: 40px !important; width: 420px !important; max-width: 100% !important; box-shadow: var(--shadow-xl) !important; animation: fadeInUp 0.6s ease-out !important; border: 1px solid var(--border-color) !important; position: relative !important; z-index: 1 !important; }
.login-card-wrapper .gr-box, .login-card-wrapper .gr-form, .login-card-wrapper .gr-panel, .login-card-wrapper label, .login-card-wrapper span, .login-card-wrapper .gr-text-input, .login-card-wrapper input, .login-card-wrapper textarea { color: var(--text-primary) !important; background: var(--bg-input) !important; border-color: var(--border-color) !important; }
.login-card-wrapper .gr-tabs { background: transparent !important; }
.login-card-wrapper .tab-nav button { color: var(--text-secondary) !important; }
.login-card-wrapper .tab-nav button.selected { color: var(--primary) !important; }
.login-icon { font-size: 56px; margin-bottom: 8px; display: inline-block; animation: float 3s ease-in-out infinite; }
.login-title { color: var(--text-primary); font-size: 28px; font-weight: 700; margin: 0; }
.login-subtitle { color: var(--text-secondary); font-size: 14px; margin: 4px 0 0 0; }
.login-security-badge { margin-top: 24px; padding: 12px 16px; background: var(--bg-hover); border: 1px solid var(--border-color); border-radius: 12px; font-size: 12px; color: var(--text-secondary); text-align: center; transition: all var(--transition); }
.login-security-badge:hover { border-color: var(--primary-light); box-shadow: 0 2px 8px rgba(46, 117, 182, 0.08); }

/* ============================================================
   HEADER
   ============================================================ */
.header-container { background: var(--bg-header) !important; background-size: 200% 200% !important; animation: gradientShift 8s ease infinite !important; padding: 14px 28px !important; display: flex !important; align-items: center !important; justify-content: space-between !important; border-bottom: 3px solid var(--accent) !important; box-shadow: 0 4px 20px rgba(0,0,0,0.15) !important; position: relative !important; z-index: 100 !important; }
.header-title { color: white !important; font-size: 22px !important; font-weight: 700 !important; display: flex !important; align-items: center !important; gap: 10px !important; }
.header-title-icon { font-size: 26px; animation: float 3s ease-in-out infinite; }
.header-subtitle { color: rgba(255,255,255,0.75) !important; font-size: 12px !important; margin: 1px 0 0 0 !important; font-weight: 400 !important; }
.header-status { display: flex !important; align-items: center !important; gap: 12px !important; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; transition: all var(--transition); }
.status-dot.online { background: #4CAF50; box-shadow: 0 0 10px rgba(76, 175, 80, 0.6); animation: pulse 2s infinite; }
.status-dot.offline { background: #F44336; box-shadow: 0 0 10px rgba(244, 67, 54, 0.6); }
.status-text { color: white !important; font-size: 12px !important; font-weight: 500 !important; }

/* ============================================================
   SIDEBAR
   ============================================================ */
.sidebar-container { background: var(--bg-sidebar) !important; border-radius: 0 !important; padding: 0 !important; min-height: calc(100vh - 80px); position: relative !important; }
.sidebar-container label, .sidebar-container span, .sidebar-container .gr-box, .sidebar-container .gr-form, .sidebar-container .gr-panel, .sidebar-container input, .sidebar-container textarea, .sidebar-container select, .sidebar-container option, .sidebar-container .gr-dropdown, .sidebar-container .gr-text-input, .sidebar-container .gr-number-input, .sidebar-container .gr-checkbox, .sidebar-container .gr-radio, .sidebar-container .gr-slider, .sidebar-container .gr-markdown, .sidebar-container .gr-markdown p, .sidebar-container .gr-markdown h1, .sidebar-container .gr-markdown h2, .sidebar-container .gr-markdown h3, .sidebar-container .gr-markdown strong, .sidebar-container .gr-markdown em, .sidebar-container .gr-markdown a, .sidebar-container .prose, .sidebar-container .prose p, .sidebar-container .prose h1, .sidebar-container .prose h2, .sidebar-container .prose h3 { color: var(--text-on-dark) !important; }
.sidebar-container input, .sidebar-container textarea, .sidebar-container select, .sidebar-container .gr-text-input input, .sidebar-container .gr-number-input input { background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.12) !important; color: white !important; border-radius: var(--radius-sm) !important; }
.sidebar-container input::placeholder, .sidebar-container textarea::placeholder { color: rgba(255,255,255,0.4) !important; }
.sidebar-container input:focus, .sidebar-container textarea:focus { border-color: var(--primary-light) !important; box-shadow: 0 0 0 3px rgba(46, 117, 182, 0.2) !important; background: rgba(255,255,255,0.12) !important; }
.sidebar-container .gr-dropdown { background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.12) !important; color: white !important; border-radius: var(--radius-sm) !important; }
.sidebar-container .gr-dropdown .gr-dropdown-label { color: var(--text-on-dark-muted) !important; }
.sidebar-container .gr-dropdown .options, .sidebar-container .gr-dropdown .dropdown-list { background: var(--bg-sidebar) !important; border-color: rgba(255,255,255,0.12) !important; }
.sidebar-container .gr-dropdown .options .item, .sidebar-container .gr-dropdown .dropdown-list .item { color: var(--text-on-dark) !important; background: transparent !important; }
.sidebar-container .gr-dropdown .options .item:hover, .sidebar-container .gr-dropdown .dropdown-list .item:hover { background: rgba(255,255,255,0.08) !important; color: white !important; }

/* Sidebar Buttons */
.sidebar-container button { font-weight: 700 !important; font-size: 14px !important; letter-spacing: 0.5px !important; border-radius: var(--radius-sm) !important; padding: 10px 20px !important; cursor: pointer !important; transition: all var(--transition) !important; text-transform: none !important; position: relative !important; overflow: hidden !important; color: white !important; border: 1.5px solid rgba(255,255,255,0.15) !important; }
#btn-new-project button { background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important; border: none !important; color: white !important; font-weight: 800 !important; font-size: 15px !important; box-shadow: 0 4px 15px rgba(5, 150, 105, 0.4) !important; padding: 10px 24px !important; }
#btn-new-project button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 25px rgba(5, 150, 105, 0.55) !important; background: linear-gradient(135deg, #047857 0%, #059669 100%) !important; }
#btn-delete-project button { background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%) !important; border: none !important; color: white !important; font-weight: 800 !important; font-size: 15px !important; box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4) !important; }
#btn-delete-project button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 25px rgba(220, 38, 38, 0.55) !important; background: linear-gradient(135deg, #B91C1C 0%, #DC2626 100%) !important; }
#btn-refresh button, #btn-logout button { background: rgba(255,255,255,0.12) !important; border: 1.5px solid rgba(255,255,255,0.25) !important; color: white !important; font-weight: 700 !important; font-size: 13px !important; padding: 9px 18px !important; backdrop-filter: blur(8px) !important; box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important; }
#btn-refresh button:hover, #btn-logout button:hover { background: rgba(255,255,255,0.22) !important; border-color: rgba(255,255,255,0.45) !important; transform: translateY(-2px) !important; box-shadow: 0 4px 16px rgba(0,0,0,0.25) !important; }
.sidebar-container .gr-accordion button.gr-button-primary { background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%) !important; border: none !important; font-weight: 800 !important; font-size: 15px !important; padding: 12px 24px !important; color: white !important; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important; width: 100% !important; text-shadow: 0 1px 2px rgba(0,0,0,0.15) !important; }
.sidebar-container .gr-accordion button.gr-button-primary:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 25px rgba(37, 99, 235, 0.55) !important; background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important; }
.sidebar-container .gr-accordion .gr-accordion-header { font-weight: 700 !important; font-size: 14px !important; color: white !important; background: rgba(255,255,255,0.06) !important; padding: 10px 16px !important; }
.sidebar-container .gr-label, .sidebar-container label { color: var(--text-on-dark-muted) !important; font-size: 12px !important; font-weight: 500 !important; }
.sidebar-container .gr-markdown, .sidebar-container .prose { color: var(--text-on-dark) !important; }
.sidebar-container .gr-accordion { background: rgba(255,255,255,0.04) !important; border-color: rgba(255,255,255,0.08) !important; }
.sidebar-section-title { color: var(--text-on-dark-muted) !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 1.2px !important; padding: 12px 16px 8px !important; border-bottom: 1px solid var(--border-light) !important; }
.sidebar-item { background: rgba(255,255,255,0.04) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: var(--radius-sm) !important; padding: 10px 14px !important; margin: 4px 16px !important; color: var(--text-on-dark) !important; font-size: 13px !important; transition: all var(--transition) !important; cursor: pointer !important; position: relative !important; overflow: hidden !important; }
.sidebar-item:hover { background: rgba(255,255,255,0.08) !important; border-color: rgba(46, 117, 182, 0.3) !important; transform: translateX(4px) !important; }
.sidebar-item .item-label { font-weight: 600 !important; color: white !important; margin-bottom: 2px !important; }
.sidebar-item .item-desc { color: var(--text-on-dark-muted) !important; font-size: 11px !important; }
.sidebar-stat { text-align: center !important; padding: 10px !important; transition: all var(--transition) !important; border-radius: var(--radius-sm) !important; flex: 1 !important; }
.sidebar-stat:hover { background: rgba(255,255,255,0.05) !important; transform: translateY(-2px) !important; }
.stat-value { font-size: 26px !important; font-weight: 700 !important; color: white !important; line-height: 1.2 !important; }
.stat-label { font-size: 10px !important; color: var(--text-on-dark-muted) !important; text-transform: uppercase !important; letter-spacing: 1px !important; margin-top: 2px !important; }

/* ============================================================
   CHAT AREA
   ============================================================ */
.chat-container { background: var(--bg-card) !important; border-radius: var(--radius-md) !important; box-shadow: var(--shadow-lg) !important; border: 1px solid var(--border-color) !important; margin: 16px !important; overflow: hidden !important; transition: all var(--transition) !important; }
.message-user, [data-testid="user"] { background: var(--bg-chat-user) !important; color: white !important; border-radius: 18px 18px 4px 18px !important; padding: 12px 18px !important; max-width: 80% !important; margin-left: auto !important; font-size: 14px !important; line-height: 1.5 !important; box-shadow: 0 2px 8px rgba(31, 78, 121, 0.2) !important; }
.message-assistant, [data-testid="bot"] { background: var(--bg-chat-assistant) !important; color: var(--text-primary) !important; border-radius: 18px 18px 18px 4px !important; padding: 12px 18px !important; max-width: 85% !important; font-size: 14px !important; line-height: 1.6 !important; border: 1px solid var(--border-color) !important; box-shadow: var(--shadow-sm) !important; }
.chat-input-wrapper input, .chat-input-wrapper textarea, .gr-text-input input, input[placeholder*="Ask about"] { border-radius: var(--radius-full) !important; border: 2px solid var(--border-color) !important; padding: 12px 20px !important; font-size: 14px !important; transition: all var(--transition) !important; background: var(--bg-input) !important; color: var(--text-primary) !important; }
.chat-input-wrapper input:focus, .gr-text-input input:focus, input[placeholder*="Ask about"]:focus { border-color: var(--primary-light) !important; box-shadow: 0 0 0 4px rgba(46, 117, 182, 0.12) !important; }
.chat-input-wrapper input::placeholder, input[placeholder*="Ask about"]::placeholder { color: var(--text-muted) !important; font-style: italic; }
.send-btn { background: var(--bg-chat-user) !important; border-radius: 50% !important; width: 46px !important; height: 46px !important; min-width: 46px !important; padding: 0 !important; display: flex !important; align-items: center !important; justify-content: center !important; box-shadow: 0 2px 8px rgba(31, 78, 121, 0.3) !important; transition: all var(--transition) !important; cursor: pointer !important; border: none !important; font-size: 20px !important; color: white !important; }
.send-btn:hover { transform: scale(1.12) !important; box-shadow: 0 4px 16px rgba(31, 78, 121, 0.4) !important; }
.send-btn:active { transform: scale(0.92) !important; }

/* ============================================================
   BUTTONS
   ============================================================ */
button.gr-button-primary, button.lg.primary { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%) !important; border: none !important; border-radius: var(--radius-sm) !important; padding: 10px 24px !important; font-weight: 600 !important; transition: all var(--transition) !important; color: white !important; position: relative !important; overflow: hidden !important; cursor: pointer !important; }
button.gr-button-primary:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(31, 78, 121, 0.3) !important; }
button.gr-button-primary:active { transform: translateY(0) !important; }
button.gr-button-secondary { background: transparent !important; border: 2px solid var(--border-color) !important; border-radius: var(--radius-sm) !important; padding: 8px 18px !important; transition: all var(--transition) !important; font-weight: 500 !important; color: var(--text-primary) !important; cursor: pointer !important; }
button.gr-button-secondary:hover { border-color: var(--primary-light) !important; color: var(--primary-light) !important; background: rgba(46, 117, 182, 0.04) !important; transform: translateY(-1px) !important; }

/* ============================================================
   TABS
   ============================================================ */
.tabs { border: none !important; }
.gr-tabs, .gr-tabs .tab-nav { background: transparent !important; }
.gr-tabs .tab-nav { border-bottom: 2px solid var(--border-color) !important; gap: 2px !important; padding: 0 16px !important; }
.gr-tabs .tab-nav button { border: none !important; background: transparent !important; color: var(--text-secondary) !important; padding: 12px 20px !important; font-weight: 500 !important; border-radius: 0 !important; transition: all var(--transition) !important; font-size: 14px !important; position: relative !important; }
.gr-tabs .tab-nav button::after { content: ''; position: absolute; bottom: -2px; left: 50%; width: 0; height: 2px; background: var(--primary); transition: all var(--transition); transform: translateX(-50%); }
.gr-tabs .tab-nav button:hover { color: var(--primary) !important; background: rgba(46, 117, 182, 0.04) !important; }
.gr-tabs .tab-nav button:hover::after { width: 60%; }
.gr-tabs .tab-nav button.selected { color: var(--primary) !important; font-weight: 600 !important; }
.gr-tabs .tab-nav button.selected::after { width: 80%; }

/* ============================================================
   FILE UPLOAD
   ============================================================ */
.file-upload, .gr-file { border: 2px dashed var(--border-color) !important; border-radius: var(--radius-lg) !important; padding: 32px !important; text-align: center !important; transition: all var(--transition) !important; background: var(--bg-card) !important; cursor: pointer !important; position: relative !important; }
.file-upload:hover, .gr-file:hover { border-color: var(--primary-light) !important; background: var(--bg-hover) !important; transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(46, 117, 182, 0.12) !important; }

/* ============================================================
   DATAFRAME / TABLE
   ============================================================ */
.gr-dataframe { border: 1px solid var(--border-color) !important; border-radius: var(--radius-md) !important; overflow: hidden !important; }
.gr-dataframe table { font-size: 13px !important; border-collapse: collapse !important; }
.gr-dataframe thead th { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%) !important; color: white !important; padding: 12px 14px !important; font-weight: 600 !important; font-size: 12px !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }
.gr-dataframe tbody td { padding: 10px 14px !important; border-bottom: 1px solid var(--border-color) !important; transition: background var(--transition-fast) !important; color: var(--text-primary) !important; }
.gr-dataframe tbody tr:hover td { background: var(--bg-hover) !important; }

/* ============================================================
   DROPDOWN (General)
   ============================================================ */
.gr-dropdown { border-radius: var(--radius-sm) !important; border: 2px solid var(--border-color) !important; transition: all var(--transition) !important; }
.gr-dropdown:focus-within { border-color: var(--border-focus) !important; box-shadow: 0 0 0 3px rgba(46, 117, 182, 0.12) !important; }

/* ============================================================
   ACCORDION
   ============================================================ */
.gr-accordion { border: 1px solid var(--border-color) !important; border-radius: var(--radius-sm) !important; margin: 8px 16px !important; overflow: hidden !important; transition: all var(--transition) !important; }
.gr-accordion:hover { border-color: rgba(46, 117, 182, 0.3) !important; }

/* ============================================================
   FOOTER
   ============================================================ */
.footer-text { text-align: center !important; padding: 16px !important; color: var(--text-muted) !important; font-size: 12px !important; border-top: 1px solid var(--border-color) !important; }

/* ============================================================
   TOOLTIP / INFO BOX
   ============================================================ */
.info-tip { background: rgba(46, 117, 182, 0.08) !important; border-left: 3px solid var(--primary-light) !important; border-radius: var(--radius-sm) !important; padding: 12px 16px !important; font-size: 13px !important; color: var(--text-secondary) !important; margin: 8px 0 !important; }

/* ============================================================
   MARKDOWN OVERRIDES
   ============================================================ */
.gr-markdown, .gr-markdown p, .prose, .prose p { color: var(--text-primary) !important; }
.gr-markdown h1, .gr-markdown h2, .gr-markdown h3, .gr-markdown h4, .gr-markdown strong, .prose h1, .prose h2, .prose h3, .prose strong { color: var(--text-primary) !important; }

/* ============================================================
   SCROLLBAR
   ============================================================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ============================================================
   RESPONSIVE
   ============================================================ */
@media (max-width: 768px) {
    .header-container { padding: 12px 16px !important; flex-wrap: wrap !important; gap: 8px !important; }
    .header-title { font-size: 18px !important; }
    .header-status { gap: 8px !important; }
    .sidebar-container { min-height: auto !important; }
    .login-card-wrapper { padding: 28px 20px !important; width: 100% !important; margin: 12px !important; }
    .message-user, .message-assistant { max-width: 90% !important; }
    .theme-toggle-btn { min-width: 40px !important; }
}

/* ============================================================
   ACCOUNTING REPORTS STYLES
   ============================================================ */
.report-card { background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px; margin-bottom:12px; transition:all var(--transition); }
.report-card:hover { box-shadow:var(--shadow-md); border-color:var(--primary-light); }
.report-table { width:100%; border-collapse:collapse; font-size:12px; }
.report-table th { background:var(--primary); color:white; padding:8px 12px; text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:0.5px; }
.report-table td { padding:6px 12px; border-bottom:1px solid var(--border-color); color:var(--text-primary); }
.report-table tr:hover td { background:var(--bg-hover); }

/* ============================================================
   ONBOARDING CHECKLIST STYLES
   ============================================================ */
.onboarding-step { margin-bottom:16px; background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:12px; transition:all var(--transition); }
.onboarding-step:hover { border-color:var(--primary-light); }
.onboarding-checkbox { width:18px; height:18px; cursor:pointer; accent-color:var(--primary-light); }
.onboarding-progress-bar { height:8px; background:var(--border-color); border-radius:4px; overflow:hidden; }
.onboarding-progress-fill { height:100%; background:linear-gradient(90deg, var(--primary-light), var(--accent)); border-radius:4px; transition:width 0.5s ease-out; }

/* ============================================================
   PROCESSING LOGS STYLES
   ============================================================ */
.log-entry { display:flex; gap:8px; padding:8px 12px; background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-sm); margin-bottom:4px; transition:all var(--transition-fast); }
.log-entry:hover { border-color:var(--primary-light); transform:translateX(4px); }
.log-status-badge { font-size:10px; font-weight:600; padding:2px 8px; border-radius:var(--radius-full); }

/* ============================================================
   VOICE INPUT STYLES
   ============================================================ */
.voice-btn { background:var(--bg-card) !important; border:2px solid var(--border-color) !important; border-radius:50% !important; width:42px !important; height:42px !important; min-width:42px !important; padding:0 !important; display:flex !important; align-items:center !important; justify-content:center !important; font-size:18px !important; cursor:pointer !important; transition:all var(--transition) !important; color:var(--text-primary) !important; }
.voice-btn:hover { border-color:var(--primary-light) !important; background:rgba(46,117,182,0.05) !important; transform:scale(1.1) !important; }
.voice-btn.listening { background:var(--danger) !important; border-color:var(--danger) !important; color:white !important; animation:pulse 1s infinite !important; }
.voice-btn.listening:hover { background:#DC2626 !important; }

/* ============================================================
   PENALTY CALCULATOR STYLES
   ============================================================ */
.penalty-item { background:var(--bg-hover); border:1px solid var(--border-color); border-radius:6px; padding:8px 12px; margin-bottom:6px; transition:all 0.2s; }
.penalty-item:hover { border-color:var(--primary-light); box-shadow:var(--shadow-sm); }
.penalty-header { display:flex; justify-content:space-between; align-items:center; }
.penalty-section { font-size:12px; font-weight:600; color:var(--primary); }
.penalty-amount { font-size:14px; font-weight:700; color:var(--danger); }
.penalty-desc { font-size:11px; color:var(--text-secondary); }
.penalty-meta { display:flex; gap:8px; font-size:10px; }

/* ============================================================
   FORECAST STYLES
   ============================================================ */
.forecast-month { background:var(--bg-hover); border:1px solid var(--border-color); border-radius:6px; padding:8px 12px; margin-bottom:6px; transition:all 0.2s; }
.forecast-month:hover { border-color:var(--primary-light); transform:translateX(4px); }
.forecast-bar-container { height:4px; background:var(--border-color); border-radius:2px; margin-top:6px; overflow:hidden; }
.forecast-bar { height:100%; border-radius:2px; transition:width 0.5s ease-out; }

/* ============================================================
   KNOWLEDGE BASE STYLES
   ============================================================ */
.kg-section { margin-bottom:16px; }
.kg-category-title { color:var(--primary); font-size:14px; font-weight:700; margin:0 0 8px 0; padding-bottom:6px; border-bottom:2px solid var(--primary-light); }
.kg-card { background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:10px 12px; margin-bottom:6px; transition:all var(--transition-fast); }
.kg-card:hover { border-color:var(--primary-light); transform:translateX(4px); }
.kg-card-header { display:flex; gap:8px; align-items:center; margin-bottom:4px; }
.kg-section-label { font-size:10px; font-weight:600; color:white; background:var(--primary-light); padding:2px 8px; border-radius:4px; }
.kg-subcategory { font-size:10px; color:var(--text-muted); }
.kg-card-title { font-size:13px; font-weight:600; color:var(--text-primary); margin-bottom:2px; }
.kg-card-content { font-size:11px; color:var(--text-secondary); line-height:1.4; }

/* ============================================================
   PROGRESS BAR STYLES
   ============================================================ */
.progress-container { background:var(--bg-card); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:16px; margin-bottom:12px; }
.progress-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.progress-title { font-size:13px; font-weight:600; color:var(--text-primary); }
.progress-value { font-size:14px; font-weight:700; color:var(--primary-light); }
.progress-bar-outer { height:8px; background:var(--border-color); border-radius:4px; overflow:hidden; }
.progress-bar-inner { height:100%; background:linear-gradient(90deg, var(--primary-light), var(--accent)); border-radius:4px; transition:width 0.5s ease-out; background-size:200% 200%; animation:gradientShift 2s ease infinite; }
.progress-detail { font-size:11px; color:var(--text-secondary); margin-top:6px; }

/* ============================================================
   TDS CALCULATOR SPECIFIC
   ============================================================ */
.tds-section { background:var(--bg-card); border:1px solid var(--border-color); border-radius:8px; padding:12px; margin-bottom:8px; transition:all 0.2s; }
.tds-section:hover { border-color:var(--primary-light); }
.tds-table { width:100%; border-collapse:collapse; font-size:11px; }
.tds-table th { background:var(--primary); color:white; padding:4px 8px; text-align:left; font-size:10px; }
.tds-table td { padding:3px 8px; border-bottom:1px solid var(--border-color); }

/* ============================================================
   GLOBAL ANIMATIONS EXTRA
   ============================================================ */
@keyframes scaleIn { from { opacity:0; transform:scale(0.9); } to { opacity:1; transform:scale(1); } }
.animate-scale-in { animation:scaleIn 0.3s ease-out both; }
@keyframes slideUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
.animate-slide-up { animation:slideUp 0.4s ease-out both; }

/* ============================================================
   TRANSITIONS FOR THEME SWITCHING
   ============================================================ */
.gradio-container, .gr-box, .gr-form, .gr-panel, .gr-tabs, .gr-tab-nav, .gr-accordion, .gr-dataframe, input, textarea, select, button, label, .gr-markdown, .prose, [data-testid="user"], [data-testid="bot"] {
    transition: background var(--transition), color var(--transition), border-color var(--transition), box-shadow var(--transition) !important;
}

""" + DASHBOARD_CSS + CALENDAR_CSS + TAX_CALCULATOR_CSS + HSN_LOOKUP_CSS + ACTIVITY_FEED_CSS + LOADING_CSS + PARTICLE_BG_CSS
