import os, csv, time, json
from flask import Flask, request, jsonify

app = Flask(__name__)

DATA_FILE = "sensor_data.csv"
API_KEY = os.getenv("API_KEY")

# Pump states added 4/11/26
pump_state = {"filler": False, "suction": False}

HEADERS = ["device_id", "timestamp", "temp_c", "moisture", "tds_ppm", "water_dist_cm", "water_low", "salinity_ohm", "salinity_type", "water_temp_c", "raw_json"]  # salinity + water_temp added 4/25/2026

def ensure_csv():
    """Create CSV with headers if missing, or fix it if header row is absent."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="") as f:
            csv.writer(f).writerow(HEADERS)
    else:
        with open(DATA_FILE, "r", newline="") as f:
            first_line = f.readline().strip()
        if first_line != ",".join(HEADERS):
            # Header missing — prepend it
            with open(DATA_FILE, "r") as f:
                existing = f.read()
            with open(DATA_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(HEADERS)
                f.write(existing)

ensure_csv()

@app.get("/health")
def health():
    return jsonify(ok=True, ts=int(time.time()))

@app.post("/ingest")
def ingest():
    if API_KEY:
        if request.headers.get("X-API-Key", "") != API_KEY:
            return jsonify(ok=False, error="unauthorized"), 401

    if not request.is_json:
        return jsonify(ok=False, error="expected application/json"), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(ok=False, error="invalid json"), 400

    device_id = str(data.get("device_id", ""))
    timestamp = str(data.get("timestamp", ""))
    readings  = data.get("readings", {}) if isinstance(data.get("readings"), dict) else {}

    temp_c        = readings.get("temp_c")
    moisture      = readings.get("moisture")
    #ph            = readings.get("ph")
    tds_ppm       = readings.get("tds_ppm")
    water_dist_cm = readings.get("water_dist_cm")
    water_low     = readings.get("water_low")
    salinity_ohm  = readings.get("salinity_ohm")   # added 4/25/2026
    salinity_type = readings.get("salinity_type")   # added 4/25/2026
    water_temp_c  = readings.get("water_temp_c")    # added 4/25/2026

    with open(DATA_FILE, "a", newline="") as f:
        csv.writer(f).writerow([device_id, timestamp, temp_c, moisture, tds_ppm, water_dist_cm, water_low, salinity_ohm, salinity_type, water_temp_c, json.dumps(data)])  # added 4/25/2026

    return jsonify(ok=True, stored=True)

@app.get("/data")
def data_view():
    try:
        n = int(request.args.get("n", "10"))
    except ValueError:
        n = 10

    rows = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline="") as f:
            rows = [
                {k: (v if v is not None else "") for k, v in row.items()}
                for row in list(csv.DictReader(f))[-n:]
            ]
    return jsonify(ok=True, count=len(rows), rows=rows)

@app.post("/pump") # added 4/11/26
def pump_control():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(ok=False, error="invalid json"), 400
    if "filler" in data:
        pump_state["filler"] = bool(data["filler"])
    if "suction" in data:
        pump_state["suction"] = bool(data["suction"])
    print(f"[PUMP] Filler: {pump_state['filler']} | Suction: {pump_state['suction']}")
    return jsonify(ok=True, **pump_state)

@app.get("/pump/state") #added 4/11/26
def pump_state_view():
    # ESP32 polls this every loop
    return jsonify(ok=True, **pump_state)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)