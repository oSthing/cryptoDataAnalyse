"""周期性检测：检测字符串最小重复周期。"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PeriodicityResult:
    min_period: Optional[int]
    pattern: Optional[str]


def detect_period(s: str) -> Optional[int]:
    """检测字符串最小周期。返回周期长度，无周期则返回 None。"""
    n = len(s)
    if n < 2:
        return None
    for period in range(1, n // 2 + 1):
        if n % period != 0:
            continue
        if all(s[i] == s[i % period] for i in range(n)):
            return period
    return None


def analyze_one(s: str) -> PeriodicityResult:
    period = detect_period(s)
    pattern = s[:period] if period else None
    return PeriodicityResult(min_period=period, pattern=pattern)


def analyze(strings: List[str]) -> List[PeriodicityResult]:
    return [analyze_one(s) for s in strings]
