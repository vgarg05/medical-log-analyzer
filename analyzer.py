"""
analyzer.py
-----------
Pure-Python log analysis engine — no Flask dependency.

Responsibilities
----------------
* Parse raw log text line-by-line
* Detect log levels  : INFO | WARNING | ERROR
* Count occurrences of each level
* Extract error messages into a dedicated list
* Generate alert status : NORMAL (errors <= 2) | CRITICAL (errors > 2)
* Simulate realistic medical-device log lines for the real-time stream
"""

import re
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CRITICAL_THRESHOLD = 2          # errors above this → CRITICAL alert

# Patterns ordered most-to-least severe so first match wins
LEVEL_PATTERNS = [
    ("ERROR",   re.compile(r"\bERROR\b",   re.IGNORECASE)),
    ("WARNING", re.compile(r"\bWARNING\b", re.IGNORECASE)),
    ("INFO",    re.compile(r"\bINFO\b",    re.IGNORECASE)),
]

# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

@dataclass
class AnalysisResult:
    """
    Output of one analysis run.

    Attributes
    ----------
    total_lines    : Non-empty lines processed
    counts         : {level: count} mapping
    error_messages : List of full text of ERROR lines
    alert_status   : 'CRITICAL' | 'NORMAL'
    parsed_logs    : List of dicts ready for DB insertion
    """
    total_lines:    int             = 0
    counts:         Dict[str, int]  = field(default_factory=lambda: {"INFO": 0, "WARNING": 0, "ERROR": 0})
    error_messages: List[str]       = field(default_factory=list)
    alert_status:   str             = "NORMAL"
    parsed_logs:    List[Dict]      = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------

def detect_level(line: str) -> str:
    """
    Return the severity level of a single log line.
    Falls back to 'INFO' when no keyword is matched.
    """
    for level, pattern in LEVEL_PATTERNS:
        if pattern.search(line):
            return level
    return "INFO"


def parse_lines(raw_text: str) -> AnalysisResult:
    """
    Analyse multi-line log content and return an AnalysisResult.

    Steps
    -----
    1. Split into lines; skip blank lines.
    2. Detect level of each line.
    3. Accumulate counts and error messages.
    4. Derive alert status.
    """
    result = AnalysisResult()
    lines  = [l.rstrip() for l in raw_text.splitlines() if l.strip()]
    result.total_lines = len(lines)

    for line in lines:
        level = detect_level(line)
        result.counts[level] = result.counts.get(level, 0) + 1

        if level == "ERROR":
            result.error_messages.append(line)

        result.parsed_logs.append({"content": line, "level": level})

    result.alert_status = (
        "CRITICAL" if result.counts.get("ERROR", 0) > CRITICAL_THRESHOLD else "NORMAL"
    )
    return result


def analyse_file(filepath: str) -> AnalysisResult:
    """
    Read a file from disk and run parse_lines on its content.
    Raises FileNotFoundError / IOError on read problems.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    return parse_lines(raw)


# ---------------------------------------------------------------------------
# Real-time log simulator
# ---------------------------------------------------------------------------

_LOG_TEMPLATES = [
    "INFO  [{ts}] HeartRateMonitor   - BPM reading: {val} bpm — within normal range",
    "INFO  [{ts}] OxygenSensor       - SpO2 level: {val}% — stable",
    "INFO  [{ts}] BloodPressure      - Systolic {val} mmHg — no anomaly detected",
    "INFO  [{ts}] TempSensor         - Body temperature: {val}°C — nominal",
    "INFO  [{ts}] DeviceManager      - Firmware heartbeat OK — uptime {val} min",
    "WARNING [{ts}] HeartRateMonitor - BPM reading: {val} bpm — elevated, monitoring",
    "WARNING [{ts}] OxygenSensor     - SpO2 dipped to {val}% — alert threshold approaching",
    "WARNING [{ts}] BloodPressure    - Systolic spike: {val} mmHg — retrying calibration",
    "WARNING [{ts}] BatteryModule    - Battery at {val}% — charge recommended",
    "ERROR [{ts}] HeartRateMonitor   - BPM reading INVALID ({val}) — sensor fault",
    "ERROR [{ts}] OxygenSensor       - SpO2 critically low: {val}% — immediate attention",
    "ERROR [{ts}] DeviceManager      - Connection lost after {val} retries — offline",
    "ERROR [{ts}] BloodPressure      - Calibration FAILED — error code {val}",
]


def generate_realtime_log() -> Dict[str, str]:
    """
    Generate one simulated medical-device log line.
    Returns a dict with keys: content, level, created_at.
    """
    template = random.choice(_LOG_TEMPLATES)
    ts       = datetime.now().strftime("%H:%M:%S")
    val      = random.randint(40, 200)
    content  = template.format(ts=ts, val=val)
    return {
        "content":    content,
        "level":      detect_level(content),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
