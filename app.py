from flask import Flask, request, Response, send_from_directory
import yt_dlp
import os
import logging

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory to store downloads temporarily
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_media(url, format_type):
    ydl_opts = {}
    if format_type == "mp4":
        ydl_opts = {
            'format': 'bestvideo+bestaudio',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        }
    elif format_type == "mp3":
        ydl_opts = {
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        file_name = ydl.prepare_filename(info)
        ydl.download([url])
        return file_name

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'mp4')  # Default to mp4 if not provided

    try:
        file_path = download_media(url, format_type)
        
        # Stream the file
        def generate():
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    yield chunk
        
        response = Response(generate(), content_type='application/octet-stream')
        response.headers.set('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
        return response
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Failed to download'}), 500

if __name__ == '__main__':
    app.run(debug=True)
