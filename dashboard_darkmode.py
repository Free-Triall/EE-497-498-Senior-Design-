# ── Session state ──────────────────────────────────────────────────────────────
if "pump_filler" not in st.session_state:
    st.session_state.pump_filler = False
if "pump_suction" not in st.session_state:
    st.session_state.pump_suction = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

LIGHT_VARS = """
    --bg-gradient-start:   #e8f5e9;
    --bg-gradient-mid:     #d0f0d8;
    --bg-gradient-end:     #e8f5e9;
    --card-bg:             #ffffff;
    --card-border:         #cde5d3;
    --header-title:        #1b5e20;
    --header-sub:          #4a6a4a;
    --metric-value:        #1b5e20;
    --metric-label:        #4a6a4a;
    --metric-shadow:       rgba(74,222,128,0.4);
    --text-primary:        #1b3a2b;
    --divider:             #1e3a1e;
    --pump-label:          #6b8f6b;
    --pump-title:          #4a6a4a;
    --btn-bg:              #ffffff;
    --btn-color:           #2f855a;
    --btn-border:          #1e3a1e;
    --btn-hover-bg:        #1e3a1e;
    --btn-hover-shadow:    rgba(74,222,128,0.2);
    --ai-label:            #2f855a;
    --dot-off:             #4a6a4a;
    --status-off:          #4a6a4a;
    --ts-color:            #2a4a2a;
    --ohm-color:           #4a6a4a;
"""

DARK_VARS = """
    --bg-gradient-start:   #0a0f0a;
    --bg-gradient-mid:     #0d1a0d;
    --bg-gradient-end:     #0a0f0a;
    --card-bg:             #0f1f0f;
    --card-border:         #1a3a1a;
    --header-title:        #4ade80;
    --header-sub:          #2a6a2a;
    --metric-value:        #4ade80;
    --metric-label:        #2a5a2a;
    --metric-shadow:       rgba(74,222,128,0.3);
    --text-primary:        #4ade80;
    --divider:             #1a3a1a;
    --pump-label:          #2a6a2a;
    --pump-title:          #2a5a2a;
    --btn-bg:              #0f1f0f;
    --btn-color:           #4ade80;
    --btn-border:          #1a3a1a;
    --btn-hover-bg:        #1a3a1a;
    --btn-hover-shadow:    rgba(74,222,128,0.15);
    --ai-label:            #4ade80;
    --dot-off:             #1a4a1a;
    --status-off:          #1a5a1a;
    --ts-color:            #1a5a1a;
    --ohm-color:           #2a6a2a;
"""

active_vars = DARK_VARS if st.session_state.dark_mode else LIGHT_VARS

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {{
    {active_vars}
}}

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    color: var(--text-primary);
}}
.stApp {{
    background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-mid) 50%, var(--bg-gradient-end) 100%);
}}
.hydro-header {{
    text-align: center;
    padding: 2rem 0 1rem 0;
    border-bottom: 1px solid var(--divider);
    margin-bottom: 2rem;
}}
.hydro-header h1 {{
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    color: var(--header-title);
    letter-spacing: 0.15em;
    margin: 0;
    text-shadow: 0 0 30px rgba(74, 222, 128, 0.3);
}}
.hydro-header p {{
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: var(--header-sub);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 0.4rem;
}}
.pump-title {{
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: var(--pump-title);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}}
.pump-label {{
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: var(--pump-label);
    margin-bottom: 0.4rem;
    margin-top: 0.6rem;
}}
.status-dot-on {{
    display: inline-block;
    width: 10px; height: 10px;
    background: #4ade80;
    border-radius: 50%;
    box-shadow: 0 0 8px #4ade80;
    margin-right: 8px;
    animation: pulse 1.5s infinite;
}}
.status-dot-off {{
    display: inline-block;
    width: 10px; height: 10px;
    background: var(--dot-off);
    border-radius: 50%;
    margin-right: 8px;
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.4; }}
}}

/* Force ALL pump buttons to identical fixed size */
div[data-testid="stButton"] > button {{
    font-family: 'Space Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.08em !important;
    border-radius: 8px !important;
    border: 1px solid var(--btn-border) !important;
    background: var(--btn-bg) !important;
    color: var(--btn-color) !important;
    height: 2.6rem !important;
    min-height: 2.6rem !important;
    max-height: 2.6rem !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    transition: all 0.2s !important;
    box-sizing: border-box !important;
}}
div[data-testid="stButton"] > button:hover {{
    background: var(--btn-hover-bg) !important;
    border-color: #4ade80 !important;
    box-shadow: 0 0 15px var(--btn-hover-shadow) !important;
}}
/* Remove any padding Streamlit adds around button containers */
div[data-testid="stButton"] {{
    margin: 0 !important;
    padding: 0 !important;
}}

