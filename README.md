# Social Media Video Downloader - Backend

This is the backend server for the Social Media Video Downloader application. It is built with Python using the Flask micro-framework and leverages the powerful `yt-dlp` library to fetch metadata and stream video content from various social media platforms.

## Features

- **Metadata Fetching:** Provides an API endpoint to get video details like title, thumbnail, and available formats.
- **Direct Video Streaming:** Downloads and streams video content directly to the client, initiating the browser's download immediately.
- **Wide Compatibility:** Supports all platforms that `yt-dlp` supports (YouTube, TikTok, Instagram, X/Twitter, Facebook, etc.).
- **Quality Selection:** Allows the client to request a specific video quality or audio-only format.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1.  **Python 3.8+**

    - To check your version, run: `python3 --version`

2.  **pip** (Python's package installer)

    - Usually comes pre-installed with modern Python versions.

3.  **ffmpeg**
    - This is a **critical dependency** required by `yt-dlp` to merge video and audio streams. The server will fail for many high-quality videos without it.
    - **On macOS (using Homebrew):**
      ```bash
      brew install ffmpeg
      ```
    - **On Debian/Ubuntu:**
      ```bash
      sudo apt-get update && sudo apt-get install ffmpeg
      ```
    - **On Windows:**
      - Download a pre-built binary from the [official FFmpeg website](https://ffmpeg.org/download.html).
      - Unzip it and add the `bin` directory to your system's PATH environment variable.

## Setup and Installation

Follow these steps to set up and run the server locally.

1.  **Clone the Repository**
    If you haven't already, clone the project to your local machine.

    ```bash
    git clone <your-repository-url>
    cd <your-project-folder>/python-server
    ```

2.  **Create and Activate a Virtual Environment**
    It is highly recommended to use a virtual environment to manage project dependencies.

    ```bash
    # Create the virtual environment
    python3 -m venv venv

    # Activate it (on macOS and Linux)
    source venv/bin/activate

    # Activate it (on Windows)
    .\venv\Scripts\activate
    ```

    Your terminal prompt should now be prefixed with `(venv)`.

3.  **Install Dependencies**
    Install all the required Python packages using `pip`.

    ```bash
    pip install Flask Flask-Cors yt-dlp
    ```

## Running the Server

Once the setup is complete, you can start the Flask development server.

1.  **Run the Application:**
    Make sure you are in the `python-server` directory with your virtual environment activated.

    ```bash
    python3 app.py
    ```

2.  **Verify the Server is Running:**
    You should see output in your terminal indicating that the server is active, typically:

    ```
     * Serving Flask app 'app'
     * Debug mode: on
     * Running on all addresses (0.0.0.0)
     * Running on http://127.0.0.1:3000
    Press CTRL+C to quit
    ```

    The backend is now running and listening for requests on `http://localhost:3000`.

## API Endpoints

### 1. Get Video Info

- **Endpoint:** `POST /info`
- **Description:** Fetches metadata for a given video URL.
- **Request Body (JSON):**
  ```json
  {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }
  ```
- **Success Response (200 OK):**
  ```json
  {
    "title": "Video Title",
    "thumbnail": "https://url.to/thumbnail.jpg",
    "formats": [
      {
        "format_id": "...",
        "ext": "mp4",
        "resolution": "1920x1080",
        "note": "1080p",
        "filesize": 12345678
      }
    ]
  }
  ```

### 2. Download Video

- **Endpoint:** `GET /download`
- **Description:** Streams the video content for a given URL and quality.
- **Query Parameters:**
  - `url`: The full URL of the video to download.
  - `quality`: The desired quality (e.g., `1080p`, `720p`, or `audio`).
- **Example Request:**
  `http://localhost:3000/download?url=https%3A%2F%2F...&quality=720p`
- **Success Response (200 OK):** The server streams the video or audio file directly to the client with the appropriate `Content-Disposition` and `Content-Type` headers, triggering a browser download.

## Project Structure

python-server/
├── venv/ # Virtual environment directory (add to .gitignore)
├── app.py # The main Flask application file
└── README.md # This file

## Troubleshooting

- **"Cannot parse data" or site-specific errors:** Social media sites frequently change their structure, which can break `yt-dlp`. If you encounter errors for a specific platform (e.g., Facebook, Instagram), the first step is always to upgrade `yt-dlp` to the latest version.

  ```bash
  # With your virtual environment active:
  pip install --upgrade yt-dlp
  ```

- **Downloads are audio-only or fail to merge:** This almost always means `ffmpeg` is not installed or not available in your system's PATH. Please verify the `ffmpeg` installation steps in the Prerequisites section.
