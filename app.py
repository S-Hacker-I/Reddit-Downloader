from flask import Flask, request, jsonify, send_file, send_from_directory
import yt_dlp
import os
import threading

app = Flask(__name__)

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
            'noplaylist': True
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
            'noplaylist': True
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            file_name = ydl.prepare_filename(info)
            ydl.download([url])
            return file_name
    except yt_dlp.utils.DownloadError as e:
        app.logger.error(f"DownloadError: {e}")
        raise
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        raise

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
        # Handle download in a separate thread
        def handle_download():
            nonlocal file_path
            file_path = download_media(url, format_type)
        
        file_path = None
        download_thread = threading.Thread(target=handle_download)
        download_thread.start()
        download_thread.join()  # Wait for the thread to finish

        # Deduct points and update download count
        global_points -= 5
        global_downloads += 1
        lifetime_points_used += 5

        # Return the file as an attachment
        return send_file(file_path, as_attachment=True)
    except yt_dlp.utils.DownloadError:
        return jsonify({'error': 'Failed to download the video. Please check the URL or try again later.'}), 500
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
    # Specify the port and enable threading for concurrent requests
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
