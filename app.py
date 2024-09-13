from flask import Flask, request, jsonify, send_from_directory, Response
import yt_dlp
import os
from threading import Thread, Timer
import datetime
import logging
from werkzeug.utils import safe_join, secure_filename

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables to track points and downloads
global_points = 10000  # Example starting points
global_downloads = 0
lifetime_points_used = 0

# Allowed referer domains
ALLOWED_REFERERS = [
    'https://trendfydigital.com',
    'http://127.0.0.1:5500'
]

# Directory to store downloads temporarily
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def allowed_referer(referer):
    return any(referer.startswith(allowed) for allowed in ALLOWED_REFERERS)

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
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            file_name = ydl.prepare_filename(info)
            
            # Download and process the file (conversion if needed)
            ydl.download([url])
            
            # Ensure the correct extension for MP3
            if format_type == "mp3":
                file_name = file_name.rsplit('.', 1)[0] + '.mp3'
            
            return file_name
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"DownloadError: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

# Function to stream files in chunks
def generate_file_stream(file_path):
    with open(file_path, 'rb') as file:
        chunk = file.read(4096)
        while chunk:
            yield chunk
            chunk = file.read(4096)

# Serve static files from any directory
@app.route('/<path:filename>')
def serve_file(filename):
    try:
        # Safely join the path to avoid directory traversal
        safe_path = safe_join(DOWNLOAD_FOLDER, filename)
        # Ensure the file exists
        if os.path.isfile(safe_path):
            return send_from_directory(DOWNLOAD_FOLDER, filename)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error serving file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    global global_points, global_downloads, lifetime_points_used
    
    # Check Referer header
    referer = request.headers.get('Referer')
    if referer is None or not allowed_referer(referer):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'mp4')  # Default to mp4 if not provided

    # Ensure user has enough points
    if global_points < 5:
        return jsonify({'error': 'Not enough points'}), 403

    try:
        # Download media in a separate thread to prevent blocking
        def handle_download():
            nonlocal file_path
            file_path = download_media(url, format_type)
        
        file_path = None
        download_thread = Thread(target=handle_download)
        download_thread.start()
        download_thread.join()  # Wait for the thread to finish
        
        # Deduct points and update download count
        global_points -= 5
        global_downloads += 1
        lifetime_points_used += 5

        # Return the file as a stream
        return Response(generate_file_stream(file_path), 
                        headers={"Content-Disposition": f"attachment; filename={os.path.basename(file_path)}"},
                        content_type="application/octet-stream")
    
    except Exception as e:
        logger.error(f"Error in download: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/points', methods=['GET'])
def points():
    return jsonify({
        'balance': global_points,
        'downloads': global_downloads,
        'lifetime_points_used': lifetime_points_used
    })

def reset_balance():
    global global_points
    global_points = 10000
    logger.info(f"Balance reset to {global_points} at {datetime.datetime.now()}")
    
    # Schedule the next reset in 24 hours
    Timer(86400, reset_balance).start()

if __name__ == '__main__':
    # Start the balance reset scheduler
    Timer(0, reset_balance).start()  # Start immediately
    # Set custom port and enable threading
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
