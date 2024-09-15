from flask import Flask, request, send_file, jsonify
import yt_dlp
import os

app = Flask(__name__)

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
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return send_file(os.path.join(VIDEO_DIR, 'video.mp4'), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
