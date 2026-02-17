import os
import uuid
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from yt_dlp import YoutubeDL
from models import VideoInfoRequest, VideoInfoResponse, VideoFormat

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def cleanup_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"[CLEANUP] Deleted temp file: {path}")
    except Exception as e:
        logger.error(f"[CLEANUP-ERROR] Failed to delete temp file: {e}")

def get_ydl_opts(extra_opts=None):
    """
    Get yt-dlp options with cookie authentication support
    """
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web', 'ios']
            }
        },
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }
    
    # COOKIE AUTHENTICATION - Priority order:
    # 1. Cookie file from environment variable (for production/headless servers)
    # 2. Browser cookies (for development/servers with browser access)
    
    cookies_path = os.getenv('YOUTUBE_COOKIES_PATH')
    cookie_browser = os.getenv('COOKIE_BROWSER', 'chrome')  # Default to chrome
    
    if cookies_path and os.path.exists(cookies_path):
        # Method 1: Use cookie file
        opts['cookiefile'] = cookies_path
        logger.info(f"[CONFIG] Using cookie file: {cookies_path}")
    elif cookies_path:
        logger.warning(f"[CONFIG] Cookie file specified but not found: {cookies_path}")
        # Fall back to browser cookies
        try:
            opts['cookiesfrombrowser'] = (cookie_browser,)
            logger.info(f"[CONFIG] Cookie file not found, falling back to browser cookies: {cookie_browser}")
        except Exception as e:
            logger.warning(f"[CONFIG] Could not use browser cookies: {e}")
    else:
        # Method 2: Use browser cookies (recommended for development)
        try:
            opts['cookiesfrombrowser'] = (cookie_browser,)
            logger.info(f"[CONFIG] Using browser cookies from: {cookie_browser}")
        except Exception as e:
            logger.warning(f"[CONFIG] Could not use browser cookies: {e}")
            logger.warning("[CONFIG] No cookie authentication configured - some videos may fail")
    
    if extra_opts:
        opts.update(extra_opts)
    return opts

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cookie_method = "none"
    cookies_path = os.getenv('YOUTUBE_COOKIES_PATH')
    cookie_browser = os.getenv('COOKIE_BROWSER', 'chrome')
    
    if cookies_path and os.path.exists(cookies_path):
        cookie_method = f"file: {cookies_path}"
    elif cookie_browser:
        cookie_method = f"browser: {cookie_browser}"
    
    return {
        "status": "healthy",
        "service": "YouTube Downloader",
        "cookie_auth": cookie_method,
        "temp_dir": TEMP_DIR
    }

@app.post("/info", response_model=VideoInfoResponse)
async def get_info(request: VideoInfoRequest):
    url = request.url
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided.")
    
    logger.info(f"[INFO] Received info request for URL: {url}")
    try:
        with YoutubeDL(get_ydl_opts()) as ydl:
            metadata = ydl.extract_info(url, download=False)
        
        formats = metadata.get('formats', [])
        video_formats = [
            VideoFormat(
                format_id=f.get('format_id'),
                ext=f.get('ext'),
                resolution=f.get('resolution'),
                note=f.get('format_note'),
                filesize=f.get('filesize'),
            )
            for f in formats if f.get('resolution') or (f.get('format_note') and f.get('format_note', '').startswith('audio only'))
        ]
        
        logger.info(f"[INFO] Successfully fetched info for: {metadata.get('title')}")
        return VideoInfoResponse(
            title=metadata.get('title'),
            thumbnail=metadata.get('thumbnail'),
            formats=video_formats
        )
    except Exception as e:
        logger.error(f"[ERROR] Failed to fetch info for URL: {url} - {str(e)}")
        
        # Provide helpful error message for cookie-related issues
        error_msg = str(e)
        if "Sign in to confirm you're not a bot" in error_msg or "bot" in error_msg.lower():
            error_msg = (
                "YouTube requires authentication. Please configure cookies:\n"
                "1. Set COOKIE_BROWSER=chrome (or firefox, edge, etc.) to use browser cookies, OR\n"
                "2. Set YOUTUBE_COOKIES_PATH=/path/to/cookies.txt to use a cookie file.\n"
                f"Original error: {error_msg}"
            )
        
        raise HTTPException(status_code=500, detail=f"Failed to fetch video information: {error_msg}")

@app.get("/download")
async def download_video(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="Video URL"),
    quality: str = Query(None, description="Video quality (e.g., 1080p, audio)")
):
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided.")
    
    temp_filename = f"{uuid.uuid4()}.mp4"
    temp_filepath = os.path.join(TEMP_DIR, temp_filename)
    logger.info(f"[DOWNLOAD] Starting download for URL: {url} with quality: {quality}")
    
    try:
        if quality == 'audio':
            format_string = 'bestaudio/best'
        elif quality:
            height = quality.replace('p', '')
            format_string = f'bestvideo[height<={height}]+bestaudio/bestvideo+bestaudio/best'
        else:
            format_string = 'bestvideo+bestaudio/best'
            
        extra_opts = {
            'format': format_string,
            'outtmpl': temp_filepath,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if quality == 'audio' else [],
        }
        
        ydl_opts = get_ydl_opts(extra_opts)
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if quality == 'audio':
                temp_filepath = temp_filepath.replace('.mp4', '.mp3')
                
        logger.info(f"[DOWNLOAD] File saved to temp path: {temp_filepath}")
        
        title = info.get('title', 'media').replace('/', '_').replace('\\', '_')
        final_filename = f"{title}.mp3" if quality == 'audio' else f"{title}.mp4"
        
        background_tasks.add_task(cleanup_file, temp_filepath)
        
        return FileResponse(
            path=temp_filepath,
            filename=final_filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"[DOWNLOAD-ERROR] Execution failed for {url}: {str(e)}")
        
        # Cleanup on error
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        mp3_path = temp_filepath.replace('.mp4', '.mp3')
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        
        # Provide helpful error message for cookie-related issues
        error_msg = str(e)
        if "Sign in to confirm you're not a bot" in error_msg or "bot" in error_msg.lower():
            error_msg = (
                "YouTube requires authentication. Please configure cookies:\n"
                "1. Set COOKIE_BROWSER=chrome (or firefox, edge, etc.) to use browser cookies, OR\n"
                "2. Set YOUTUBE_COOKIES_PATH=/path/to/cookies.txt to use a cookie file.\n"
                f"Original error: {error_msg}"
            )
            
        raise HTTPException(status_code=500, detail=f"Failed to process the video: {error_msg}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)