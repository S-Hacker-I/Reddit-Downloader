from flask import Flask, request, send_file, jsonify, make_response
import yt_dlp
import os

app = Flask(__name__)

# Directory to temporarily store video files
VIDEO_DIR = 'videos'
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

# Function to allow CORS
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# Route to download videos
@app.route('/download', methods=['POST', 'OPTIONS'])
def download_video():
    if request.method == 'OPTIONS':
        # Handle preflight request for CORS
        response = make_response()
        return add_cors_headers(response)

    url = request.json.get('url')
    if not url:
        return add_cors_headers(jsonify({'error': 'No URL provided'})), 400

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
            return add_cors_headers(jsonify({'error': str(e)})), 500

    response = send_file(os.path.join(VIDEO_DIR, 'video.mp4'), as_attachment=True)
    return add_cors_headers(response)

# Adding CORS headers to all responses
app.after_request(add_cors_headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
