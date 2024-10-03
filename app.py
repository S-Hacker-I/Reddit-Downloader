from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Allow all origins for CORS

DATA_FILE = 'data.json'

# Load existing analytics data or create a new list
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        analytics_data = json.load(f)
else:
    analytics_data = []

@app.route('/analytics/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    analytics_data.append(data)  # Store incoming data

    # Save to JSON file
    with open(DATA_FILE, 'w') as f:
        json.dump(analytics_data, f)

    return jsonify({"status": "success", "data": data}), 201

@app.route('/analytics', methods=['GET'])
def get_analytics():
    return jsonify(analytics_data), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
