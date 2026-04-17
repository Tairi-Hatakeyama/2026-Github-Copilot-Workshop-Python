from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List

from domain.models import DailyStats


class StatsStore(ABC):
    """統計情報の読み書きを抽象化するインターフェース"""

    @abstractmethod
    def add_session(self, event_type: str, completed_at: datetime) -> None:
        ...

    @abstractmethod
    def get_today_stats(self) -> DailyStats:
        ...

    @abstractmethod
    def get_stats_range(self, start: date, end: date) -> List[DailyStats]:
        ...


class InMemoryStatsStore(StatsStore):
    """テスト用のメモリ内統計ストア"""

    def __init__(self) -> None:
        self._sessions: list = []

    def add_session(self, event_type: str, completed_at: datetime) -> None:
        self._sessions.append({"event_type": event_type, "completed_at": completed_at})

    def get_today_stats(self) -> DailyStats:
        today = date.today()
        return self._aggregate(today)

    def get_stats_range(self, start: date, end: date) -> List[DailyStats]:
        result = []
        current = start
        from datetime import timedelta
        while current <= end:
            result.append(self._aggregate(current))
            current += timedelta(days=1)
        return result

    def _aggregate(self, target_date: date) -> DailyStats:
        work_sessions = 0
        break_sessions = 0
        for s in self._sessions:
            if s["completed_at"].date() == target_date:
                if s["event_type"] == "work_completed":
                    work_sessions += 1
                elif s["event_type"] == "break_completed":
                    break_sessions += 1
        return DailyStats(
            date=target_date.isoformat(),
            completed_work_sessions=work_sessions,
            completed_break_sessions=break_sessions,
            focused_minutes=work_sessions * 25,
        )


class FileStatsStore(StatsStore):
    """JSONファイルへの統計保存（将来的に SQLite へ移行可能）"""

    def __init__(self, file_path: str = "stats.json") -> None:
        self._file_path = file_path
        self._mem = InMemoryStatsStore()
        self._load()

    def _load(self) -> None:
        import json
        import os
        if not os.path.exists(self._file_path):
            return
        with open(self._file_path, encoding="utf-8") as f:
            sessions = json.load(f)
        from datetime import datetime as dt
        for s in sessions:
            self._mem._sessions.append({
                "event_type": s["event_type"],
                "completed_at": dt.fromisoformat(s["completed_at"]),
            })

    def _save(self) -> None:
        import json
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(
                [{"event_type": s["event_type"], "completed_at": s["completed_at"].isoformat()}
                 for s in self._mem._sessions],
                f,
                ensure_ascii=False,
                indent=2,
            )

    def add_session(self, event_type: str, completed_at: datetime) -> None:
        self._mem.add_session(event_type, completed_at)
        self._save()

    def get_today_stats(self) -> DailyStats:
        return self._mem.get_today_stats()

    def get_stats_range(self, start: date, end: date) -> List[DailyStats]:
        return self._mem.get_stats_range(start, end)
