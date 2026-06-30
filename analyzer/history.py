"""历史记录持久化。"""
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class HistoryEntry:
    timestamp: str
    inputs: List[str]
    result: Dict[str, Any]

    def summary(self) -> str:
        first = self.inputs[0] if self.inputs else ""
        if len(first) > 50:
            first = first[:50] + "..."
        return f"{self.timestamp} | {first}"


class History:
    def __init__(self, path: Path, max_entries: int = 20):
        self.path = path
        self.max_entries = max_entries
        self.entries: List[HistoryEntry] = []
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            self.entries = [HistoryEntry(**e) for e in data]
        except (json.JSONDecodeError, TypeError, KeyError):
            # 文件损坏，备份后重置
            backup = self.path.with_suffix('.json.bak')
            try:
                self.path.rename(backup)
            except OSError:
                pass
            self.entries = []

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(e) for e in self.entries]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    def add(self, inputs: List[str], result: Dict[str, Any]):
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(),
            inputs=inputs,
            result=result,
        )
        self.entries.insert(0, entry)
        self.entries = self.entries[:self.max_entries]
        self._save()

    def clear(self):
        self.entries = []
        self._save()