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
CORS(app)  # Allow cross-origin requests

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

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/download', methods=['POST'])
def download():
    logging.info("Download request received")
    data = request.json
    url = data.get('url')
    logging.debug(f"URL received: {url}")

    if not url:
        return jsonify({'error': 'URL is required'}), 400

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

    def task():
        logging.info("Starting download task")
        filename = download_video(url, DOWNLOAD_FOLDER)
        if filename:
            logging.info(f"Download successful: {filename}")
        downloads[token] = filename

    token = str(uuid.uuid4())
    logging.info(f"Token generated: {token}")

    thread = threading.Thread(target=task)
    thread.start()
    thread.join()

    filename = downloads.get(token)
    if filename:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            schedule_file_deletion(file_path)
            logging.info(f"File available: {filename}")
            return jsonify({'token': token, 'download_link': f'/downloads/{token}'})
        else:
            logging.error(f"File not found: {filename}")
            return jsonify({'error': 'Failed to locate the downloaded file'}), 500
    else:
        logging.error("Failed to download video")
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
    app.run(debug=True, threaded=True)
