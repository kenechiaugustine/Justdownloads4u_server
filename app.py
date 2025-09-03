import os
import uuid
import logging
# ✅ The import has been corrected here
from flask import Flask, request, jsonify, send_from_directory, after_this_request
from flask_cors import CORS
from yt_dlp import YoutubeDL

# --- 1. Basic Flask App Setup ---
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for your React app

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

# Define the temporary directory for downloads
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


# --- 2. API Endpoints ---

@app.route('/info', methods=['POST'])
def get_info():
    """
    Endpoint to get video metadata.
    Accepts a JSON body with a 'url' key.
    """
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "No URL provided."}), 400

    logging.info(f"[INFO] Received info request for URL: {url}")
    try:
        # Use yt-dlp to extract information without downloading
        with YoutubeDL() as ydl:
            metadata = ydl.extract_info(url, download=False)
        
        # Structure the response similarly to the Node.js version
        formats = metadata.get('formats', [])
        response_data = {
            "title": metadata.get('title'),
            "thumbnail": metadata.get('thumbnail'),
            "formats": [
                {
                    "format_id": f.get('format_id'),
                    "ext": f.get('ext'),
                    "resolution": f.get('resolution'),
                    "note": f.get('format_note'),
                    "filesize": f.get('filesize'),
                }
                for f in formats if f.get('resolution') or f.get('format_note', '').startswith('audio only')
            ]
        }
        logging.info(f"[INFO] Successfully sent info for: {metadata.get('title')}")
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"[ERROR] Failed to fetch info for URL: {url} - {str(e)}")
        return jsonify({
            "error": "Failed to fetch video information. The URL might be private or invalid.",
            "details": str(e)
        }), 500


@app.route('/download', methods=['GET'])
def download_video():
    """
    Endpoint to download a video and stream it to the client.
    Accepts 'url' and 'quality' as query parameters.
    """
    url = request.args.get('url')
    quality = request.args.get('quality')

    if not url:
        return jsonify({"error": "No URL provided."}), 400

    temp_filename = f"{uuid.uuid4()}.mp4"
    temp_filepath = os.path.join(TEMP_DIR, temp_filename)

    logging.info(f"[DOWNLOAD] Starting download for URL: {url} with quality: {quality}")

    try:
        # Build a robust format selector string
        if quality == 'audio':
            format_string = 'bestaudio/best'
        elif quality:
            height = quality.replace('p', '')
            format_string = f'bestvideo[height<={height}]+bestaudio/bestvideo+bestaudio/best'
        else:
            format_string = 'bestvideo+bestaudio/best'
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': format_string,
            'outtmpl': temp_filepath,
            'merge_output_format': 'mp4',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            # For 'audio' quality, we can post-process to MP3
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if quality == 'audio' else [],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True) # Download and get info
            # If audio, the final file has a different extension
            if quality == 'audio':
                temp_filepath = temp_filepath.replace('.mp4', '.mp3')


        logging.info(f"[DOWNLOAD] File saved to temp path: {temp_filepath}")
        
        title = info.get('title', 'media').replace('/', '_').replace('\\', '_')
        
        # Determine final filename based on content type
        final_filename = f"{title}.mp3" if quality == 'audio' else f"{title}.mp4"

        # This decorator ensures the cleanup function runs after the request is complete
        @after_this_request
        def cleanup(response):
            try:
                os.remove(temp_filepath)
                logging.info(f"[CLEANUP] Deleted temp file: {temp_filepath}")
            except Exception as error:
                logging.error(f"[CLEANUP-ERROR] Failed to delete temp file: {error}")
            return response

        return send_from_directory(
            directory=TEMP_DIR,
            path=os.path.basename(temp_filepath), # Use basename to be safe
            as_attachment=True,
            download_name=final_filename
        )

    except Exception as e:
        logging.error(f"[DOWNLOAD-ERROR] Execution failed for {url}: {str(e)}")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        # Also check for the .mp3 version if audio conversion was attempted
        mp3_path = temp_filepath.replace('.mp4', '.mp3')
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        return jsonify({
            "error": "Failed to process the video. The URL may be private, invalid, or the site may have updated.",
            "details": str(e)
        }), 500

# --- 3. Run the App ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)