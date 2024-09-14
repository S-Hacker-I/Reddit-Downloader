from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import subprocess
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Function to ensure yt-dlp is updated
def update_yt_dlp():
    try:
        subprocess.run(['yt-dlp', '-U'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to update yt-dlp: {e}")

@app.route('/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Ensure yt-dlp is updated
    update_yt_dlp()
     
    # Download video and audio using yt-dlp
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'temp_video.mp4',
        'noplaylist': True,
    }
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    
    try:
        # Attempt to download the video
        ydl.download([url])
    except Exception as e:
        return jsonify({'error': f'Failed to download video: {str(e)}'}), 500

    # Combine video and audio (if necessary)
    try:
        # Process video file using ffmpeg
        subprocess.run([
            'ffmpeg', '-i', 'temp_video.mp4', '-c', 'copy', 'output_video.mp4'
        ], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'FFmpeg processing error: {str(e)}'}), 500
    finally:
        # Clean up the temp video
        if os.path.exists('temp_video.mp4'):
            os.remove('temp_video.mp4')

    return send_file('output_video.mp4', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
