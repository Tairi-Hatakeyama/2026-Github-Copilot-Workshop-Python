from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Tuple

from .events import (
    CompleteEvent,
    PauseEvent,
    ResetEvent,
    ResumeEvent,
    StartEvent,
    TimerEvent,
)
from .models import DailyStats, Mode, SessionState, Status, TimerConfig


class Clock(ABC):
    """現在時刻取得の抽象クラス（テスト時に差し替え可能）"""

    @abstractmethod
    def now(self) -> datetime:
        ...


class SystemClock(Clock):
    """本番環境で使用するシステムクロック"""

    def now(self) -> datetime:
        return datetime.now()


class FakeClock(Clock):
    """テスト用の固定クロック"""

    def __init__(self, fixed_time: datetime) -> None:
        self._time = fixed_time

    def now(self) -> datetime:
        return self._time

    def advance(self, seconds: int) -> None:
        """指定秒数だけ時刻を進める"""
        from datetime import timedelta
        self._time += timedelta(seconds=seconds)


def handle_event(
    current_state: SessionState,
    event: TimerEvent,
    config: TimerConfig,
    clock: Clock,
) -> SessionState:
    """
    現在状態 + イベント → 次状態を返す純粋関数。
    副作用（通知・音・保存）はここでは行わない。
    """
    if isinstance(event, StartEvent):
        return _handle_start(current_state, config, clock)
    elif isinstance(event, PauseEvent):
        return _handle_pause(current_state, clock)
    elif isinstance(event, ResumeEvent):
        return _handle_resume(current_state, clock)
    elif isinstance(event, ResetEvent):
        return _handle_reset(current_state, config)
    elif isinstance(event, CompleteEvent):
        return _handle_complete(current_state, config, clock)
    else:
        raise ValueError(f"未知のイベント: {event}")


def _handle_start(
    state: SessionState, config: TimerConfig, clock: Clock
) -> SessionState:
    """idle → running"""
    from datetime import timedelta

    if state.current_status != Status.IDLE:
        return state  # 既に実行中またはポーズ中は無視

    total = (
        config.work_seconds()
        if state.current_mode == Mode.WORK
        else config.break_seconds()
    )
    now = clock.now()
    end_at = now + timedelta(seconds=total)
    return SessionState(
        current_mode=state.current_mode,
        current_status=Status.RUNNING,
        remaining_seconds=total,
        end_at=end_at,
        paused_at=None,
        session_count=state.session_count,
        started_at=now,
    )


def _handle_pause(state: SessionState, clock: Clock) -> SessionState:
    """running → paused"""
    if state.current_status != Status.RUNNING:
        return state

    remaining = calculate_remaining_seconds(state.end_at, clock)
    return SessionState(
        current_mode=state.current_mode,
        current_status=Status.PAUSED,
        remaining_seconds=remaining,
        end_at=None,
        paused_at=clock.now(),
        session_count=state.session_count,
        started_at=state.started_at,
    )


def _handle_resume(state: SessionState, clock: Clock) -> SessionState:
    """paused → running"""
    from datetime import timedelta

    if state.current_status != Status.PAUSED:
        return state

    now = clock.now()
    new_end_at = now + timedelta(seconds=state.remaining_seconds)
    return SessionState(
        current_mode=state.current_mode,
        current_status=Status.RUNNING,
        remaining_seconds=state.remaining_seconds,
        end_at=new_end_at,
        paused_at=None,
        session_count=state.session_count,
        started_at=state.started_at,
    )


def _handle_reset(state: SessionState, config: TimerConfig) -> SessionState:
    """<any> → idle（同じモードの初期状態へ戻る）"""
    total = (
        config.work_seconds()
        if state.current_mode == Mode.WORK
        else config.break_seconds()
    )
    return SessionState(
        current_mode=state.current_mode,
        current_status=Status.IDLE,
        remaining_seconds=total,
        end_at=None,
        paused_at=None,
        session_count=state.session_count,
        started_at=None,
    )


def _handle_complete(
    state: SessionState, config: TimerConfig, clock: Clock
) -> SessionState:
    """running + complete → 次モードの idle"""
    next_mode = Mode.BREAK if state.current_mode == Mode.WORK else Mode.WORK
    total = (
        config.break_seconds()
        if next_mode == Mode.BREAK
        else config.work_seconds()
    )
    return SessionState(
        current_mode=next_mode,
        current_status=Status.IDLE,
        remaining_seconds=total,
        end_at=None,
        paused_at=None,
        session_count=state.session_count + 1,
        started_at=None,
    )


def calculate_remaining_seconds(end_at: datetime, clock: Clock) -> int:
    """
    終了予定時刻と現在時刻の差分を秒単位で返す。
    過ぎていた場合は 0 を返す。
    """
    delta = (end_at - clock.now()).total_seconds()
    return max(0, int(delta))


def calculate_progress_percentage(
    remaining_seconds: int, total_seconds: int
) -> float:
    """
    進捗率を 0.0 ～ 1.0 で返す。
    0.0 が開始直後、1.0 が完了。
    """
    if total_seconds <= 0:
        return 1.0
    elapsed = total_seconds - remaining_seconds
    return max(0.0, min(1.0, elapsed / total_seconds))
