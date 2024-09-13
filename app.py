from flask import Flask, request, jsonify, send_from_directory, send_file, abort
import yt_dlp
import os
import logging
import threading
import uuid
import time
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
CORS(app)  # Enable CORS for all routes

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Directory to store downloaded files
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Dictionary to store mapping of tokens to filenames
downloads = {}

def schedule_file_deletion(filepath, delay=900):
    """Schedule file deletion after a delay (default 15 minutes)."""
    def delete_file():
        time.sleep(delay)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                logging.info(f"File {filepath} deleted after {delay} seconds")
            except Exception as e:
                logging.error(f"Error deleting file {filepath}: {e}")
        else:
            logging.info(f"File {filepath} not found for deletion")
    
    thread = threading.Thread(target=delete_file, daemon=True)
    thread.start()

def download_video(url, download_folder):
    """Download and process the video."""
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'noplaylist': True,
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            base, ext = os.path.splitext(filename)
            if ext != '.mp4':
                mp4_filename = base + '.mp4'
                mp4_filepath = os.path.join(download_folder, mp4_filename)
                if os.path.exists(filename):
                    os.rename(filename, mp4_filepath)
                    filename = mp4_filename
                else:
                    logging.error(f'File {filename} not found for renaming')
                    return None
            else:
                filename = os.path.basename(filename)
            
            return filename
        except yt_dlp.utils.ExtractorError as e:
            logging.error('Extractor error: %s', e)
            return None
        except Exception as e:
            logging.error('Error: %s', e)
            return None

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    def task():
        return download_video(url, DOWNLOAD_FOLDER)

    # Generate a unique token for this download request
    token = str(uuid.uuid4())
    
    # Run the download in a separate thread
    thread = threading.Thread(target=lambda: downloads.update({token: task()}))
    thread.start()
    thread.join()

    filename = downloads.get(token)
    if filename:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            # Schedule the file deletion after 15 minutes
            schedule_file_deletion(file_path)
            return jsonify({'token': token, 'download_link': f'/downloads/{token}'})
        else:
            return jsonify({'error': 'Failed to locate the downloaded file'}), 500
    else:
        return jsonify({'error': 'Failed to download video'}), 500

@app.route('/downloads/<token>', methods=['GET'])
def download_file(token):
    filename = downloads.get(token)
    if filename:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            abort(404)
    else:
        abort(404)

if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 5000))  # Use PORT from environment or default to 5000
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
