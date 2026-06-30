"""Tests for analyzer.basic_features."""
from analyzer.basic_features import analyze_all, BasicFeatures


def test_empty_string():
    result = analyze_all([""])[0]
    assert result.length == 0
    assert result.unique_chars == 0
    assert result.char_classes == {"upper": 0, "lower": 0, "digit": 0, "other": 0}


def test_single_char():
    result = analyze_all(["A"])[0]
    assert result.length == 1
    assert result.unique_chars == 1
    assert result.char_classes == {"upper": 1, "lower": 0, "digit": 0, "other": 0}


def test_mixed_strings():
    strings = ["ABC123", "abc!@#"]
    results = analyze_all(strings)
    assert results[0].length == 6
    assert results[0].char_classes == {"upper": 3, "lower": 0, "digit": 3, "other": 0}
    assert results[1].char_classes == {"upper": 0, "lower": 3, "digit": 0, "other": 3}


def test_chinese_detection():
    result = analyze_all(["你好"])[0]
    assert result.has_chinese is True
    assert result.is_printable is True


def test_unique_chars():
    result = analyze_all(["aabbcc"])[0]
    assert result.unique_chars == 3


def test_all_identical():
    result = analyze_all(["aaaa"])[0]
    assert result.unique_chars == 1
    assert result.length == 4


def test_special_characters():
    result = analyze_all(["\n\t  "])[0]
    assert result.is_printable is False
    assert result.char_classes["other"] == 4
