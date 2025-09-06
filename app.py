import os
import uuid
import logging
from flask import Flask, request, jsonify, send_from_directory, after_this_request
from flask_cors import CORS
from yt_dlp import YoutubeDL

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@app.route('/info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided."}), 400
    logging.info(f"[INFO] Received info request for URL: {url}")
    try:
        with YoutubeDL() as ydl:
            metadata = ydl.extract_info(url, download=False)
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
    url = request.args.get('url')
    quality = request.args.get('quality')
    if not url:
        return jsonify({"error": "No URL provided."}), 400
    temp_filename = f"{uuid.uuid4()}.mp4"
    temp_filepath = os.path.join(TEMP_DIR, temp_filename)
    logging.info(f"[DOWNLOAD] Starting download for URL: {url} with quality: {quality}")
    try:
        if quality == 'audio':
            format_string = 'bestaudio/best'
        elif quality:
            height = quality.replace('p', '')
            format_string = f'bestvideo[height<={height}]+bestaudio/bestvideo+bestaudio/best'
        else:
            format_string = 'bestvideo+bestaudio/best'
        ydl_opts = {
            'format': format_string,
            'outtmpl': temp_filepath,
            'merge_output_format': 'mp4',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if quality == 'audio' else [],
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if quality == 'audio':
                temp_filepath = temp_filepath.replace('.mp4', '.mp3')
        logging.info(f"[DOWNLOAD] File saved to temp path: {temp_filepath}")
        title = info.get('title', 'media').replace('/', '_').replace('\\', '_')
        final_filename = f"{title}.mp3" if quality == 'audio' else f"{title}.mp4"
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
            path=os.path.basename(temp_filepath),
            as_attachment=True,
            download_name=final_filename
        )
    except Exception as e:
        logging.error(f"[DOWNLOAD-ERROR] Execution failed for {url}: {str(e)}")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        mp3_path = temp_filepath.replace('.mp4', '.mp3')
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        return jsonify({
            "error": "Failed to process the video. The URL may be private, invalid, or the site may have updated.",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
