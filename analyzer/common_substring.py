"""最长公共子串/子序列分析。"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class CommonSubstringResult:
    pairwise: Dict[Tuple[int, int], List[Tuple[str, int, int]]] = field(default_factory=dict)
    multi: List[Tuple[str, List[int]]] = field(default_factory=list)
    common_prefix: int = 0
    common_suffix: int = 0


def longest_common_substring(s1: str, s2: str) -> List[Tuple[str, int, int]]:
    """返回所有最长公共子串及其在 s1, s2 中的起始位置。"""
    if not s1 or not s2:
        return []

    n, m = len(s1), len(s2)
    # dp[i][j] = 以 s1[i-1], s2[j-1] 结尾的公共子串长度
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    max_len = 0
    results = []

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
                if dp[i][j] > max_len:
                    max_len = dp[i][j]
                    results = [(s1[i-max_len:i], i - max_len, j - max_len)]
                elif dp[i][j] == max_len and max_len > 0:
                    results.append((s1[i-max_len:i], i - max_len, j - max_len))

    return results


def longest_common_subsequence(s1: str, s2: str) -> int:
    """返回最长公共子序列长度。"""
    if not s1 or not s2:
        return 0
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[n][m]


def common_prefix_length(s1: str, s2: str) -> int:
    n = min(len(s1), len(s2))
    i = 0
    while i < n and s1[i] == s2[i]:
        i += 1
    return i


def common_suffix_length(s1: str, s2: str) -> int:
    n = min(len(s1), len(s2))
    i = 0
    while i < n and s1[-(i+1)] == s2[-(i+1)]:
        i += 1
    return i


def _multi_lcs(strings: List[str]) -> List[Tuple[str, List[int]]]:
    """求多串公共子串。返回所有最长公共子串及在每条串中的起始位置。"""
    if not strings or len(strings) < 3:
        return []
    # 收集所有串对之间的最长公共子串，做交集
    pairwise_subs: List[List[str]] = []
    for i in range(1, len(strings)):
        subs = longest_common_substring(strings[0], strings[i])
        pairwise_subs.append([s[0] for s in subs])

    if not pairwise_subs or not any(pairwise_subs):
        return []

    # 交集
    candidate_subs = set(pairwise_subs[0])
    for subs in pairwise_subs[1:]:
        candidate_subs &= set(subs)
        if not candidate_subs:
            return []

    if not candidate_subs:
        return []

    max_len = max(len(s) for s in candidate_subs)
    result = []
    for sub in candidate_subs:
        if len(sub) == max_len:
            positions = [s.find(sub) for s in strings]
            result.append((sub, positions))
    return result


def analyze(strings: List[str]) -> CommonSubstringResult:
    result = CommonSubstringResult()
    if not strings:
        return result

    # 两两公共子串
    n = len(strings)
    for i in range(n):
        for j in range(i + 1, n):
            subs = longest_common_substring(strings[i], strings[j])
            if subs:
                result.pairwise[(i, j)] = subs

    # 多串公共子串
    if n >= 3:
        result.multi = _multi_lcs(strings)

    # 公共前缀/后缀（仅多串时计算）
    if n >= 2:
        prefix = len(strings[0])
        suffix = len(strings[0])
        for s in strings[1:]:
            prefix = min(prefix, common_prefix_length(strings[0], s))
            suffix = min(suffix, common_suffix_length(strings[0], s))
        result.common_prefix = prefix
        result.common_suffix = suffix
    else:
        result.common_prefix = len(strings[0])
        result.common_suffix = len(strings[0])

    return result
