from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Function to download the video from Reddit URL
def download_video(url):
    output_file = f"{uuid.uuid4()}.mp4"  # Random filename to avoid conflicts

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Get best video and audio
        'merge_output_format': 'mp4',  # Ensure the output is in mp4 format
        'outtmpl': output_file,  # Name of the output file
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_file  # Return the path of the downloaded file
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None  # Return None if there's an error

# Route to handle video download requests
@app.route('/download', methods=['POST'])
def download_reddit_video():
    try:
        # Get the URL from the POST request
        data = request.json
        url = data.get('url')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Download the video
        video_file = download_video(url)

        if video_file and os.path.exists(video_file):
            # Send the file back to the client as a download
            return send_file(video_file, as_attachment=True)

        return jsonify({'error': 'Video download failed'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup the downloaded file if it exists
        if video_file and os.path.exists(video_file):
            os.remove(video_file)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
