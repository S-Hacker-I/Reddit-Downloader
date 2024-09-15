from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Directory to temporarily store video files
VIDEO_DIR = 'videos'
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

@app.route('/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Define download options
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(VIDEO_DIR, 'video.mp4'),
        'noplaylist': True,
        'quiet': True,
        'age_limit': 18,  # Handle age-restricted content
        'merge_output_format': 'mp4',  # Ensure output is mp4
        'noprogress': True,  # Disable progress output
        'writeinfojson': True,  # Write video info as JSON (for debugging)
    }

    logging.debug(f"Downloading video from URL: {url}")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return jsonify({'error': str(e)}), 500

    video_path = os.path.join(VIDEO_DIR, 'video.mp4')
    if not os.path.exists(video_path):
        logging.error('Video file not found')
        return jsonify({'error': 'Video file not found'}), 404

    return send_file(video_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
