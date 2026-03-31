"""
app.py
------
Entry point for the Medical Log Analyzer & Real-Time Monitoring System.

Architecture
------------
  Flask         : HTTP server + REST API
  Flask-SocketIO: WebSocket server for real-time log streaming
  SQLAlchemy    : ORM layer over SQLite (logs.db)
  analyzer.py   : Pure-Python log analysis engine
  models.py     : Database schema definitions

Run
---
    python app.py
    Then open http://localhost:5000
"""

import logging
import os
import threading
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

from analyzer import analyse_file, generate_realtime_log, parse_lines
from models import LogEntry, db

# ---------------------------------------------------------------------------
# Load environment variables from .env (if present)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Logging setup  —  writes to console AND app.log
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask application setup
# ---------------------------------------------------------------------------
BASE_DIR       = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER  = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTS   = {"txt"}

app = Flask(__name__)
app.config.update(
    SECRET_KEY                  = os.environ.get("SECRET_KEY", "med-log-secret-2024"),
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'logs.db')}"),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    UPLOAD_FOLDER               = UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH          = 16 * 1024 * 1024,   # 16 MB
)

# Bind extensions
db.init_app(app)

# threading async_mode — no eventlet/gevent required, works on Windows
socketio = SocketIO(app, async_mode="gevent", cors_allowed_origins="*")

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create all DB tables on startup
with app.app_context():
    db.create_all()
    log.info("Database initialised.")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    """Return True only when extension is in ALLOWED_EXTS."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS

# ---------------------------------------------------------------------------
# HTTP Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Serve the single-page dashboard."""
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_log():
    """
    POST /api/upload
    ----------------
    Accepts multipart/form-data with field 'logfile'.
    Analyses the file and persists all parsed entries to SQLite.
    Returns JSON analysis summary.
    """
    if "logfile" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["logfile"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only .txt files are allowed"}), 415

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    try:
        file.save(filepath)
        result = analyse_file(filepath)
        log.info("File '%s' analysed — %d lines.", filename, result.total_lines)
    except Exception as exc:
        log.error("Failed to process file: %s", exc)
        return jsonify({"error": f"Failed to process file: {exc}"}), 500

    # Persist parsed log entries to the database
    try:
        for entry in result.parsed_logs:
            db.session.add(LogEntry(
                content=entry["content"],
                level=entry["level"],
                source="upload",
            ))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        log.error("Database error: %s", exc)
        return jsonify({"error": f"Database error: {exc}"}), 500

    return jsonify({
        "filename":       filename,
        "total_lines":    result.total_lines,
        "counts":         result.counts,
        "alert_status":   result.alert_status,
        "error_messages": result.error_messages,
    })


@app.route("/api/logs", methods=["GET"])
def get_logs():
    """
    GET /api/logs
    -------------
    Returns all stored log entries as a JSON array (newest first, max 500).
    Supports optional ?source= filter  (upload | realtime).
    """
    source = request.args.get("source")
    query  = LogEntry.query
    if source:
        query = query.filter_by(source=source)
    logs = query.order_by(LogEntry.id.desc()).limit(500).all()
    return jsonify([l.to_dict() for l in logs])


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """
    GET /api/stats
    --------------
    Returns aggregate counts grouped by level + current alert status.
    Used by the dashboard to populate stats cards on page load.
    """
    from sqlalchemy import func

    rows = (
        db.session.query(LogEntry.level, func.count(LogEntry.id).label("cnt"))
        .group_by(LogEntry.level)
        .all()
    )
    counts = {"INFO": 0, "WARNING": 0, "ERROR": 0}
    for level, count in rows:
        counts[level] = count

    alert_status = "CRITICAL" if counts.get("ERROR", 0) > 2 else "NORMAL"
    return jsonify({"counts": counts, "alert_status": alert_status})


@app.route("/api/clear", methods=["DELETE"])
def clear_logs():
    """DELETE /api/clear — Wipe all log entries from the database."""
    try:
        db.session.query(LogEntry).delete()
        db.session.commit()
        log.info("All logs cleared.")
        return jsonify({"message": "All logs cleared"})
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500

# ---------------------------------------------------------------------------
# WebSocket — Real-Time Log Streaming
# ---------------------------------------------------------------------------

_streaming_active = False
_stream_lock      = threading.Lock()


def _stream_logs():
    """
    Background daemon thread.
    Emits a simulated log entry every 2 seconds via the 'new_log' event.
    Also persists each entry to SQLite.
    """
    global _streaming_active
    while True:
        with _stream_lock:
            if not _streaming_active:
                break

        log_data = generate_realtime_log()

        with app.app_context():
            try:
                entry = LogEntry(
                    content=log_data["content"],
                    level=log_data["level"],
                    source="realtime",
                )
                db.session.add(entry)
                db.session.commit()
                log_data["id"] = entry.id
            except Exception as exc:
                db.session.rollback()
                log.error("Realtime DB error: %s", exc)

        socketio.emit("new_log", log_data)
        time.sleep(2)


@socketio.on("connect")
def on_connect():
    emit("connected", {"message": "Connected to Medical Log Monitor"})
    log.info("Client connected.")


@socketio.on("start_stream")
def on_start_stream():
    """Start the background log-generation thread."""
    global _streaming_active
    with _stream_lock:
        if _streaming_active:
            emit("stream_status", {"status": "already_running"})
            return
        _streaming_active = True

    thread = threading.Thread(target=_stream_logs, daemon=True)
    thread.start()
    log.info("Real-time stream started.")
    emit("stream_status", {"status": "started"})


@socketio.on("stop_stream")
def on_stop_stream():
    """Stop the background log-generation thread."""
    global _streaming_active
    with _stream_lock:
        _streaming_active = False
    log.info("Real-time stream stopped.")
    emit("stream_status", {"status": "stopped"})


@socketio.on("disconnect")
def on_disconnect():
    global _streaming_active
    with _stream_lock:
        _streaming_active = False
    log.info("Client disconnected.")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    log.info("Medical Log Analyzer starting on http://localhost:%s", port)
    socketio.run(app, host="0.0.0.0", port=port, debug=debug)
