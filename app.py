from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import subprocess
import os

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

@app.route('/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
     
    # Download video and audio
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'temp_video.mp4',
        'noplaylist': True,
    }
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    try:
        ydl.download([url])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Combine video and audio
    try:
        subprocess.run([
            'ffmpeg', '-i', 'temp_video.mp4', '-c', 'copy', 'output_video.mp4'
        ], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'FFmpeg processing error: ' + str(e)}), 500
    finally:
        os.remove('temp_video.mp4')

    return send_file('output_video.mp4', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
