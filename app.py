from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import subprocess
import traceback
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.json.get('url')
    if not video_url:
        return jsonify({'error': 'URL is required'}), 400

    # Temporary file paths
    temp_video_filename = 'temp_video.mp4'
    temp_audio_filename = 'temp_audio.mp4'
    output_filename = 'output_video.mp4'

    # Set up yt-dlp options for video
    ydl_opts_video = {
        'format': 'bestvideo',
        'outtmpl': temp_video_filename,
    }

    # Set up yt-dlp options for audio
    ydl_opts_audio = {
        'format': 'bestaudio',
        'outtmpl': temp_audio_filename,
    }

    try:
        # Download the best video
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            ydl.download([video_url])

        # Download the best audio
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([video_url])

        # Merge video and audio using ffmpeg
        result = subprocess.run([
            'ffmpeg',
            '-i', temp_video_filename,
            '-i', temp_audio_filename,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_filename
        ], capture_output=True, text=True)

        # Log ffmpeg output for debugging
        print(result.stdout)
        print(result.stderr)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg error: {result.stderr}")

        # Serve the merged file for download
        response = send_file(output_filename, as_attachment=True, download_name='video.mp4')
        
        # Delay the cleanup to ensure the file is not in use
        time.sleep(2)  # Adjust this delay if needed

        # Clean up temporary files
        for file in [temp_video_filename, temp_audio_filename, output_filename]:
            if os.path.exists(file):
                os.remove(file)

        return response
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temporary files
        for file in [temp_video_filename, temp_audio_filename, output_filename]:
            if os.path.exists(file):
                os.remove(file)

if __name__ == '__main__':
    app.run(debug=True)
