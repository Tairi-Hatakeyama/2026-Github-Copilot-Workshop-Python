"""
domain/models.py のテスト
"""
import pytest

from domain.models import DailyStats, Mode, SessionState, Status, TimerConfig


class TestTimerConfig:
    def test_default_values(self):
        cfg = TimerConfig()
        assert cfg.work_minutes == 25
        assert cfg.break_minutes == 5

    def test_work_seconds(self):
        cfg = TimerConfig(work_minutes=25)
        assert cfg.work_seconds() == 1500

    def test_break_seconds(self):
        cfg = TimerConfig(break_minutes=5)
        assert cfg.break_seconds() == 300

    def test_custom_values(self):
        cfg = TimerConfig(work_minutes=30, break_minutes=10)
        assert cfg.work_seconds() == 1800
        assert cfg.break_seconds() == 600


class TestSessionState:
    def test_default_mode_is_work(self):
        assert SessionState().current_mode == Mode.WORK

    def test_default_status_is_idle(self):
        assert SessionState().current_status == Status.IDLE

    def test_default_remaining_seconds(self):
        assert SessionState().remaining_seconds == 25 * 60

    def test_default_session_count_is_zero(self):
        assert SessionState().session_count == 0

    def test_default_end_at_is_none(self):
        assert SessionState().end_at is None


class TestDailyStats:
    def test_instantiation(self):
        stats = DailyStats(date="2026-04-17", completed_work_sessions=3,
                           completed_break_sessions=2, focused_minutes=75)
        assert stats.completed_work_sessions == 3
        assert stats.focused_minutes == 75

    def test_default_values(self):
        stats = DailyStats()
        assert stats.completed_work_sessions == 0
        assert stats.focused_minutes == 0
