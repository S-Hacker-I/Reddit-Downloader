from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
from uuid import uuid4

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"

# Ensure the downloads folder exists
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        reddit_url = data['url']

        # Create a unique file name for the downloaded video
        video_id = str(uuid4())
        download_path = os.path.join(DOWNLOAD_FOLDER, f"{video_id}.mp4")

        # yt-dlp options
        ydl_opts = {
            'outtmpl': download_path,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([reddit_url])

        # Send the video file for download
        return jsonify({"video_id": video_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/downloaded/<video_id>', methods=['GET'])
def serve_video(video_id):
    try:
        file_path = os.path.join(DOWNLOAD_FOLDER, f"{video_id}.mp4")
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
