"""
models.py
---------
SQLAlchemy database models for the Medical Log Analyzer.
Defines the LogEntry table stored in SQLite (logs.db).
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialized here; bound to the Flask app in app.py via db.init_app(app)
db = SQLAlchemy()


class LogEntry(db.Model):
    """
    Represents a single parsed log entry persisted in the database.

    Columns
    -------
    id         : Auto-incremented primary key
    content    : Full text of the log line
    level      : Detected severity  —  INFO | WARNING | ERROR
    source     : Origin of the log  —  'upload' | 'realtime'
    created_at : UTC timestamp of insertion
    """

    __tablename__ = "log_entries"

    id         = db.Column(db.Integer,     primary_key=True)
    content    = db.Column(db.Text,        nullable=False)
    level      = db.Column(db.String(10),  nullable=False, default="INFO")
    source     = db.Column(db.String(20),  nullable=False, default="upload")
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        """Return a JSON-serialisable dictionary of this record."""
        return {
            "id":         self.id,
            "content":    self.content,
            "level":      self.level,
            "source":     self.source,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __repr__(self):
        return f"<LogEntry id={self.id} level={self.level}>"
