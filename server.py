# server.py
import os
import re
import shutil
import tempfile

import yt_dlp
from flask import Flask, after_this_request, jsonify, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=os.environ.get("ALLOWED_ORIGIN", "*"))

URL_PATTERN = re.compile(
    r"^https?://(www\.)?instagram\.com/(p|reel|reels|tv)/[A-Za-z0-9_\-]+/?(\?.*)?$"
)


@app.route("/")
def health():
    return "ok"


@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not URL_PATTERN.match(url):
        return jsonify(error="Invalid Instagram URL."), 400

    tmp = tempfile.mkdtemp()
    opts = {
        "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
    }

    @after_this_request
    def cleanup(response):
        shutil.rmtree(tmp, ignore_errors=True)
        return response

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
        return send_file(
            path,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="instagram_video.mp4",
        )
    except yt_dlp.utils.DownloadError:
        return jsonify(error="Could not download. Post may be private, removed, or require login."), 400
    except Exception as e:
        return jsonify(error=f"Server error: {e}"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))