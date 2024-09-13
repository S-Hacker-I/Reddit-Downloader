from flask import Flask, request, jsonify, send_file, send_from_directory
import yt_dlp
import os
from threading import Thread, Lock
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables to track points and downloads
global_points = 10000  # Example starting points
global_downloads = 0
lifetime_points_used = 0
download_lock = Lock()

# Directory to store downloads temporarily
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Function to download the video or audio
def download_media(url, format_type, callback):
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
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            file_name = ydl.prepare_filename(info)
            ydl.download([url])
            # Ensure the correct extension for MP3
            if format_type == "mp3":
                file_name = file_name.rsplit('.', 1)[0] + '.mp3'
            callback(file_name)
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"DownloadError: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

# Serve the main HTML page
@app.route('/')
def index():
    return send_from_directory('', 'index.html')

@app.route('/download', methods=['POST'])
def download():
    global global_points, global_downloads, lifetime_points_used
    
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'mp4')  # Default to mp4 if not provided

    # Ensure user has enough points
    if global_points < 5:
        return jsonify({'error': 'Not enough points'}), 403

    # Using a list to store file_path because nonlocal cannot be used
    file_path = [None]

    def handle_download(file_name):
        nonlocal file_path
        file_path[0] = file_name
        
        # Deduct points and update download count
        with download_lock:
            global_points -= 5
            global_downloads += 1
            lifetime_points_used += 5

    try:
        # Download media in a separate thread to prevent blocking
        download_thread = Thread(target=download_media, args=(url, format_type, handle_download))
        download_thread.start()
        download_thread.join()  # Wait for the thread to finish
        
        # Return the file as a response
        if file_path[0]:
            return send_file(file_path[0], as_attachment=True)
        else:
            return jsonify({'error': 'Failed to download'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/points', methods=['GET'])
def points():
    return jsonify({
        'balance': global_points,
        'downloads': global_downloads,
        'lifetime_points_used': lifetime_points_used
    })

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
