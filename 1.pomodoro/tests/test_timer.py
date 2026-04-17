"""
domain/timer.py のテスト（状態遷移・時間計算）
"""
import pytest
from datetime import datetime, timedelta

from domain.events import (
    CompleteEvent,
    PauseEvent,
    ResetEvent,
    ResumeEvent,
    StartEvent,
)
from domain.models import Mode, SessionState, Status, TimerConfig
from domain.timer import (
    FakeClock,
    calculate_progress_percentage,
    calculate_remaining_seconds,
    handle_event,
)


class TestHandleStart:
    def test_idle_start_becomes_running(self, initial_state, default_config, fake_clock):
        new_state = handle_event(initial_state, StartEvent(), default_config, fake_clock)
        assert new_state.current_status == Status.RUNNING

    def test_start_sets_end_at(self, initial_state, default_config, fake_clock):
        new_state = handle_event(initial_state, StartEvent(), default_config, fake_clock)
        expected_end = fake_clock.now() + timedelta(seconds=default_config.work_seconds())
        assert new_state.end_at == expected_end

    def test_start_sets_remaining_to_total(self, initial_state, default_config, fake_clock):
        new_state = handle_event(initial_state, StartEvent(), default_config, fake_clock)
        assert new_state.remaining_seconds == default_config.work_seconds()

    def test_running_start_is_ignored(self, default_config, fake_clock):
        running = SessionState(current_status=Status.RUNNING,
                               end_at=fake_clock.now() + timedelta(seconds=100))
        new_state = handle_event(running, StartEvent(), default_config, fake_clock)
        assert new_state.current_status == Status.RUNNING

    def test_break_mode_start_uses_break_seconds(self, default_config, fake_clock):
        state = SessionState(current_mode=Mode.BREAK, current_status=Status.IDLE,
                             remaining_seconds=default_config.break_seconds())
        new_state = handle_event(state, StartEvent(), default_config, fake_clock)
        assert new_state.remaining_seconds == default_config.break_seconds()


class TestHandlePause:
    def test_running_pause_becomes_paused(self, default_config, fake_clock):
        start_state = handle_event(SessionState(), StartEvent(), default_config, fake_clock)
        fake_clock.advance(60)
        paused = handle_event(start_state, PauseEvent(), default_config, fake_clock)
        assert paused.current_status == Status.PAUSED

    def test_pause_saves_remaining_seconds(self, default_config, fake_clock):
        start_state = handle_event(SessionState(), StartEvent(), default_config, fake_clock)
        fake_clock.advance(60)
        paused = handle_event(start_state, PauseEvent(), default_config, fake_clock)
        assert paused.remaining_seconds == default_config.work_seconds() - 60

    def test_pause_clears_end_at(self, default_config, fake_clock):
        start_state = handle_event(SessionState(), StartEvent(), default_config, fake_clock)
        paused = handle_event(start_state, PauseEvent(), default_config, fake_clock)
        assert paused.end_at is None

    def test_idle_pause_is_ignored(self, default_config, fake_clock):
        state = SessionState()
        new_state = handle_event(state, PauseEvent(), default_config, fake_clock)
        assert new_state.current_status == Status.IDLE


class TestHandleResume:
    def test_paused_resume_becomes_running(self, default_config, fake_clock):
        start = handle_event(SessionState(), StartEvent(), default_config, fake_clock)
        fake_clock.advance(60)
        paused = handle_event(start, PauseEvent(), default_config, fake_clock)
        fake_clock.advance(30)
        resumed = handle_event(paused, ResumeEvent(), default_config, fake_clock)
        assert resumed.current_status == Status.RUNNING

    def test_resume_recalculates_end_at(self, default_config, fake_clock):
        start = handle_event(SessionState(), StartEvent(), default_config, fake_clock)
        fake_clock.advance(60)
        paused = handle_event(start, PauseEvent(), default_config, fake_clock)
        fake_clock.advance(30)
        resumed = handle_event(paused, ResumeEvent(), default_config, fake_clock)
        expected_end = fake_clock.now() + timedelta(seconds=paused.remaining_seconds)
        assert resumed.end_at == expected_end

    def test_idle_resume_is_ignored(self, default_config, fake_clock):
        state = SessionState()
        new_state = handle_event(state, ResumeEvent(), default_config, fake_clock)
        assert new_state.current_status == Status.IDLE


