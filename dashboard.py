import streamlit as st
import requests
import time
import csv
import os
import json

st.set_page_config(
    page_title="Hydroponic Home",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

FLASK_URL = "http://127.0.0.1:5000"
DATA_FILE   = "sensor_data.csv"
CONFIG_FILE = "hydro_config.json"

# ── Config helpers ─────────────────────────────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return None

def save_config(water_type, baseline_tds):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"water_type": water_type, "baseline_tds": baseline_tds}, f)

# ── CSV fallback (reads last row directly — works without ESP32/hotspot) ────────
def get_hardcoded_optimization(tds_ppm, water_dist_cm, water_low, salinity_type, water_temp_c, moisture, temp_c, baseline_tds):
    """Rule-based optimization message based on sensor values."""
    try:
        tds      = float(tds_ppm)
        dist     = float(water_dist_cm)
        wtemp    = float(water_temp_c)
        humid    = float(moisture)
        atemp    = float(temp_c)
        baseline = float(baseline_tds)
        w_low    = str(water_low).lower() == "true"
        sal      = str(salinity_type).lower()
    except:
        return "Unable to read sensor values."

    if sal in ["seawater", "sea water"]:
        return "⚠️ Seawater detected — drain and refill with fresh water immediately. Plants will not survive in this salinity."
    if w_low or dist > 50:
        return "🪣 Reservoir critically low — refill with fresh water now to prevent pump damage and plant stress."
    if dist > 15:
        return "🪣 Water level getting low — top off the reservoir soon."
    if wtemp > 25:
        return "🌊 Water temperature is too high — add ice packs or a water chiller to bring it below 22°C."
    if tds < baseline - 100:
        return "🧪 Nutrient levels are depleted — add hydroponic nutrient solution to raise TDS above your baseline."
    if tds > baseline + 800:
        return "🧪 Nutrient concentration is critically high — dilute with fresh water to avoid nutrient burn."
    if tds > baseline + 400:
        return "🧪 TDS is elevated — consider a partial water change to balance nutrient levels."
    if atemp > 28:
        return "🌡️ Ambient temperature is too high — improve ventilation or add a fan to keep plants below 26°C."
    if humid < 40:
        return "💧 Humidity is low — increase misting frequency or add a humidifier to reach 50–70%."
    return "✅ All parameters are within healthy ranges — no action needed at this time."

# ── CSV fallback ───────────────────────────────────────────────────────────────
def get_latest_from_csv():
    """Read the last row of sensor_data.csv directly."""
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else None
    """Read the last row of sensor_data.csv directly. Edit this row to demo AI."""
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-1] if rows else None

# ── AI analysis via Anthropic API ───────────────────────────────────────────────
def get_ai_analysis(temp_c, moisture, tds_ppm, water_dist_cm, water_low,
                    salinity_ohm, salinity_type, water_temp_c, baseline_tds, water_type):
    """Call local Ollama (llama3.2) to analyze sensor data."""
    try:
        try:
            tds_val      = float(tds_ppm)
            baseline_val = float(baseline_tds)
            tds_above    = round(tds_val - baseline_val, 1)
            tds_status   = (
                "SEAWATER_DETECTED" if str(salinity_type).lower() in ["seawater", "sea water"]
                else "CRITICALLY_HIGH" if tds_val > baseline_val + 800
                else "HIGH"           if tds_val > baseline_val + 400
                else "GOOD"           if tds_val > baseline_val + 100
                else "LOW_NEEDS_NUTRIENTS" if tds_val <= baseline_val + 50
                else "NORMAL"
            )
        except:
            tds_above  = "unknown"
            tds_status = "UNKNOWN"

        prompt = f"""You are Glados, an AI assistant for a home hydroponic system called Hydroponic Home.

Analyze these live sensor readings:
- Ambient temperature: {temp_c} °C
- Humidity: {moisture} %
- TDS (nutrients): {tds_ppm} ppm
- User baseline TDS ({water_type} water): {baseline_tds} ppm
- TDS above baseline: {tds_above} ppm
- TDS status: {tds_status}
- Water distance from sensor: {water_dist_cm} cm
- Water level low alert: {water_low}
- Salinity: {salinity_ohm} Ω ({salinity_type})
- Water temperature: {water_temp_c} °C

Rules:
- Healthy ambient temp: 18-26°C, Humidity: 50-70%, Water temp: 18-22°C
- water_dist_cm: under 15cm = tank full, over 15cm = getting low, over 50cm = critically low
- water_low=True means refill needed
- TDS status SEAWATER_DETECTED = tell user to immediately drain and refill with fresh water, plants will die
- TDS status LOW_NEEDS_NUTRIENTS = user needs to add nutrient solution now
- TDS status HIGH or CRITICALLY_HIGH = too many nutrients, dilute with fresh water
- TDS status GOOD = nutrient levels healthy, no action needed
- Always base TDS recommendations on the difference from the user's baseline, not absolute values

Respond ONLY with a JSON object, no extra text, no markdown:
{{"health": "1-2 sentence overall system health summary. You MUST mention the most out-of-range value by name.", "optimization": "1-2 sentence actionable recommendation focused specifically on the single most urgent issue. Be direct and specific."}}"""

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2", "prompt": prompt, "stream": False},
            timeout=30
        )
        text = response.json().get("response", "").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result.get("health", "Analysis unavailable."), result.get("optimization", "No recommendations.")
    except Exception as e:
        return f"AI unavailable: {e}", "Make sure Ollama is running and llama3.2 is installed."

