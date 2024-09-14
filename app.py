from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import logging
from uuid import uuid4
import json

app = Flask(__name__)
CORS(app)  # Allow all origins, adjust as needed

# Set up logging
logging.basicConfig(level=logging.INFO)

DOWNLOAD_DIR = 'downloads'

# Ensure the download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.json
        if not data or 'url' not in data:
            logging.error("No URL provided in request")
            return jsonify({'error': 'URL is required'}), 400

        url = data['url']
        unique_filename = f"{uuid4().hex}.mp4"
        file_path = os.path.join(DOWNLOAD_DIR, unique_filename)

        ydl_opts = {
            'format': 'best',
            'outtmpl': file_path,
            'quiet': True  # Set to False if you want more detailed output for debugging
        }

        # Attempt to download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                logging.info(f"Attempting to download video from URL: {url}")
                result = ydl.extract_info(url, download=True)
            except yt_dlp.utils.DownloadError as de:
                logging.error(f"DownloadError: {de}", exc_info=True)
                return jsonify({'error': f'Failed to download video: {de}'}), 500
            except yt_dlp.utils.ExtractorError as ee:
                logging.error(f"ExtractorError: {ee}", exc_info=True)
                return jsonify({'error': f'Failed to extract video info: {ee}'}), 500
            except yt_dlp.utils.PostProcessingError as ppe:
                logging.error(f"PostProcessingError: {ppe}", exc_info=True)
                return jsonify({'error': f'Failed during post-processing: {ppe}'}), 500
            except json.JSONDecodeError as jde:
                logging.error(f"JSONDecodeError: {jde}", exc_info=True)
                return jsonify({'error': 'Failed to parse JSON from the video source.'}), 500
            except Exception as e:
                logging.error(f"Unexpected error: {e}", exc_info=True)
                return jsonify({'error': f'Internal server error: {e}'}), 500

        # If the download is successful, return the file path
        logging.info(f"Download successful, file saved as: {unique_filename}")
        return jsonify({'status': 'success', 'file': unique_filename}), 200

    except Exception as e:
        logging.error(f"Unexpected error during processing: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {e}'}), 500

if __name__ == '__main__':
    # Adjust as needed for production
    app.run(debug=True, host='0.0.0.0', port=10000)
