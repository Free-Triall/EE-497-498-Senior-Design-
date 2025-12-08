import os, csv, time, json #import the commands for working with an os, csv, time and json file.
from flask import Flask, request, jsonify

app = Flask(__name__)

DATA_FILE = "sensor_data.csv" #creating csv here
API_KEY = os.getenv("API_KEY") 

def ensure_csv(): #checks to make sure if csv actually exists
    if not os.path.exists(DATA_FILE): #if not create csv and add these columns
        with open(DATA_FILE, "w", newline="") as f:
            w = csv.writer(f)
            #ADD SENSOR STUFF HEREE
            w.writerow([
                "device_id", #device number
                "timestamp", #timestamp of taken data
                "temp_c", #temperature reading from *DHT32*
                "moisture", #moisture reading from *DHT32*
                "ph", #N/A yet
                "tds_ppm", #Added as of 11/15/25 *TDS Sensor*
                "raw_json" #Json file
                ])
ensure_csv() #function call

@app.get("/health") #checks to make sure FLASK is running if it is sends terminal message
def health():
    return jsonify(ok=True, ts=int(time.time()))

@app.post("/ingest")
def ingest(): #function to read sensor data

    # optional header authentication
    # Doesnt do anything in this case
    if API_KEY:
        if request.headers.get("X-API-Key","") != API_KEY: 
            return jsonify(ok=False, error="unauthorized"), 401

    if not request.is_json: #makes sure request is indeed a json file
        return jsonify(ok=False, error="expected application/json"), 400

    data = request.get_json(silent=True) #makes sure json sent is a dictionary
    if not isinstance(data, dict):
        return jsonify(ok=False, error="invalid json"), 400

    #Sensor data here
    device_id = str(data.get("device_id",""))
    timestamp = str(data.get("timestamp",""))
    readings = data.get("readings", {}) if isinstance(data.get("readings"), dict) else {}

    temp_c = readings.get("temp_c")
    moisture = readings.get("moisture")
    ph = readings.get("ph")
    tds_ppm = readings.get("tds_ppm") #Added as of 11/15/25 *TDS Sensor*

    # append a row
    with open(DATA_FILE, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow([device_id, timestamp, temp_c, moisture, ph, tds_ppm, json.dumps(data)])
        # Added as of 11/15/25 "tds_ppm"

    return jsonify(ok=True, stored=True)

@app.get("/data")
def data_view():
    # return last N rows
    try:
        n = int(request.args.get("n","10"))
    except ValueError:
        n = 10

    rows = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline="") as f:
            rows = list(csv.DictReader(f))[-n:]
    return jsonify(ok=True, count=len(rows), rows=rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