# ── Session state ──────────────────────────────────────────────────────────────
if "pump_filler" not in st.session_state:
    st.session_state.pump_filler = False
if "pump_suction" not in st.session_state:
    st.session_state.pump_suction = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # light | dark | discord_dark | discord_light
if "ai_cache" not in st.session_state:
    st.session_state.ai_cache = {}
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = load_config() is not None

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

DISCORD_DARK_VARS = """
    --bg-gradient-start:   #313338;
    --bg-gradient-mid:     #2b2d31;
    --bg-gradient-end:     #1e1f22;
    --card-bg:             #2b2d31;
    --card-border:         #1e1f22;
    --header-title:        #ffffff;
    --header-sub:          #b5bac1;
    --metric-value:        #ffffff;
    --metric-label:        #b5bac1;
    --metric-shadow:       rgba(88,101,242,0.3);
    --text-primary:        #dbdee1;
    --divider:             #1e1f22;
    --pump-label:          #b5bac1;
    --pump-title:          #b5bac1;
    --btn-bg:              #4e5058;
    --btn-color:           #ffffff;
    --btn-border:          #1e1f22;
    --btn-hover-bg:        #5865f2;
    --btn-hover-shadow:    rgba(88,101,242,0.3);
    --ai-label:            #5865f2;
    --dot-off:             #4e5058;
    --status-off:          #b5bac1;
    --ts-color:            #b5bac1;
    --ohm-color:           #b5bac1;
"""

DISCORD_LIGHT_VARS = """
    --bg-gradient-start:   #f2f3f5;
    --bg-gradient-mid:     #e3e5e8;
    --bg-gradient-end:     #f2f3f5;
    --card-bg:             #ffffff;
    --card-border:         #e3e5e8;
    --header-title:        #313338;
    --header-sub:          #4e5058;
    --metric-value:        #313338;
    --metric-label:        #4e5058;
    --metric-shadow:       rgba(88,101,242,0.2);
    --text-primary:        #2e3338;
    --divider:             #e3e5e8;
    --pump-label:          #4e5058;
    --pump-title:          #4e5058;
    --btn-bg:              #ffffff;
    --btn-color:           #313338;
    --btn-border:          #e3e5e8;
    --btn-hover-bg:        #5865f2;
    --btn-hover-shadow:    rgba(88,101,242,0.2);
    --ai-label:            #5865f2;
    --dot-off:             #4e5058;
    --status-off:          #4e5058;
    --ts-color:            #4e5058;
    --ohm-color:           #4e5058;
"""

THEME_VARS = {
    "light":          LIGHT_VARS,
    "dark":           DARK_VARS,
    "discord_dark":   DISCORD_DARK_VARS,
    "discord_light":  DISCORD_LIGHT_VARS,
}

