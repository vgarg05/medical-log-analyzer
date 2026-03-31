"""
tests/test_analyzer.py
----------------------
Unit tests for the log analysis engine (analyzer.py).
Run with:  pytest tests/ -v
"""

import sys
import os

# Make sure the parent directory is on the path so we can import analyzer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from analyzer import detect_level, parse_lines, generate_realtime_log

# ---------------------------------------------------------------------------
# detect_level()
# ---------------------------------------------------------------------------

class TestDetectLevel:

    def test_detects_error_uppercase(self):
        assert detect_level("ERROR [12:00] sensor fault detected") == "ERROR"

    def test_detects_warning_uppercase(self):
        assert detect_level("WARNING battery level low") == "WARNING"

    def test_detects_info_uppercase(self):
        assert detect_level("INFO system is running normally") == "INFO"

    def test_case_insensitive_error(self):
        assert detect_level("error something went wrong") == "ERROR"

    def test_case_insensitive_warning(self):
        assert detect_level("warning threshold approaching") == "WARNING"

    def test_error_takes_priority_over_warning(self):
        # Line contains both keywords — ERROR should win (higher severity)
        assert detect_level("ERROR WARNING mixed line") == "ERROR"

    def test_default_to_info_when_no_keyword(self):
        assert detect_level("device heartbeat ok 72bpm") == "INFO"

    def test_empty_string_defaults_to_info(self):
        assert detect_level("") == "INFO"


# ---------------------------------------------------------------------------
# parse_lines()
# ---------------------------------------------------------------------------

class TestParseLines:

    def test_counts_each_level_correctly(self):
        text = "\n".join([
            "INFO system ok",
            "INFO another info",
            "WARNING battery low",
            "ERROR sensor fault",
            "ERROR connection lost",
        ])
        result = parse_lines(text)
        assert result.counts["INFO"]    == 2
        assert result.counts["WARNING"] == 1
        assert result.counts["ERROR"]   == 2

    def test_total_lines_excludes_blank_lines(self):
        text = "INFO ok\n\n\nWARNING low\n"
        result = parse_lines(text)
        assert result.total_lines == 2

    def test_alert_normal_when_errors_equal_threshold(self):
        # Exactly 2 errors → NORMAL
        text = "ERROR one\nERROR two"
        result = parse_lines(text)
        assert result.alert_status == "NORMAL"

    def test_alert_critical_when_errors_exceed_threshold(self):
        # 3 errors → CRITICAL
        text = "ERROR one\nERROR two\nERROR three"
        result = parse_lines(text)
        assert result.alert_status == "CRITICAL"

    def test_alert_normal_when_no_errors(self):
        text = "INFO all good\nWARNING minor issue"
        result = parse_lines(text)
        assert result.alert_status == "NORMAL"

    def test_error_messages_extracted(self):
        text = "ERROR fault detected\nINFO all good\nERROR another fault"
        result = parse_lines(text)
        assert len(result.error_messages) == 2
        assert all("ERROR" in m for m in result.error_messages)

    def test_empty_input_returns_zero_counts(self):
        result = parse_lines("")
        assert result.total_lines == 0
        assert result.counts["INFO"]    == 0
        assert result.counts["WARNING"] == 0
        assert result.counts["ERROR"]   == 0
        assert result.alert_status == "NORMAL"

    def test_parsed_logs_list_length_matches_total_lines(self):
        text = "INFO a\nWARNING b\nERROR c"
        result = parse_lines(text)
        assert len(result.parsed_logs) == result.total_lines == 3

    def test_parsed_logs_contain_correct_keys(self):
        result = parse_lines("INFO system ok")
        assert "content" in result.parsed_logs[0]
        assert "level"   in result.parsed_logs[0]


# ---------------------------------------------------------------------------
# generate_realtime_log()
# ---------------------------------------------------------------------------

class TestGenerateRealtimeLog:

    def test_returns_required_keys(self):
        log = generate_realtime_log()
        assert "content"    in log
        assert "level"      in log
        assert "created_at" in log

    def test_level_is_valid(self):
        for _ in range(20):   # run several times due to randomness
            log = generate_realtime_log()
            assert log["level"] in ("INFO", "WARNING", "ERROR")

    def test_content_is_non_empty_string(self):
        log = generate_realtime_log()
        assert isinstance(log["content"], str)
        assert len(log["content"]) > 0
