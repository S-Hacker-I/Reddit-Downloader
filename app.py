from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables to track points and downloads
global_points = 10000  # Example starting points
global_downloads = 0
lifetime_points_used = 0

# Directory to store downloads temporarily
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

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
        ydl.download([url])
        return file_name

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

    try:
        # Download media
        file_path = download_media(url, format_type)
        
        # Deduct points and update download count
        global_points -= 5
        global_downloads += 1
        lifetime_points_used += 5
        
        return send_file(file_path, as_attachment=True)
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
    app.run(debug=True)