active_vars = THEME_VARS.get(st.session_state.theme, LIGHT_VARS)
# keep dark_mode in sync for legacy code that references it
st.session_state.dark_mode = st.session_state.theme in ("dark", "discord_dark")

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
    """Try Flask first; fall back to reading sensor_data.csv directly."""
    try:
        r = requests.get(f"{FLASK_URL}/data?n=1", timeout=3)
        if r.status_code == 200:
            rows = r.json().get("rows", [])
            if rows:
                return rows[-1], "flask"
    except Exception:
        pass
    row = get_latest_from_csv()
    return (row, "csv") if row else (None, None)

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
data, data_source = get_latest_data()

card_bg     = "var(--card-bg)"
card_border = "var(--card-border)"
ai_label    = "var(--ai-label)"
ai_text     = "var(--text-primary)"

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

# ── Pump Control + AI Assistant ──────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

pump_col, ai_col = st.columns([2, 3])

with pump_col:
    st.markdown('<div class="pump-title">⚙ &nbsp; PUMP CONTROL</div>', unsafe_allow_html=True)

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
    st.markdown(f'<div class="pump-title" style="color: var(--header-title); text-shadow: 0 0 10px rgba(74,222,128,0.8), 0 0 20px rgba(74,222,128,0.4);">🤖 &nbsp; Glados · HYDROPONIC SYSTEM AI</div>', unsafe_allow_html=True)

    if data:
        cfg          = load_config()
        baseline_tds = cfg.get("baseline_tds", 0) if cfg else 0
        water_type   = cfg.get("water_type", "Unknown") if cfg else "Unknown"

        sensor_key = f"{data.get('temp_c')}|{data.get('moisture')}|{data.get('tds_ppm')}|{data.get('water_dist_cm')}|{data.get('water_low')}|{data.get('salinity_ohm')}|{data.get('salinity_type')}|{data.get('water_temp_c')}"
        if sensor_key not in st.session_state.ai_cache:
            health_msg, _ = get_ai_analysis(
                data.get("temp_c", ""),
                data.get("moisture", ""),
                data.get("tds_ppm", ""),
                data.get("water_dist_cm", ""),
                data.get("water_low", ""),
                data.get("salinity_ohm", ""),
                data.get("salinity_type", ""),
                data.get("water_temp_c", ""),
                baseline_tds,
                water_type,
            )
            st.session_state.ai_cache[sensor_key] = health_msg
        else:
            health_msg = st.session_state.ai_cache[sensor_key]

        optim_msg = get_hardcoded_optimization(
            data.get("tds_ppm", ""),
            data.get("water_dist_cm", ""),
            data.get("water_low", ""),
            data.get("salinity_type", ""),
            data.get("water_temp_c", ""),
            data.get("moisture", ""),
            data.get("temp_c", ""),
            baseline_tds,
        )
    else:
        health_msg = "No sensor data available."
        optim_msg  = "Edit sensor_data.csv or start the ESP32 to begin."

    st.markdown(f"""
    <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:0.6rem; min-height:5.5rem;">
        <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:{ai_label}; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.6rem;">
            🌱 System Health
        </div>
        <div style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:{ai_text}; line-height:1.6;">
            {health_msg}
        </div>
    </div>
    <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:12px; padding:1.2rem 1.5rem; min-height:5.5rem;">
        <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:{ai_label}; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.6rem;">
            🌱 Live Optimization
        </div>
        <div style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:{ai_text}; line-height:1.6;">
            {optim_msg}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Auto-refresh + Theme Buttons ─────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
refresh_col, _ = st.columns([3, 7])
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

st.markdown('<div class="pump-title">🎨 &nbsp; THEME SELECTOR</div>', unsafe_allow_html=True)

t1, t2, t3, t4 = st.columns(4)
with t1:
    if st.button("🌿 Garden", key="theme_light", use_container_width=True):
        st.session_state.theme = "light"
        st.rerun()
with t2:
    if st.button("🌑 Grove", key="theme_dark", use_container_width=True):
        st.session_state.theme = "dark"
        st.rerun()
with t3:
    if st.button("🌙 Midnight", key="theme_dd", use_container_width=True):
        st.session_state.theme = "discord_dark"
        st.rerun()
with t4:
    if st.button("☁️ Cloud", key="theme_dl", use_container_width=True):
        st.session_state.theme = "discord_light"
        st.rerun()

if auto_refresh:
    time.sleep(5)
    st.rerun()