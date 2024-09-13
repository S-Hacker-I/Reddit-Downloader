from flask import Flask, request, jsonify, send_file, Response
import yt_dlp
import os
import threading
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Global variables to track points and downloads, protected by locks
global_points = 10000  # Starting points
global_downloads = 0
lifetime_points_used = 0

# Locks to prevent race conditions
points_lock = threading.Lock()
downloads_lock = threading.Lock()

# Directory to store downloads temporarily
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Thread pool for handling concurrent downloads
executor = ThreadPoolExecutor(max_workers=100)  # Adjust number of workers for high load

# Function to download the video or audio
def download_media(url, format_type):
    ydl_opts = {}
    if format_type == "mp4":
        ydl_opts = {
            'format': 'bestvideo+bestaudio',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        }
    elif format_type == "mp3":
        ydl_opts = {
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        file_name = ydl.prepare_filename(info)

        # Download and process the file (conversion if needed)
        ydl.download([url])

        # Ensure the correct extension for MP3
        if format_type == "mp3":
            file_name = file_name.rsplit('.', 1)[0] + '.mp3'

        return file_name

# Function to stream files in chunks
def generate_file_stream(file_path):
    with open(file_path, 'rb') as file:
        chunk = file.read(4096)
        while chunk:
            yield chunk
            chunk = file.read(4096)

# Serve the main HTML page
@app.route('/')
def index():
    return send_from_directory('', 'index.html')

# Handle download requests concurrently
@app.route('/download', methods=['POST'])
def download():
    global global_points, global_downloads, lifetime_points_used

    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'mp4')  # Default to mp4 if not provided

    # Ensure user has enough points
    with points_lock:
        if global_points < 5:
            return jsonify({'error': 'Not enough points'}), 403

    try:
        # Concurrent task for downloading media
        def handle_download():
            return download_media(url, format_type)

        # Run the download in a separate thread
        future = executor.submit(handle_download)
        file_path = future.result()

        # Update points and downloads safely
        with points_lock:
            global_points -= 5
            lifetime_points_used += 5

        with downloads_lock:
            global_downloads += 1

        # Return the file as a stream
        return Response(generate_file_stream(file_path),
                        headers={"Content-Disposition": f"attachment; filename={os.path.basename(file_path)}"},
                        content_type="application/octet-stream")

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get the points and download stats
@app.route('/points', methods=['GET'])
def points():
    return jsonify({
        'balance': global_points,
        'downloads': global_downloads,
        'lifetime_points_used': lifetime_points_used
    })

if __name__ == '__main__':
    # For production-level concurrent requests, use gunicorn to run the app
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
