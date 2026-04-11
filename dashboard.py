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
    background-color: #0a0f0a;
    color: #e0ead0;
}
.stApp {
    background: linear-gradient(135deg, #0a0f0a 0%, #0d1a10 50%, #0a0f0a 100%);
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
    color: #4ade80;
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
    margin-bottom: 1rem;
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
    background: #111a11 !important;
    color: #4ade80 !important;
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
    background: linear-gradient(145deg, #111a11, #0d150d);
    border: 1px solid #1e3a1e;
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
    color: #4ade80 !important;
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

def get_latest_data():
    try:
        r = requests.get(f"{FLASK_URL}/data?n=1", timeout=3)
        if r.status_code == 200:
            rows = r.json().get("rows", [])
            return rows[-1] if rows else None
    except Exception:
        return None

def send_pump_command(state: bool):
    try:
        requests.post(f"{FLASK_URL}/pump", json={"on": state}, timeout=3)
    except Exception:
        pass

def fmt(val, decimals=1):
    try:
        return f"{float(val):.{decimals}f}"
    except:
        return "—"

if "pump_on" not in st.session_state:
    st.session_state.pump_on = False

st.markdown("""
<div class="hydro-header">
    <h1>🌿 Hydroponic Home</h1>
    <p>UNLV Senior Design · Hydroponic Monitoring System</p>
</div>
""", unsafe_allow_html=True)

data = get_latest_data()

if data:
    temp  = fmt(data.get("temp_c",   ""), 1)
    humid = fmt(data.get("moisture", ""), 1)
    tds   = fmt(data.get("tds_ppm",  ""), 1)
    ts    = data.get("timestamp", "—")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="🌡️  Ambient Temp", value=f"{temp} °C")
    with col2:
        st.metric(label="💧  Humidity", value=f"{humid} %")
    with col3:
        st.metric(label="🧪  TDS", value=f"{tds} ppm")
    with col4:
        st.metric(label="🪣  Water Level", value="OK")

    st.markdown(f'<div class="timestamp">Last reading · ms since boot: {ts}</div>', unsafe_allow_html=True)

else:
    st.warning("⚠️  No data — make sure app.py is running and the ESP32 is posting.")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown('<div class="pump-title">⚙ &nbsp; PUMP CONTROL</div>', unsafe_allow_html=True)

pump_col1, pump_col2, pump_col3 = st.columns([1, 1, 3])

with pump_col1:
    if st.button("▶  PUMP ON"):
        st.session_state.pump_on = True
        send_pump_command(True)

with pump_col2:
    if st.button("■  PUMP OFF"):
        st.session_state.pump_on = False
        send_pump_command(False)

with pump_col3:
    dot = '<span class="status-dot-on"></span>' if st.session_state.pump_on else '<span class="status-dot-off"></span>'
    status_text  = "RUNNING" if st.session_state.pump_on else "IDLE"
    status_color = "#4ade80" if st.session_state.pump_on else "#4a6a4a"
    st.markdown(f"""
    <div style="padding:0.6rem 0; font-family:'Space Mono',monospace; font-size:0.8rem; color:{status_color};">
        {dot} PUMP STATUS: {status_text}
    </div>""", unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
refresh_col, _ = st.columns([1, 4])
with refresh_col:
    auto_refresh = st.toggle("Auto-refresh (5s)", value=True)

if auto_refresh:
    time.sleep(5)
    st.rerun()