from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Function to download the video from Reddit using yt-dlp
def download_video(url):
    unique_filename = f"{uuid.uuid4()}.mp4"  # Generate a unique filename for the video
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download best video and audio
        'merge_output_format': 'mp4',  # Ensure the output is in mp4 format
        'outtmpl': unique_filename,  # Use unique filename to avoid conflicts
    }

    try:
        # Download video using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return unique_filename
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

# Route to download Reddit video
@app.route('/download', methods=['POST'])
def download_reddit_video():
    try:
        # Get the URL from the request JSON data
        data = request.json
        url = data.get('url')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        print(f"Received URL: {url}")

        # Download the video
        video_file = download_video(url)

        if video_file and os.path.exists(video_file):
            # Send the downloaded video file to the user
            return send_file(video_file, as_attachment=True)
        else:
            return jsonify({'error': 'Failed to download video'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup: remove the downloaded file from the server
        if 'video_file' in locals() and video_file and os.path.exists(video_file):
            os.remove(video_file)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
