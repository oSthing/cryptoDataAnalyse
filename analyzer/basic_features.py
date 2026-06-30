"""基本特征分析：长度、字符类、唯一字符数。"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BasicFeatures:
    length: int
    unique_chars: int
    char_classes: Dict[str, int]  # upper/lower/digit/other
    is_printable: bool
    has_chinese: bool


def _classify_char(c: str) -> str:
    if c.isupper():
        return "upper"
    if c.islower():
        return "lower"
    if c.isdigit():
        return "digit"
    return "other"


def analyze_one(s: str) -> BasicFeatures:
    char_classes = {"upper": 0, "lower": 0, "digit": 0, "other": 0}
    for c in s:
        char_classes[_classify_char(c)] += 1
    is_printable = all(c.isprintable() for c in s) if s else True
    has_chinese = any('一' <= c <= '鿿' for c in s)
    return BasicFeatures(
        length=len(s),
        unique_chars=len(set(s)),
        char_classes=char_classes,
        is_printable=is_printable,
        has_chinese=has_chinese,
    )


def analyze_all(strings: List[str]) -> List[BasicFeatures]:
    return [analyze_one(s) for s in strings]