.section-divider {{
    border: none;
    border-top: 1px solid var(--divider);
    margin: 1.5rem 0;
}}
.timestamp {{
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: var(--ts-color);
    text-align: right;
    margin-top: 0.5rem;
}}
[data-testid="stMetric"] {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 1.2rem !important;
    text-align: left;
}}
[data-testid="stMetricLabel"] > div {{
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    color: var(--metric-label) !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    width: 100%;
    text-align: left;
}}
[data-testid="stMetricValue"] > div {{
    font-family: 'Space Mono', monospace !important;
    font-size: 2rem !important;
    color: var(--metric-value) !important;
    text-shadow: 0 0 20px var(--metric-shadow);
    width: 100%;
    text-align: left;
}}

/* Custom salinity card matches st.metric exactly */
.sal-card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: left;
    position: relative;
}}
.sal-label {{
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: var(--metric-label);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    text-align: left;
    margin-bottom: 0.4rem;
}}
.sal-value {{
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    color: var(--metric-value);
    text-shadow: 0 0 20px var(--metric-shadow);
    text-align: left;
}}
.sal-ohm {{
    position: absolute;
    top: 0.5rem;
    right: 0.7rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: var(--ohm-color);
    letter-spacing: 0.05em;
}}

/* Toggle label — aggressive catch for all Streamlit versions */
p, span, label, div {{
    color: inherit;
}}
[data-testid="stToggle"] p,
[data-testid="stToggle"] span,
[data-testid="stToggle"] label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
[class*="stWidgetLabel"] p,
[class*="stWidgetLabel"] span,
[class*="stWidgetLabel"] {{
    color: var(--pump-title) !important;
    font-family: 'Space Mono', monospace !important;
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
[data-testid="stSidebar"] {{display: none !important;}}
[data-testid="collapsedControl"] {{display: none !important;}}
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_latest_data():
    try:
        r = requests.get(f"{FLASK_URL}/data?n=1", timeout=3)
        if r.status_code == 200:
            rows = r.json().get("rows", [])
            return rows[-1] if rows else None
    except Exception:
        return None

def send_pump_command(filler=None, suction=None):
    try:
        payload = {}
        if filler is not None:
            payload["filler"] = filler
        if suction is not None:
            payload["suction"] = suction
        requests.post(f"{FLASK_URL}/pump", json=payload, timeout=3)
    except Exception:
        pass

def fmt(val, decimals=1):
    try:
        return f"{float(val):.{decimals}f}"
    except:
        return "—"

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hydro-header">
    <h1>🌿 Hydroponic Home</h1>
    <p>UNLV Senior Design · Hydroponic Monitoring System</p>
</div>
""", unsafe_allow_html=True)

# ── Sensor Cards ──────────────────────────────────────────────────────────────
data = get_latest_data()

card_bg     = "#0f1f0f" if st.session_state.dark_mode else "#ffffff"
card_border = "#1a3a1a" if st.session_state.dark_mode else "#cde5d3"
ai_label    = "#4ade80" if st.session_state.dark_mode else "#2f855a"
ai_text     = "#3aaa5a" if st.session_state.dark_mode else "#2d3748"

if data:
    temp  = fmt(data.get("temp_c",   ""), 1)
    humid = fmt(data.get("moisture", ""), 1)
    tds   = fmt(data.get("tds_ppm",  ""), 1)
    ts    = data.get("timestamp", "—")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric(label="🌡️  Ambient Temp", value=f"{temp} °C")
    with col2:
        st.metric(label="💧  Humidity", value=f"{humid} %")
    with col3:
        st.metric(label="🧪  TDS", value=f"{tds} ppm")
    with col4:
        dist  = data.get("water_dist_cm", "")
        w_low = data.get("water_low", "false")
        if w_low == "true":
            st.metric(label="🪣  Water Level", value="⚠️ LOW", delta="Refill!")
        else:
            wval = fmt(dist, 1)
            st.metric(label="🪣  Water Level", value=f"{wval} cm")
    with col5:
        water_temp = fmt(data.get("water_temp_c", ""), 1)
        st.metric(label="🌊  Water Temp", value=f"{water_temp} °C")
    with col6:
        sal_ohm   = fmt(data.get("salinity_ohm", ""), 0)
        sal_label = data.get("salinity_type", "—")
        # Custom card so we can put Ω in the top-right corner
        st.markdown(f"""
        <div class="sal-card">
            <div class="sal-ohm">{sal_ohm} Ω</div>
            <div class="sal-label">🧂&nbsp; Salinity</div>
            <div class="sal-value">{sal_label}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f'<div class="timestamp">Last reading · ms since boot: {ts}</div>', unsafe_allow_html=True)

else:
    st.warning("⚠️  No data — make sure app.py is running and the ESP32 is posting.")

# ── Pump Control + AI Assistant (same row) ─────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

pump_col, ai_col = st.columns([2, 3])

with pump_col:
    st.markdown('<div class="pump-title">⚙ &nbsp; PUMP CONTROL</div>', unsafe_allow_html=True)

    # — Filler Pump (D18) —
    st.markdown('<div class="pump-label">💧 FILLER PUMP · D18</div>', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        if st.button("▶ FILLER ON", key="filler_on", use_container_width=True):
            st.session_state.pump_filler = True
            send_pump_command(filler=True)
    with f_col2:
        if st.button("■ FILLER OFF", key="filler_off", use_container_width=True):
            st.session_state.pump_filler = False
            send_pump_command(filler=False)
    with f_col3:
        dot    = '<span class="status-dot-on"></span>' if st.session_state.pump_filler else '<span class="status-dot-off"></span>'
        status = "RUNNING" if st.session_state.pump_filler else "IDLE"
        color  = "#4ade80" if st.session_state.pump_filler else "var(--status-off)"
        st.markdown(f'<div style="height:2.6rem;display:flex;align-items:center;font-family:Space Mono,monospace;font-size:0.78rem;color:{color};">{dot}{status}</div>', unsafe_allow_html=True)

    # — Suction Pump (D13) —
    st.markdown('<div class="pump-label">🔄 SUCTION PUMP · D13</div>', unsafe_allow_html=True)
    s_col1, s_col2, s_col3 = st.columns([1, 1, 1])
    with s_col1:
        if st.button("▶ SUCTION ON", key="suction_on", use_container_width=True):
            st.session_state.pump_suction = True
            send_pump_command(suction=True)
    with s_col2:
        if st.button("■ SUCTION OFF", key="suction_off", use_container_width=True):
            st.session_state.pump_suction = False
            send_pump_command(suction=False)
    with s_col3:
        dot    = '<span class="status-dot-on"></span>' if st.session_state.pump_suction else '<span class="status-dot-off"></span>'
        status = "RUNNING" if st.session_state.pump_suction else "IDLE"
        color  = "#4ade80" if st.session_state.pump_suction else "var(--status-off)"
        st.markdown(f'<div style="height:2.6rem;display:flex;align-items:center;font-family:Space Mono,monospace;font-size:0.78rem;color:{color};">{dot}{status}</div>', unsafe_allow_html=True)

with ai_col:
    st.markdown(f'<div class="pump-title" style="color: var(--header-title); text-shadow: 0 0 10px rgba(74,222,128,0.8), 0 0 20px rgba(74,222,128,0.4);">🤖 &nbsp; GLADOS * HYDROPONIC SYSTEM AI</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:0.6rem; min-height:5.5rem;">
        <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:{ai_label}; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.6rem;">
            🌱 System Health
        </div>
        <div style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:{ai_text}; line-height:1.6;">
            System integrity confirmed. Environmental variables remain within acceptable thresholds. No intervention necessary. Monitoring will continue.
        </div>
    </div>
    <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:12px; padding:1.2rem 1.5rem; min-height:5.5rem;">
        <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:{ai_label}; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.6rem;">
            🌱 Live Optimization
        </div>
        <div style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:{ai_text}; line-height:1.6;">
            Environmental drift detected in humidity levels. Increasing misting frequency is advised to restore optimal growth conditions.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Auto-refresh + Dark Mode Toggle (same row) ─────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
refresh_col, _, dark_col = st.columns([2, 5, 1])
with refresh_col:
    if st.session_state.dark_mode:
        toggle_color = "#4ade80"
        toggle_glow  = "0 0 8px rgba(74,222,128,0.6)"
    else:
        toggle_color = "#1b5e20"
        toggle_glow  = "none"
    st.markdown(f"""<style>
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    [data-testid="stWidgetLabel"] {{
        color: {toggle_color} !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.1em !important;
        text-shadow: {toggle_glow} !important;
    }}
    </style>""", unsafe_allow_html=True)
    auto_refresh = st.toggle("Auto refresh (5s)", value=True)
with dark_col:
    icon = "☀️ Light" if st.session_state.dark_mode else "🌙 Dark"
    if st.button(icon, key="theme_toggle", use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

if auto_refresh:
    time.sleep(5)
    st.rerun()
