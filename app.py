from flask import Flask, render_template, jsonify, send_file
import json
from datetime import datetime
import requests
import os

app = Flask(__name__)

# Load data from JSON
def load_data():
    with open('analytics.json', 'r') as file:
        return json.load(file)

# Save data to JSON
def save_data(data):
    with open('analytics.json', 'w') as file:
        json.dump(data, file)

# Function to download TikTok video
def download_video(video_url):
    response = requests.get(video_url, stream=True)
    
    if response.status_code == 200:
        video_path = 'video.mp4'
        with open(video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        return video_path
    else:
        return None

# Route to serve index.html
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint for download logic
@app.route('/download', methods=['GET'])
def download():
    data = load_data()
    data['last_request'] = str(datetime.now())
    data['requests'] += 1
    
    # Download the specific TikTok video
    video_url = 'https://vm.tiktok.com/ZMhBWrJu6/'  # Your TikTok video link
    video_file_path = download_video(video_url)

    if video_file_path:
        save_data(data)
        return send_file(video_file_path, as_attachment=True)
    else:
        return jsonify({"message": "Download failed", "status": 500}), 500

# Endpoint to keep the server alive
@app.route('/keep-alive', methods=['GET'])
def keep_alive():
    data = load_data()
    data['last_request'] = str(datetime.now())
    data['requests'] += 1
    save_data(data)
    return jsonify({"message": "Server is alive", "status": 200})

# Endpoint to get server analytics
@app.route('/analytics', methods=['GET'])
def get_analytics():
    data = load_data()
    return jsonify(data)

if __name__ == '__main__':
    # Initialize JSON file with empty data if not present
    if not os.path.exists('analytics.json'):
        initial_data = {
            "requests": 0,
            "last_request": None,
            "uptime": "Running"
        }
        with open('analytics.json', 'w') as file:
            json.dump(initial_data, file)

    app.run(debug=True, host='0.0.0.0', port=65000)
