# 🏥 MedLog — Medical Device Log Analyzer & Real-Time Monitor

A production-ready full-stack web application that simulates monitoring of medical device logs —
built to demonstrate real-world healthcare telemetry pipelines with clean architecture,
modular components, REST APIs, real-time WebSocket streaming, and automated testing.

Designed with software quality principles aligned to **IEC 62304** (medical device software lifecycle).

---

## ✨ Features

| Feature | Details |
|---|---|
| File Upload | Drag-and-drop or click to upload `.txt` log files |
| Log Analysis | Detects INFO / WARNING / ERROR levels, counts each |
| Alert System | NORMAL (≤ 2 errors) · CRITICAL (> 2 errors) |
| SQLite Storage | All parsed entries stored via SQLAlchemy ORM |
| REST API | `/api/logs` · `/api/stats` · `/api/upload` · `/api/clear` |
| Real-Time Stream | WebSocket-powered simulated medical device logs every 2s |
| Dashboard UI | Chart.js bar chart · stats cards · live terminal · alert banner |
| Unit Tests | pytest test suite covering analysis engine |
| Logging | Python logging module — console + file (`app.log`) |

---

## 📁 Project Structure

```
medical-log-analyzer/
├── app.py                        ← Flask app, REST API, SocketIO, entry point
├── analyzer.py                   ← Log analysis engine + real-time simulator
├── models.py                     ← SQLAlchemy LogEntry model
├── requirements.txt              ← Python dependencies (pinned)
├── .env                          ← Environment configuration
├── CHANGELOG.md                  ← Version history
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml                ← GitHub Actions CI/CD
├── tests/
│   ├── __init__.py
│   └── test_analyzer.py          ← Unit tests (pytest)
├── uploads/
│   └── sample_medical.txt        ← Sample log file for quick testing
└── templates/
    └── index.html                ← Dashboard (HTML + CSS + JS)
```

---

## 🚀 How to Run (Step by Step)

### Step 1 — Open terminal in project folder

```
cd medical-log-analyzer
```

### Step 2 — Create virtual environment

```
python -m venv venv
```

### Step 3 — Activate virtual environment

Windows PowerShell:
```
venv\Scripts\activate
```

Mac / Linux:
```
source venv/bin/activate
```

### Step 4 — Install dependencies

```
pip install -r requirements.txt
```

### Step 5 — Run the app

```
python app.py
```

### Step 6 — Open in browser

```
http://localhost:5000
```

---

## 🧪 Run Tests

```
pytest tests/ -v
```

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/logs` | All stored log entries |
| GET | `/api/logs?source=upload` | Filter by source |
| GET | `/api/stats` | Counts + alert status |
| POST | `/api/upload` | Upload & analyse a `.txt` file |
| DELETE | `/api/clear` | Wipe all logs |

---

## 🛠 Common Errors & Fixes

| Error | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside venv |
| `TypeError: Can't replace canonical symbol` | SQLAlchemy version mismatch — use pinned `requirements.txt` |
| Port 5000 in use | Set `PORT=5001` in `.env` |
| Upload returns 415 | Only `.txt` files accepted |
| WebSocket fails | App auto-falls-back to HTTP long-polling |

---

## 📄 License

MIT — free for personal and commercial use.
