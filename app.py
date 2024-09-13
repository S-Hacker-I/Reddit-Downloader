import os
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

# Ensure the downloads folder exists
if not os.path.exists('downloads'):
    os.makedirs('downloads')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Replace 'www.reddit.com' with 'old.reddit.com' for better compatibility
    if 'reddit.com' in url:
        url = url.replace('www.reddit.com', 'old.reddit.com')

    try:
        # yt-dlp options for downloading best video+audio
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = f"downloads/{info['title']}.{info['ext']}"

        # Send the downloaded file to the user
        return send_file(file_name, as_attachment=True)

    except yt_dlp.utils.DownloadError as e:
        return jsonify({'error': 'Failed to download video: ' + str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred: ' + str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
