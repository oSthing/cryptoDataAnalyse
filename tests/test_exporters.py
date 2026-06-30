import json
from datetime import datetime
from exporters import to_json, to_markdown
from analyzer.basic_features import BasicFeatures


def test_to_json_basic():
    data = {
        "timestamp": "2026-06-30T12:00:00",
        "inputs": ["abc"],
        "basic_features": [BasicFeatures(length=3, unique_chars=3, char_classes={"upper":0,"lower":3,"digit":0,"other":0}, is_printable=True, has_chinese=False)],
        "patterns": [["全字母", "可打印ASCII"]],
    }
    output = to_json(data)
    parsed = json.loads(output)
    assert parsed["inputs"] == ["abc"]
    assert parsed["basic_features"][0]["length"] == 3


def test_to_markdown_basic():
    data = {
        "timestamp": "2026-06-30T12:00:00",
        "inputs": ["abc", "123"],
        "basic_features": [
            BasicFeatures(length=3, unique_chars=3, char_classes={"upper":0,"lower":3,"digit":0,"other":0}, is_printable=True, has_chinese=False),
            BasicFeatures(length=3, unique_chars=3, char_classes={"upper":0,"lower":0,"digit":3,"other":0}, is_printable=True, has_chinese=False),
        ],
        "patterns": [["全字母"], ["全数字"]],
    }
    output = to_markdown(data)
    assert "# 数据分析报告" in output
    assert "abc" in output
    assert "123" in output
    assert "全字母" in output
    assert "全数字" in output


def test_to_json_empty():
    data = {"timestamp": "2026-06-30T12:00:00", "inputs": [], "basic_features": [], "patterns": []}
    output = to_json(data)
    assert json.loads(output)["inputs"] == []


def test_to_markdown_empty():
    data = {"timestamp": "2026-06-30T12:00:00", "inputs": [], "basic_features": [], "patterns": []}
    output = to_markdown(data)
    assert "# 数据分析报告" in output
