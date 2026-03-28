import os, csv, time, json
from flask import Flask, request, jsonify

app = Flask(__name__)

DATA_FILE = "sensor_data.csv"
API_KEY = os.getenv("API_KEY")

HEADERS = ["device_id", "timestamp", "temp_c", "moisture", "ph", "tds_ppm", "raw_json"]

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

    temp_c   = readings.get("temp_c")
    moisture = readings.get("moisture")
    ph       = readings.get("ph")
    tds_ppm  = readings.get("tds_ppm")

    with open(DATA_FILE, "a", newline="") as f:
        csv.writer(f).writerow([device_id, timestamp, temp_c, moisture, ph, tds_ppm, json.dumps(data)])

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

@app.post("/pump")
def pump_control():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(ok=False, error="invalid json"), 400
    state = data.get("on", False)
    print(f"[PUMP] {'ON' if state else 'OFF'}")
    return jsonify(ok=True, pump_on=state)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)