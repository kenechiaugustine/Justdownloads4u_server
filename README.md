# Social Media Video Downloader - Backend

This is the backend server for the Social Media Video Downloader application. It has been modernized to use **FastAPI**, offering high performance, automatic API documentation, and asynchronous capabilities. It leverages the powerful `yt-dlp` library to fetch metadata and stream video content from various social media platforms.

## Features

- **Metadata Fetching:** Provides an API endpoint to get video details like title, thumbnail, and available formats.
- **Direct Video Streaming:** Downloads and streams video content directly to the client, initiating the browser's download immediately.
- **Wide Compatibility:** Supports all platforms that `yt-dlp` supports (YouTube, TikTok, Instagram, X/Twitter, Facebook, etc.).
- **Quality Selection:** Allows the client to request a specific video quality or audio-only format.
- **FastAPI Powered:** Built with modern Python features for speed and reliability.
- **Automatic Docs:** Interactive API documentation available at `/docs`.

## Prerequisites

Before you begin, you have two options to run this application:

### Option 1: Docker (Recommended for Easy Deployment)

1.  **Docker**
    - Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
    - To verify installation: `docker --version`

2.  **Docker Compose** (usually included with Docker Desktop)
    - To verify installation: `docker-compose --version`

### Option 2: Local Python Setup

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

## Quick Start with Docker (Recommended)

The easiest way to run this application is using Docker. This method handles all dependencies (including ffmpeg) automatically.

### Using Docker Compose

1.  **Start the Application**
    ```bash
    docker-compose up -d
    ```
    This will build the Docker image and start the container in detached mode.

2.  **View Logs**
    ```bash
    docker-compose logs -f
    ```

3.  **Stop the Application**
    ```bash
    docker-compose down
    ```

The API will be available at `http://localhost:3000`

### Using Docker Directly

1.  **Build the Docker Image**
    ```bash
    docker build -t justdownloads4u-api .
    ```

2.  **Run the Container**
    ```bash
    docker run -d -p 3000:3000 --name justdownloads4u-api justdownloads4u-api
    ```

3.  **Stop the Container**
    ```bash
    docker stop justdownloads4u-api
    docker rm justdownloads4u-api
    ```

### Development Mode with Docker

To enable hot-reload for development, uncomment the volume mounts in `docker-compose.yml`:

```yaml
volumes:
  - ./main.py:/app/main.py
  - ./models.py:/app/models.py
```

Then restart the container:
```bash
docker-compose down
docker-compose up -d
```

---

## Local Setup and Installation (Without Docker)

Follow these steps to set up and run the server locally without Docker.

1.  **Clone the Repository**
    If you haven't already, clone the project to your local machine.

    ```bash
    git clone <your-repository-url>
    cd <your-project-folder>/server_py
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
    Install all the required Python packages using `pip` and the provided `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

Once the setup is complete, you can start the FastAPI server.

1.  **Run the Application:**
    Make sure you are in the `server_py` directory with your virtual environment activated.

    ```bash
    # Using python directly
    python3 main.py

    # OR using uvicorn directly (for development with auto-reload)
    uvicorn main:app --reload --host 0.0.0.0 --port 3000
    ```

2.  **Verify the Server is Running:**
    You should see output in your terminal indicating that the server is active, typically:

    ```
    INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)
    INFO:     Started reloader process [...] using StatReload
    INFO:     Started server process [...]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    ```

    The backend is now running and listening for requests on `http://localhost:3000`.

## API Documentation

FastAPI automatically generates interactive API documentation.

- **Swagger UI:** Open [http://localhost:3000/docs](http://localhost:3000/docs) in your browser to explore and test the API endpoints interactively.
- **ReDoc:** Open [http://localhost:3000/redoc](http://localhost:3000/redoc) for an alternative documentation view.

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
- **Success Response (200 OK):** The server streams the video or audio file directly to the client.

## Project Structure

```
server_py/
├── venv/               # Virtual environment directory (add to .gitignore)
├── main.py             # The main FastAPI application file
├── models.py           # Pydantic models for request/response schemas
├── requirements.txt    # Project dependencies
├── temp/               # Temporary directory for downloads
└── README.md           # This file
```

## Troubleshooting

- **"Cannot parse data" or site-specific errors:** Social media sites frequently change their structure, which can break `yt-dlp`. If you encounter errors for a specific platform (e.g., Facebook, Instagram), the first step is always to upgrade `yt-dlp` to the latest version.

  ```bash
  # With your virtual environment active:
  pip install --upgrade yt-dlp
  ```

- **Downloads are audio-only or fail to merge:** This almost always means `ffmpeg` is not installed or not available in your system's PATH. Please verify the `ffmpeg` installation steps in the Prerequisites section.
