from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import threading
from pathlib import Path

app = Flask(__name__)

# Directory to save downloaded videos
DOWNLOAD_FOLDER = 'downloads'
Path(DOWNLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# Threading lock to prevent simultaneous access issues
lock = threading.Lock()

def download_video(url, output_file):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_file,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({'error': 'No URL provided'}), 400

    output_file = os.path.join(DOWNLOAD_FOLDER, 'video.mp4')

    def handle_download():
        with lock:
            try:
                download_video(video_url, output_file)
            except Exception as e:
                os.remove(output_file)
                return jsonify({'error': str(e)}), 500
        return send_file(output_file, as_attachment=True)
    
    # Start a new thread for the download task
    download_thread = threading.Thread(target=handle_download)
    download_thread.start()
    
    # Inform the user that the download is being processed
    return jsonify({'status': 'Download started. You will receive the file once the download is complete.'}), 202

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Server is running'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, threaded=True)
