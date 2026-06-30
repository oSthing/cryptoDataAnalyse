"""公共子串/子序列分析。

- longest_common_substring:  最长公共子串（连续）
- longest_common_subsequence: 最长公共子序列（不连续）
- all_common_substrings:    所有公共子串（≥min_length 字符）
- common_prefix_length/suffix_length
- analyze:                   综合分析
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class CommonSubstringResult:
    pairwise: Dict[Tuple[int, int], List[Tuple[str, int, int]]] = field(default_factory=dict)
    multi: List[Tuple[str, List[int]]] = field(default_factory=list)
    common_prefix: int = 0
    common_suffix: int = 0
    # 新增：所有公共子串（按长度降序），用于"显示全部重复"
    all_pairwise: Dict[Tuple[int, int], List[Tuple[str, int, int]]] = field(default_factory=dict)
    all_multi: List[Tuple[str, List[int]]] = field(default_factory=list)


def longest_common_substring(s1: str, s2: str) -> List[Tuple[str, int, int]]:
    """返回所有最长公共子串及其在 s1, s2 中的起始位置。"""
    if not s1 or not s2:
        return []

    n, m = len(s1), len(s2)
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


def _collect_all_substrings(s: str, min_length: int = 1) -> Set[str]:
    """返回字符串 s 中所有长度 >= min_length 的不同子串集合。"""
    if not s or min_length < 1:
        return set()
    n = len(s)
    subs: Set[str] = set()
    for i in range(n):
        # 收集以 i 起始的所有子串（去重）
        seen_at_i: Set[str] = set()
        for j in range(i + min_length, n + 1):
            sub = s[i:j]
            if sub not in seen_at_i:
                seen_at_i.add(sub)
                subs.add(sub)
    return subs


def all_common_substrings(s1: str, s2: str, min_length: int = 1) -> List[Tuple[str, int, int]]:
    """返回 s1, s2 中所有长度 >= min_length 的公共子串，按长度降序。

    去重规则：若一个子串已被任何"更长"的公共子串包含（位置重叠且完全在内部），
    则不显示。位置定义：
      - 包含 = 子串 A 完全在 子串 B 的范围内（按各自串内的位置）
    """
    subs1 = _collect_all_substrings(s1, min_length)
    if not subs1:
        return []
    subs2 = _collect_all_substrings(s2, min_length)
    common = subs1 & subs2
    if not common:
        return []

    # 收集每个子串在 s1 和 s2 中第一次出现的位置
    raw = []
    for sub in common:
        raw.append((sub, s1.find(sub), s2.find(sub)))
    # 按长度降序，长度相同时按首次出现位置升序
    raw.sort(key=lambda x: (-len(x[0]), x[1], x[2]))

    # 去重：跳过被已通过项完全包含的子串
    results: List[Tuple[str, int, int]] = []
    for sub, pos_i, pos_j in raw:
        if pos_i < 0 or pos_j < 0:
            continue
        sub_len = len(sub)
        # 检查是否被之前已通过的任何项包含
        contained = False
        for kept_sub, kept_i, kept_j in results:
            if (pos_i >= kept_i
                    and pos_i + sub_len <= kept_i + len(kept_sub)
                    and pos_j >= kept_j
                    and pos_j + sub_len <= kept_j + len(kept_sub)):
                contained = True
                break
        if not contained:
            results.append((sub, pos_i, pos_j))
    return results


def all_multi_common_substrings(strings: List[str], min_length: int = 1) -> List[Tuple[str, List[int]]]:
    """返回多串（≥3 串）所有长度 >= min_length 的公共子串。

    去重规则：若一个子串已被任何"更长"的公共子串在每条串内都完全包含，则不显示。
    """
    if not strings or len(strings) < 3:
        return []
    base = strings[0]
    candidate = _collect_all_substrings(base, min_length)
    for s in strings[1:]:
        sub_set = _collect_all_substrings(s, min_length)
        candidate &= sub_set
        if not candidate:
            return []
    if not candidate:
        return []

    raw = []
    for sub in candidate:
        positions = [s.find(sub) for s in strings]
        raw.append((sub, positions))
    raw.sort(key=lambda x: (-len(x[0]), x[1][0]))

    # 去重：跳过被已通过项在每条串中都包含的子串
    results: List[Tuple[str, List[int]]] = []
    for sub, positions in raw:
        if any(p < 0 for p in positions):
            continue
        sub_len = len(sub)
        contained = False
        for kept_sub, kept_pos in results:
            # 必须在每条串内都被包含
            all_inside = all(
                positions[k] >= kept_pos[k]
                and positions[k] + sub_len <= kept_pos[k] + len(kept_sub)
                for k in range(len(strings))
            )
            if all_inside:
                contained = True
                break
        if not contained:
            results.append((sub, positions))
    return results


def _multi_lcs(strings: List[str]) -> List[Tuple[str, List[int]]]:
    """求多串公共子串（最长）。"""
    if not strings or len(strings) < 3:
        return []
    base = strings[0]
    pairwise_subs: List[List[str]] = []
    for i in range(1, len(strings)):
        subs = longest_common_substring(strings[0], strings[i])
        pairwise_subs.append([s[0] for s in subs])

    if not pairwise_subs or not any(pairwise_subs):
        return []

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


def analyze(strings: List[str], min_length: int = 1) -> CommonSubstringResult:
    """综合分析公共子串/子序列。

    min_length: 用于 all_pairwise / all_multi 的子串最小长度。
    """
    result = CommonSubstringResult()
    if not strings:
        return result

    n = len(strings)

    # 最长公共子串（两两 + 多串）
    for i in range(n):
        for j in range(i + 1, n):
            subs = longest_common_substring(strings[i], strings[j])
            if subs:
                result.pairwise[(i, j)] = subs

    if n >= 3:
        result.multi = _multi_lcs(strings)

    # 所有公共子串（按长度降序）
    for i in range(n):
        for j in range(i + 1, n):
            all_subs = all_common_substrings(strings[i], strings[j], min_length=min_length)
            if all_subs:
                result.all_pairwise[(i, j)] = all_subs

    if n >= 3:
        result.all_multi = all_multi_common_substrings(strings, min_length=min_length)

    # 公共前缀/后缀
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
