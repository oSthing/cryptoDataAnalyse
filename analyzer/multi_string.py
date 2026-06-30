"""多串关联分析。"""
from dataclasses import dataclass, field
from typing import List, Optional
from analyzer.common_substring import longest_common_substring


@dataclass
class MultiStringResult:
    common_substring_matrix: List[List[int]] = field(default_factory=list)
    length_progression: Optional[str] = None
    can_concatenate: bool = False


def _detect_progression(lengths: List[int]) -> Optional[str]:
    if len(lengths) < 3:
        return None
    diffs = [lengths[i+1] - lengths[i] for i in range(len(lengths) - 1)]
    if all(d > 0 for d in diffs):
        return "递增"
    if all(d < 0 for d in diffs):
        return "递减"
    return "无规律"


def _can_concatenate(strings: List[str], full_string: str) -> bool:
    """检测给定字符串能否按某种顺序拼接成完整字符串。"""
    if not full_string or not strings:
        return False
    from itertools import permutations
    for perm in permutations(strings):
        if ''.join(perm) == full_string:
            return True
    return False


def analyze(strings: List[str], full_string: Optional[str] = None) -> MultiStringResult:
    n = len(strings)
    result = MultiStringResult()

    # 两两公共子串长度矩阵
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            subs = longest_common_substring(strings[i], strings[j])
            max_len = max((len(sub[0]) for sub in subs), default=0)
            matrix[i][j] = max_len
            matrix[j][i] = max_len
    result.common_substring_matrix = matrix

    # 长度递进
    if n >= 3:
        result.length_progression = _detect_progression([len(s) for s in strings])

    # 拼接还原
    if full_string is not None:
        result.can_concatenate = _can_concatenate(strings, full_string)

    return result
