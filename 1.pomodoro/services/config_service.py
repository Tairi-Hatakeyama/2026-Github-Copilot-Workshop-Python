from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models import TimerConfig


class ConfigStore(ABC):
    """設定の読み書きを抽象化するインターフェース"""

    @abstractmethod
    def get_config(self) -> TimerConfig:
        ...

    @abstractmethod
    def save_config(self, config: TimerConfig) -> None:
        ...


class InMemoryConfigStore(ConfigStore):
    """テスト用のメモリ内設定ストア"""

    def __init__(self) -> None:
        self._config = TimerConfig()

    def get_config(self) -> TimerConfig:
        return self._config

    def save_config(self, config: TimerConfig) -> None:
        self._config = config


class FileConfigStore(ConfigStore):
    """JSONファイルへの設定保存（将来的に SQLite へ移行可能）"""

    def __init__(self, file_path: str = "config.json") -> None:
        self._file_path = file_path

    def get_config(self) -> TimerConfig:
        import json
        import os

        if not os.path.exists(self._file_path):
            return TimerConfig()
        with open(self._file_path, encoding="utf-8") as f:
            data = json.load(f)
        return TimerConfig(
            work_minutes=data.get("work_minutes", 25),
            break_minutes=data.get("break_minutes", 5),
        )

    def save_config(self, config: TimerConfig) -> None:
        import json

        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(
                {"work_minutes": config.work_minutes, "break_minutes": config.break_minutes},
                f,
                ensure_ascii=False,
                indent=2,
            )
