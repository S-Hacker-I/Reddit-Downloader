from flask import Flask, request, Response, jsonify
import yt_dlp
import os

app = Flask(__name__)

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

# Stream the file as it is being downloaded
def stream_file(file_path):
    def generate():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk
    return Response(generate(), headers={
        'Content-Disposition': f'attachment; filename="{os.path.basename(file_path)}"',
        'Content-Type': 'application/octet-stream',
    })

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'mp4')

    try:
        file_path = download_media(url, format_type)
        return stream_file(file_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
