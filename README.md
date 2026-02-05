# YouTube Downloader Backend

FastAPI backend service for YouTube video/audio downloading.

## Features

- Extract available video formats and qualities
- Download videos in MP4 format (various qualities)
- Download audio in MP3 format
- CORS support for frontend integration
- File serving for downloaded content

## Requirements

- Python 3.8+
- yt-dlp >= 2024.12.06
- FFmpeg (for video processing)

## Installation

```bash
# Create virtual environment
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Server

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### GET `/`
Health check endpoint

### GET `/formats?url={video_url}`
Returns available video formats and qualities

### GET `/download?url={video_url}&format={mp4|mp3}&quality={best|1080|720|480|360|240|144}`
Downloads video/audio in specified format and quality

### GET `/file?filename={filename}`
Serves downloaded files

## Environment Variables

- `DOWNLOAD_FOLDER`: Path to store downloaded files (default: `/tmp`)

## Dependencies

- **FastAPI**: Web framework
- **uvicorn**: ASGI server
- **yt-dlp**: YouTube downloader
- **python-multipart**: File upload support

## Notes

- Uses Android client configuration for yt-dlp to avoid YouTube restrictions
- Automatically cleans up old downloads before new ones
- Supports video qualities up to 4K depending on source
- Requires FFmpeg for video processing and merging