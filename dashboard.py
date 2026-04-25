import streamlit as st
import requests
import time

st.set_page_config(
    page_title="Hydroponic Home",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

FLASK_URL = "http://127.0.0.1:5000"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #e8f5e9;
    color: #1b3a2b;
}
.stApp {
    background: linear-gradient(135deg, #e8f5e9 0%, #d0f0d8 50%, #e8f5e9 100%);
}
.hydro-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
    border-bottom: 1px solid #1e3a1e;
    margin-bottom: 2rem;
}
.hydro-header h1 {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    color: #1b5e20;
    letter-spacing: 0.15em;
    margin: 0;
    text-shadow: 0 0 30px rgba(74, 222, 128, 0.3);
}
.hydro-header p {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: #4a6a4a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 0.4rem;
}
.pump-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: #4a6a4a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.pump-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: #6b8f6b;
    margin-bottom: 0.5rem;
    margin-top: 1rem;
}
.status-dot-on {
    display: inline-block;
    width: 10px; height: 10px;
    background: #4ade80;
    border-radius: 50%;
    box-shadow: 0 0 8px #4ade80;
    margin-right: 8px;
    animation: pulse 1.5s infinite;
}
.status-dot-off {
    display: inline-block;
    width: 10px; height: 10px;
    background: #4a6a4a;
    border-radius: 50%;
    margin-right: 8px;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
div[data-testid="stButton"] > button {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.1em !important;
    border-radius: 8px !important;
    border: 1px solid #1e3a1e !important;
    background: #ffffff !important;
    color: #2f855a !important;
    padding: 0.6rem 2rem !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    background: #1e3a1e !important;
    border-color: #4ade80 !important;
    box-shadow: 0 0 15px rgba(74, 222, 128, 0.2) !important;
}
.section-divider {
    border: none;
    border-top: 1px solid #1e3a1e;
    margin: 1.5rem 0;
}
.timestamp {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #2a4a2a;
    text-align: right;
    margin-top: 0.5rem;
}
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #cde5d3;
    border-radius: 12px;
    padding: 1.2rem !important;
    text-align: center;
}
[data-testid="stMetricLabel"] > div {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    color: #4a6a4a !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    width: 100%;
    text-align: center;
}
[data-testid="stMetricValue"] > div {
    font-family: 'Space Mono', monospace !important;
    font-size: 2rem !important;
    color: #1b5e20 !important;
    text-shadow: 0 0 20px rgba(74, 222, 128, 0.4);
    width: 100%;
    text-align: center;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] {display: none !important;}
[data-testid="collapsedControl"] {display: none !important;}
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

# ── Session state ──────────────────────────────────────────────────────────────
if "pump_filler" not in st.session_state:
    st.session_state.pump_filler = False
if "pump_suction" not in st.session_state:
    st.session_state.pump_suction = False

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hydro-header">
    <h1>🌿 Hydroponic Home</h1>
    <p>UNLV Senior Design · Hydroponic Monitoring System</p>
</div>
""", unsafe_allow_html=True)

# ── Sensor Cards ──────────────────────────────────────────────────────────────
data = get_latest_data()

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
        # Water Temp from DS18B20 — wired up 4/25/2026
        water_temp = fmt(data.get("water_temp_c", ""), 1)
        st.metric(label="🌊  Water Temp", value=f"{water_temp} °C")
    with col6:
        # Salinity — wired up 4/25/2026
        sal_ohm   = fmt(data.get("salinity_ohm", ""), 0)
        sal_label = data.get("salinity_type", "—")
        st.metric(label="🧂  Salinity", value=sal_label, delta=f"{sal_ohm} Ω")

    st.markdown(f'<div class="timestamp">Last reading · ms since boot: {ts}</div>', unsafe_allow_html=True)

else:
    st.warning("⚠️  No data — make sure app.py is running and the ESP32 is posting.")

# ── Pump Control ───────────────────────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown('<div class="pump-title">⚙ &nbsp; PUMP CONTROL</div>', unsafe_allow_html=True)

# — Filler Pump (D18) —
st.markdown('<div class="pump-label">💧 FILLER PUMP · D18</div>', unsafe_allow_html=True)
f_col1, f_col2, f_col3 = st.columns([1, 1, 3])
with f_col1:
    if st.button("▶  FILLER ON"):
        st.session_state.pump_filler = True
        send_pump_command(filler=True)
with f_col2:
    if st.button("■  FILLER OFF"):
        st.session_state.pump_filler = False
        send_pump_command(filler=False)
with f_col3:
    dot    = '<span class="status-dot-on"></span>' if st.session_state.pump_filler else '<span class="status-dot-off"></span>'
    status = "RUNNING" if st.session_state.pump_filler else "IDLE"
    color  = "#4ade80" if st.session_state.pump_filler else "#4a6a4a"
    st.markdown(f'<div style="padding:0.6rem 0;font-family:Space Mono,monospace;font-size:0.8rem;color:{color};">{dot} {status}</div>', unsafe_allow_html=True)

# — Suction Pump (D13) —
st.markdown('<div class="pump-label">🔄 SUCTION PUMP · D13</div>', unsafe_allow_html=True)
s_col1, s_col2, s_col3 = st.columns([1, 1, 3])
with s_col1:
    if st.button("▶  SUCTION ON"):
        st.session_state.pump_suction = True
        send_pump_command(suction=True)
with s_col2:
    if st.button("■  SUCTION OFF"):
        st.session_state.pump_suction = False
        send_pump_command(suction=False)
with s_col3:
    dot    = '<span class="status-dot-on"></span>' if st.session_state.pump_suction else '<span class="status-dot-off"></span>'
    status = "RUNNING" if st.session_state.pump_suction else "IDLE"
    color  = "#4ade80" if st.session_state.pump_suction else "#4a6a4a"
    st.markdown(f'<div style="padding:0.6rem 0;font-family:Space Mono,monospace;font-size:0.8rem;color:{color};">{dot} {status}</div>', unsafe_allow_html=True)

# ── AI Assistant Placeholder ───────────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown('<div class="pump-title">🤖 &nbsp; AI ASSISTANT</div>', unsafe_allow_html=True)

ai_col1, ai_col2 = st.columns([3, 1])

with ai_col1:
    st.markdown("""
    <div style="
        background: #ffffff;
        border: 1px solid #cde5d3;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
    ">
        <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#2f855a; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.8rem;">
            🌱 System Recommendation
        </div>
        <div style="font-family:'DM Sans',sans-serif; font-size:1rem; color:#2d3748; line-height:1.6;">
            System performance is within normal range. All sensors are reporting stable values. 
            Continue monitoring to maintain optimal plant health.
        </div>
    </div>
    """, unsafe_allow_html=True)

with ai_col2:
    st.markdown("""
<div style="
    background:#ffffff;
    border:1px solid #cde5d3;
    border-radius:12px;
    padding:1.2rem 1.5rem;
">
    <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#2f855a; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.8rem;">
        🌱 Live Recommendation
    </div>
    <div style="font-size:1rem; color:#2d3748; line-height:1.6;">
        Water level is stable. Humidity is slightly low. Consider increasing misting frequency by 10% to optimize plant growth.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Auto-refresh ───────────────────────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
refresh_col, _ = st.columns([1, 4])
with refresh_col:
    auto_refresh = st.toggle("Auto-refresh (5s)", value=True)

if auto_refresh:
    time.sleep(5)
    st.rerun()