from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Function to download the video
def download_video(url):
    # Generate a random filename to avoid collisions
    output_file = f"{uuid.uuid4()}.mp4"

    # yt-dlp options
    ydl_opts = {
        'outtmpl': output_file,  # Save the file with the generated name
        'format': 'bestvideo+bestaudio/best',  # Download the best quality
        'merge_output_format': 'mp4',  # Ensure mp4 format
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_file

# Route to handle video download
@app.route('/download', methods=['POST'])
def download_reddit_video():
    try:
        data = request.json
        url = data.get('url')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Download the video
        video_file = download_video(url)

        # Send the file to the client
        return send_file(video_file, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up: Remove the downloaded file after sending it
        if os.path.exists(video_file):
            os.remove(video_file)

# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True)
