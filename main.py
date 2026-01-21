import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os, threading, subprocess, time, json
import yt_dlp

# ---------------- CONFIG ----------------
BASE = os.path.dirname(os.path.abspath(__file__))
SONGS = os.path.join(BASE, "songs")
PLAYLISTS = os.path.join(BASE, "playlists")
FFMPEG = os.path.join(BASE, "ffmpeg")
FFPLAY = os.path.join(FFMPEG, "ffplay.exe")
FFPROBE = os.path.join(FFMPEG, "ffprobe.exe")

os.makedirs(SONGS, exist_ok=True)
os.makedirs(PLAYLISTS, exist_ok=True)

# ---------------- THEME ----------------
COLORS = [
    "#0f0f1a", "#121225", "#151531", "#18183d"
]
ACCENT = "#7c7cff"
TEXT = "#eaeaff"
MUTED = "#9a9ac9"

# ---------------- STATE ----------------
player = None
current_song = None
duration = 0
playing = False
volume = 80

# ---------------- UTIL ----------------
def get_duration(path):
    try:
        result = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries",
             "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except:
        return 0

def format_time(sec):
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"

# ---------------- GRADIENT ----------------
grad_index = 0
def animate_bg():
    global grad_index
    root.configure(bg=COLORS[grad_index])
    grad_index = (grad_index + 1) % len(COLORS)
    root.after(3500, animate_bg)

# ---------------- PLAYLISTS ----------------
def load_playlist(name):
    tree.delete(*tree.get_children())
    path = os.path.join(PLAYLISTS, f"{name}.json")
    if os.path.exists(path):
        with open(path) as f:
            songs = json.load(f)
        for s in songs:
            tree.insert("", "end", values=(s,))

def save_playlist(name):
    songs = [tree.item(i)["values"][0] for i in tree.get_children()]
    with open(os.path.join(PLAYLISTS, f"{name}.json"), "w") as f:
        json.dump(songs, f)

def new_playlist():
    name = simpledialog.askstring("Playlist", "Playlist name:")
    if name:
        save_playlist(name)
        playlist_box["values"] = os.listdir(PLAYLISTS)
        playlist_box.set(f"{name}.json")

# ---------------- PLAYER ----------------
def play():
    global player, current_song, duration, playing
    sel = tree.selection()
    if not sel:
        return
    song = tree.item(sel[0])["values"][0]
    path = os.path.join(SONGS, song)

    stop()

    duration = get_duration(path)
    seek.config(to=duration)
    dur_label.config(text=format_time(duration))

    player = subprocess.Popen(
        [FFPLAY, "-nodisp", "-autoexit",
         "-volume", str(volume), path],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    current_song = song
    playing = True
    status.set(f"▶ {song}")
    update_seek()

def stop():
    global player, playing
    if player:
        player.terminate()
        player = None
    playing = False
    seek.set(0)

def update_seek():
    if playing:
        seek.set(seek.get() + 1)
        pos_label.config(text=format_time(seek.get()))
        root.after(1000, update_seek)

def change_volume(val):
    global volume
    volume = int(float(val))

# ---------------- DOWNLOAD ----------------
def start_download():
    url = url_entry.get().strip()
    if not url:
        return
    threading.Thread(target=download, args=(url,), daemon=True).start()

def download(url):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(SONGS, "%(title).200s.%(ext)s"),
        "restrictfilenames": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
        "ffmpeg_location": FFMPEG,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    refresh()

# ---------------- UI ----------------
root = tk.Tk()
root.title("🎧 VibeTune Ultimate")
root.geometry("900x620")
animate_bg()

status = tk.StringVar(value="Ready")

tk.Label(root, text="VibeTune", fg=ACCENT,
         font=("Segoe UI", 22, "bold"),
         bg=COLORS[0]).pack()

# Playlist
playlist_box = ttk.Combobox(root)
playlist_box.pack()
playlist_box.bind("<<ComboboxSelected>>",
                  lambda e: load_playlist(playlist_box.get().replace(".json","")))

tk.Button(root, text="+ Playlist", command=new_playlist).pack(pady=3)

# URL
url_entry = tk.Entry(root)
url_entry.pack(fill="x", padx=20)
tk.Button(root, text="⬇ Download", command=start_download).pack(pady=5)

# Song list
tree = ttk.Treeview(root, columns=("Song",), show="headings")
tree.heading("Song", text="🎵 Song")
tree.pack(fill="both", expand=True, padx=20, pady=5)

def refresh():
    tree.delete(*tree.get_children())
    for f in os.listdir(SONGS):
        if f.endswith(".mp3"):
            tree.insert("", "end", values=(f,))

refresh()

# Controls
ctrl = tk.Frame(root)
ctrl.pack()

tk.Button(ctrl, text="▶ Play", command=play).grid(row=0, column=0, padx=5)
tk.Button(ctrl, text="⏹ Stop", command=stop).grid(row=0, column=1, padx=5)

# Seek
seek = ttk.Scale(root, from_=0, to=100)
seek.pack(fill="x", padx=20)

pos_label = tk.Label(root, text="00:00", fg=MUTED)
pos_label.pack(side="left", padx=20)

dur_label = tk.Label(root, text="00:00", fg=MUTED)
dur_label.pack(side="right", padx=20)

# Volume
tk.Label(root, text="🔊 Volume", fg=TEXT).pack()
vol = ttk.Scale(root, from_=0, to=100, command=change_volume)
vol.set(volume)
vol.pack(padx=40)

# Footer
tk.Label(root, textvariable=status, fg=MUTED).pack(pady=8)
tk.Label(root, text="Made with ❤️ by Yash • Ultimate Edition",
         fg=MUTED).pack()

root.mainloop()
