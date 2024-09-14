from flask import Flask, request, send_file, jsonify
import yt_dlp
import subprocess
import os
import traceback

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'temp_video.mp4',
        'noplaylist': True,
    }
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    try:
        ydl.download([url])
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({'error': 'Failed to download video', 'details': str(e), 'traceback': traceback_str}), 500

    try:
        subprocess.run([
            'ffmpeg', '-i', 'temp_video.mp4', '-c', 'copy', 'output_video.mp4'
        ], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'FFmpeg processing error', 'details': str(e)}), 500
    finally:
        os.remove('temp_video.mp4')

    return send_file('output_video.mp4', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')  # Ensure it listens on all IPs for deployment
