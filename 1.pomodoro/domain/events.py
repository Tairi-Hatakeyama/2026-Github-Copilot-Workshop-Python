from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class TimerEvent(ABC):
    """タイマーイベントの基底クラス"""
    pass


@dataclass
class StartEvent(TimerEvent):
    """タイマー開始イベント"""
    pass


@dataclass
class PauseEvent(TimerEvent):
    """タイマー一時停止イベント"""
    pass


@dataclass
class ResumeEvent(TimerEvent):
    """タイマー再開イベント"""
    pass


@dataclass
class ResetEvent(TimerEvent):
    """タイマーリセットイベント"""
    pass


@dataclass
class CompleteEvent(TimerEvent):
    """タイマー完了イベント"""
    pass
