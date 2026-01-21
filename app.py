from flask import Flask, render_template, request, jsonify, send_from_directory
import os, threading, json
import yt_dlp

BASE = os.path.dirname(os.path.abspath(__file__))
SONGS = os.path.join(BASE, "songs")
PLAYLISTS = os.path.join(BASE, "playlists")
FFMPEG = os.path.join(BASE, "ffmpeg")

os.makedirs(SONGS, exist_ok=True)
os.makedirs(PLAYLISTS, exist_ok=True)

app = Flask(__name__)

download_progress = 0

# ---------------- HELPERS ----------------
def progress_hook(d):
    global download_progress
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        if total:
            download_progress = int(d["downloaded_bytes"] / total * 100)
    elif d["status"] == "finished":
        download_progress = 100

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/songs")
def songs():
    return jsonify([f for f in os.listdir(SONGS) if f.endswith(".mp3")])

@app.route("/download", methods=["POST"])
def download():
    global download_progress
    url = request.json["url"]
    download_progress = 0

    def task():
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(SONGS, "%(title).200s.%(ext)s"),
            "restrictfilenames": True,
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "ffmpeg_location": FFMPEG,
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    threading.Thread(target=task, daemon=True).start()
    return jsonify({"status": "started"})

@app.route("/progress")
def progress():
    return jsonify({"progress": download_progress})

@app.route("/songs/<path:filename>")
def serve_song(filename):
    return send_from_directory(SONGS, filename)

if __name__ == "__main__":
    app.run(debug=True)
