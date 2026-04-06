from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import yt_dlp
import threading
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

def download_video(url, format_type):
    output_path = os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s")
    
    if format_type == "video":
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'progress_hooks': [progress_hook]
        }
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [progress_hook]
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0.0%')
        socketio.emit('progress', {'percent': percent})
    elif d['status'] == 'finished':
        socketio.emit('progress', {'percent': '100%', 'done': True})

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format_type = request.form['format']

    # Start download in background thread
    threading.Thread(target=download_video, args=(url, format_type)).start()
    return "Download started"

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
