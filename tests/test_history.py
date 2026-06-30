"""历史记录模块测试。"""
import json
import pytest
from pathlib import Path
from analyzer.history import History, HistoryEntry


@pytest.fixture
def history_file(tmp_path):
    return tmp_path / "history.json"


def test_add_entry(history_file):
    h = History(history_file)
    h.add(["abc"], {"result": "test"})
    assert len(h.entries) == 1


def test_persistence(history_file):
    h1 = History(history_file)
    h1.add(["abc"], {"result": "test"})
    h2 = History(history_file)
    assert len(h2.entries) == 1


def test_capacity_limit(history_file):
    h = History(history_file, max_entries=3)
    for i in range(5):
        h.add([f"input_{i}"], {"i": i})
    assert len(h.entries) == 3
    # 最新的应该在前
    assert h.entries[0].inputs == ["input_4"]


def test_corrupted_file_recovery(history_file):
    history_file.write_text("not a json")
    h = History(history_file)
    assert h.entries == []


def test_summary():
    e = HistoryEntry(timestamp="2026-06-30T12:00:00", inputs=["abcdef"], result={})
    assert "abcdef" in e.summary()


def test_long_input_truncated():
    long_input = "x" * 100
    e = HistoryEntry(timestamp="2026-06-30T12:00:00", inputs=[long_input], result={})
    assert len(e.summary()) < 100