from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Function to download the video using yt-dlp
def download_video(url):
    unique_filename = f"{uuid.uuid4()}.mp4"  # Generate unique filename for the video

    # yt-dlp options to get the best video and audio and merge them into an MP4
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download best video+audio
        'merge_output_format': 'mp4',          # Ensure output is in mp4 format
        'outtmpl': unique_filename,            # Use unique filename
    }

    try:
        # Download video using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return unique_filename
    except Exception as e:
        print(f"Error while downloading video: {e}")
        return None

# Route to download Reddit video
@app.route('/download', methods=['POST'])
def download_reddit_video():
    try:
        # Get the Reddit video URL from the request data
        data = request.json
        url = data.get('url')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        print(f"Received URL: {url}")

        # Download the video using the download_video function
        video_file = download_video(url)

        if video_file and os.path.exists(video_file):
            # Send the video file to the user
            return send_file(video_file, as_attachment=True)
        else:
            return jsonify({'error': 'Failed to download video'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up: remove the downloaded file from the server after sending
        if 'video_file' in locals() and video_file and os.path.exists(video_file):
            os.remove(video_file)

if __name__ == '__main__':
    app.run(debug=True, port=8080)  # Change port to 8080 or any other
