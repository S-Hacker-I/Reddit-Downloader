from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import logging

app = Flask(__name__)

# Directory to temporarily store video files
VIDEO_DIR = 'videos'
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route('/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    logging.info(f"Attempting to download video from URL: {url}")

    # Define download options for Reddit
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download the best video + best audio
        'outtmpl': os.path.join(VIDEO_DIR, 'reddit_video.%(ext)s'),  # Save with the correct extension
        'noplaylist': True,
        'quiet': True,
        'merge_output_format': 'mp4',  # Ensure the output is in mp4 format
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # Convert to mp4 if needed
        }],
        'age_limit': 18,  # Optional: Set age limit if needed
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)  # Prepare the filename
            logging.info(f"Downloaded video saved to: {filename}")
        except Exception as e:
            logging.error(f"Error downloading video: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # Ensure the file exists before sending
    filename = os.path.join(VIDEO_DIR, 'reddit_video.mp4')
    if not os.path.isfile(filename):
        return jsonify({'error': 'Failed to download video'}), 500

    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