class TestHandleReset:
    def test_running_reset_becomes_idle(self, default_config, fake_clock):
        start = handle_event(SessionState(), StartEvent(), default_config, fake_clock)
        reset = handle_event(start, ResetEvent(), default_config, fake_clock)
        assert reset.current_status == Status.IDLE

    def test_paused_reset_becomes_idle(self, default_config, fake_clock):
        start = handle_event(SessionState(), StartEvent(), default_config, fake_clock)
        paused = handle_event(start, PauseEvent(), default_config, fake_clock)
        reset = handle_event(paused, ResetEvent(), default_config, fake_clock)
        assert reset.current_status == Status.IDLE

    def test_reset_clears_end_at(self, default_config, fake_clock):
        start = handle_event(SessionState(), StartEvent(), default_config, fake_clock)
        reset = handle_event(start, ResetEvent(), default_config, fake_clock)
        assert reset.end_at is None

    def test_reset_restores_remaining_to_total(self, default_config, fake_clock):
        start = handle_event(SessionState(), StartEvent(), default_config, fake_clock)
        fake_clock.advance(300)
        reset = handle_event(start, ResetEvent(), default_config, fake_clock)
        assert reset.remaining_seconds == default_config.work_seconds()

    def test_reset_preserves_session_count(self, default_config, fake_clock):
        state = SessionState(session_count=3, current_status=Status.RUNNING,
                             end_at=fake_clock.now() + timedelta(seconds=100))
        reset = handle_event(state, ResetEvent(), default_config, fake_clock)
        assert reset.session_count == 3


class TestHandleComplete:
    def test_work_complete_switches_to_break(self, default_config, fake_clock):
        state = SessionState(current_mode=Mode.WORK, current_status=Status.RUNNING,
                             end_at=fake_clock.now())
        new_state = handle_event(state, CompleteEvent(), default_config, fake_clock)
        assert new_state.current_mode == Mode.BREAK

    def test_break_complete_switches_to_work(self, default_config, fake_clock):
        state = SessionState(current_mode=Mode.BREAK, current_status=Status.RUNNING,
                             end_at=fake_clock.now())
        new_state = handle_event(state, CompleteEvent(), default_config, fake_clock)
        assert new_state.current_mode == Mode.WORK

    def test_complete_becomes_idle(self, default_config, fake_clock):
        state = SessionState(current_mode=Mode.WORK, current_status=Status.RUNNING,
                             end_at=fake_clock.now())
        new_state = handle_event(state, CompleteEvent(), default_config, fake_clock)
        assert new_state.current_status == Status.IDLE

    def test_complete_increments_session_count(self, default_config, fake_clock):
        state = SessionState(session_count=2, current_status=Status.RUNNING,
                             end_at=fake_clock.now())
        new_state = handle_event(state, CompleteEvent(), default_config, fake_clock)
        assert new_state.session_count == 3

    def test_work_complete_sets_break_remaining(self, default_config, fake_clock):
        state = SessionState(current_mode=Mode.WORK, current_status=Status.RUNNING,
                             end_at=fake_clock.now())
        new_state = handle_event(state, CompleteEvent(), default_config, fake_clock)
        assert new_state.remaining_seconds == default_config.break_seconds()


class TestCalculateRemainingSeconds:
    def test_returns_correct_remaining(self, fake_clock):
        end_at = fake_clock.now() + timedelta(seconds=500)
        assert calculate_remaining_seconds(end_at, fake_clock) == 500

    def test_returns_zero_when_past_end_at(self, fake_clock):
        end_at = fake_clock.now() - timedelta(seconds=10)
        assert calculate_remaining_seconds(end_at, fake_clock) == 0

    def test_returns_zero_at_exact_end(self, fake_clock):
        end_at = fake_clock.now()
        assert calculate_remaining_seconds(end_at, fake_clock) == 0


class TestCalculateProgressPercentage:
    def test_zero_at_start(self):
        assert calculate_progress_percentage(1500, 1500) == 0.0

    def test_one_at_complete(self):
        assert calculate_progress_percentage(0, 1500) == 1.0

    def test_half_at_midpoint(self):
        assert abs(calculate_progress_percentage(750, 1500) - 0.5) < 1e-9

    def test_clamped_above_one(self):
        assert calculate_progress_percentage(-100, 1500) == 1.0

    def test_total_zero_returns_one(self):
        assert calculate_progress_percentage(0, 0) == 1.0
