from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import yt_dlp
import os
import logging
import threading
import uuid
import time
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500"])
app.wsgi_app = ProxyFix(app.wsgi_app)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

downloads = {}

def schedule_file_deletion(filepath, delay=900):
    def delete_file():
        time.sleep(delay)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    threading.Thread(target=delete_file, daemon=True).start()

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    if not url.startswith("https://www.reddit.com/"):
        return jsonify({'error': 'Invalid URL'}), 400

    try:
        filename = download_video(url, DOWNLOAD_FOLDER)
        if filename:
            token = str(uuid.uuid4())
            downloads[token] = filename
            schedule_file_deletion(os.path.join(DOWNLOAD_FOLDER, filename))
            return jsonify({'token': token, 'download_link': f'/downloads/{token}'})
        else:
            return jsonify({'error': 'Failed to download video'}), 500
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/downloads/<token>', methods=['GET'])
def download_file(token):
    filename = downloads.get(token)
    if filename:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
    abort(404)

if __name__ == '__main__':
    app.run(debug=True)

