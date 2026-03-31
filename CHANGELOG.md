# Changelog

All notable changes to the Medical Log Analyzer are documented here.

## [1.1.0] - 2024-03-31
### Added
- Unit tests for the analysis engine (`tests/test_analyzer.py`)
- Python `logging` module replacing all `print` statements
- `python-dotenv` support for environment-based configuration (`.env`)
- `CHANGELOG.md` for professional change tracking

### Changed
- `requirements.txt` pinned to Python 3.8–3.12 compatible versions
- Stats query made compatible with SQLAlchemy 1.4

## [1.0.0] - 2024-01-15
### Added
- File upload and log analysis engine (`analyzer.py`)
- SQLite database integration via SQLAlchemy (`models.py`)
- REST API: upload, logs, stats, clear endpoints
- Real-time WebSocket log streaming (Flask-SocketIO, threading mode)
- SaaS-style dashboard (Chart.js, Socket.IO client)
- Alert system — NORMAL / CRITICAL based on error count
- GitHub Actions CI/CD pipeline
- Sample log file for quick testing
