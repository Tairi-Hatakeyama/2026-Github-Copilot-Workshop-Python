from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Mode(Enum):
    WORK = "work"
    BREAK = "break"


class Status(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class TimerConfig:
    work_minutes: int = 25
    break_minutes: int = 5

    def work_seconds(self) -> int:
        return self.work_minutes * 60

    def break_seconds(self) -> int:
        return self.break_minutes * 60


@dataclass
class SessionState:
    current_mode: Mode = Mode.WORK
    current_status: Status = Status.IDLE
    remaining_seconds: int = 25 * 60
    end_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    session_count: int = 0
    started_at: Optional[datetime] = None


@dataclass
class DailyStats:
    date: str = ""
    completed_work_sessions: int = 0
    completed_break_sessions: int = 0
    focused_minutes: int = 0
