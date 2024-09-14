from flask import Flask, request, send_file, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download_video():
    try:
        reddit_url = request.json.get('url')

        if not reddit_url:
            return jsonify({'error': 'No URL provided'}), 400

        # Generate unique filename for the downloaded video
        video_id = yt_dlp.utils.Random().getrandbits(64)  # Random video ID
        download_path = f"downloads/{video_id}.mp4"

        # yt-dlp options
        ydl_opts = {
            'outtmpl': download_path,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(reddit_url, download=True)

        # Respond with video ID to allow client to download later
        return jsonify({"video_id": video_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/downloaded/<video_id>', methods=['GET'])
def serve_video(video_id):
    try:
        file_path = f"downloads/{video_id}.mp4"

        if os.path.exists(file_path):
            # Serve the video file for download
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
