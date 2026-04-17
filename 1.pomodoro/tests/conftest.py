"""
pytest 共通設定・フィクスチャ
"""
import pytest
from datetime import datetime

from domain.models import TimerConfig, SessionState
from domain.timer import FakeClock
from services.config_service import InMemoryConfigStore
from services.stats_service import InMemoryStatsStore


@pytest.fixture
def default_config() -> TimerConfig:
    """デフォルト設定（作業25分、休憩5分）"""
    return TimerConfig(work_minutes=25, break_minutes=5)


@pytest.fixture
def fake_clock() -> FakeClock:
    """固定時刻を返すテスト用クロック"""
    return FakeClock(fixed_time=datetime(2026, 4, 17, 10, 0, 0))


@pytest.fixture
def initial_state(default_config: TimerConfig) -> SessionState:
    """初期状態（IDLE, WORKモード）"""
    return SessionState()


@pytest.fixture
def config_store() -> InMemoryConfigStore:
    return InMemoryConfigStore()


@pytest.fixture
def stats_store() -> InMemoryStatsStore:
    return InMemoryStatsStore()
