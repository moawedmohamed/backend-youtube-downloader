import subprocess
import os
import glob
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_FOLDER = "/tmp"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.get("/file")
def get_file(filename: str):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/octet-stream", filename=filename)
    return {"status": "error", "message": "File not found"}

@app.get("/formats")
def get_available_formats(url: str):
    try:
        command = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android,web",  # استخدم android
            "--extractor-args", "youtube:skip=translated_subs",
            "--no-check-certificates",
            "-F",
            "--no-warnings",
            url
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        lines = result.stdout.strip().split('\n')
        formats = []
        
        for line in lines:
            if 'mp4' in line and ('x' in line or 'p' in line):
                parts = line.split()
                if len(parts) >= 2:
                    format_id = parts[0]
                    
                    quality = None
                    for part in parts:
                        if 'x' in part:
                            height = part.split('x')[1]
                            quality = f"{height}p"
                            break
                        elif part.endswith('p'):
                            quality = part
                            break
                    
                    if quality and format_id.isdigit():
                        formats.append({
                            "format_id": format_id,
                            "quality": quality,
                            "description": line.strip()
                        })
        
        unique_formats = {}
        for fmt in formats:
            q = fmt['quality']
            if q not in unique_formats:
                unique_formats[q] = fmt
        
        sorted_formats = sorted(
            unique_formats.values(),
            key=lambda x: int(x['quality'].replace('p', '')),
            reverse=True
        )
        
        return {
            "status": "success",
            "formats": sorted_formats
        }
        
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Request timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/download")
def download_video(
    url: str, 
    format: str = Query("mp4", enum=["mp3", "mp4"]),
    quality: str = Query("best", description="Quality: best, 1080, 720, 480, 360, 240, 144")
):
    for f in glob.glob(os.path.join(DOWNLOAD_FOLDER, "*")):
        try:
            os.remove(f)
        except:
            pass
    
    output_path = f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s"

    if format == "mp3":
        command = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android",
            "--no-check-certificates",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",  # أفضل جودة صوت
            "-o", output_path,
            url
        ]
    else:
        # استخدم صيغة مبسطة جداً
        if quality == "best":
            format_string = "bv*+ba/b"
        else:
            format_string = f"bv*[height<={quality}]+ba/b[height<={quality}]"
        
        command = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android",  # Android client يعمل بدون PO token
            "--no-check-certificates",
            "--format", format_string,
            "--merge-output-format", "mp4",
            "-o", output_path,
            url
        ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print("=" * 50)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("=" * 50)

        files = glob.glob(os.path.join(DOWNLOAD_FOLDER, "*"))
        
        if not files:
            return {"status": "error", "message": "No file downloaded"}
        
        filename = max(files, key=os.path.getctime).split("/")[-1]
        
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,width,height",
            "-of", "csv=p=0",
            file_path
        ]
        
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        streams = probe_result.stdout.strip().split('\n')
        
        has_video = any('video' in s for s in streams)
        has_audio = any('audio' in s for s in streams)
        
        actual_quality = "unknown"
        for stream in streams:
            if 'video' in stream:
                parts = stream.split(',')
                if len(parts) >= 3:
                    height = parts[2]
                    actual_quality = f"{height}p"
                    break

        return {
            "status": "success",
            "message": "Download completed!",
            "filename": filename,
            "debug": {
                "has_video": has_video,
                "has_audio": has_audio,
                "requested_quality": quality,
                "actual_quality": actual_quality,
                "streams": streams
            }
        }

    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Download timeout"}
    except subprocess.CalledProcessError as e:
        error_message = e.stderr if e.stderr else str(e)
        print("ERROR:", error_message)
        return {"status": "error", "message": f"Download failed. YouTube may have blocked this video."}

@app.get("/")
def root():
    return {"message": "YouTube Downloader Backend is Running!"}