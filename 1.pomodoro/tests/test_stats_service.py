"""
services/stats_service.py のテスト
"""
import pytest
from datetime import datetime, date, timedelta

from domain.models import DailyStats
from services.stats_service import InMemoryStatsStore


class TestInMemoryStatsStore:
    def test_add_work_session(self, stats_store):
        stats_store.add_session("work_completed", datetime.now())
        assert stats_store.get_today_stats().completed_work_sessions == 1

    def test_get_today_stats_empty(self, stats_store):
        stats = stats_store.get_today_stats()
        assert stats.completed_work_sessions == 0
        assert stats.completed_break_sessions == 0
        assert stats.focused_minutes == 0

    def test_get_today_stats_after_session(self, stats_store):
        stats_store.add_session("work_completed", datetime.now())
        stats_store.add_session("break_completed", datetime.now())
        stats = stats_store.get_today_stats()
        assert stats.completed_work_sessions == 1
        assert stats.completed_break_sessions == 1

    def test_focused_minutes_accumulate(self, stats_store):
        stats_store.add_session("work_completed", datetime.now())
        stats_store.add_session("work_completed", datetime.now())
        assert stats_store.get_today_stats().focused_minutes == 50

    def test_yesterday_session_not_counted_today(self, stats_store):
        stats_store.add_session("work_completed", datetime.now() - timedelta(days=1))
        assert stats_store.get_today_stats().completed_work_sessions == 0

    def test_get_stats_range_returns_correct_dates(self, stats_store):
        today = date.today()
        stats_store.add_session("work_completed", datetime.now())
        results = stats_store.get_stats_range(today, today)
        assert len(results) == 1
        assert results[0].date == today.isoformat()
        assert results[0].completed_work_sessions == 1

    def test_get_stats_range_multiple_days(self, stats_store):
        today = date.today()
        yesterday = today - timedelta(days=1)
        stats_store.add_session(
            "work_completed",
            datetime.combine(yesterday, datetime.min.time()),
        )
        stats_store.add_session("work_completed", datetime.now())
        results = stats_store.get_stats_range(yesterday, today)
        assert len(results) == 2
        assert results[0].completed_work_sessions == 1
        assert results[1].completed_work_sessions == 1
