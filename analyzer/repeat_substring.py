"""单字符串内重复最多的子字符串。

找出字符串中所有出现次数 >= min_count 的不同子串，
按出现次数降序排序，每条带 (子串, 出现次数, 所有出现位置)。

性能：对每个长度 L 扫描一次字符串，记录所有 L 长度子串的出现位置。
总复杂度 O(n * (max_length - min_length + 1))，对 n=10KB 约 5×10^7 操作，
在中数据规模下秒级返回。
"""
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class RepeatResult:
    substrings: List[Tuple[str, int, List[int]]] = field(default_factory=list)


def find_repeat_substrings(s: str, min_length: int = 2, max_length: int = 0,
                            min_count: int = 2,
                            max_results: int = 100) -> List[Tuple[str, int, List[int]]]:
    """找出字符串 s 中所有出现次数 >= min_count 的不同子串。

    Args:
        s: 输入字符串
        min_length: 子串最小长度（默认 2）
        max_length: 子串最大长度（0 = 自动设为 n//2）
        min_count: 最少出现次数（默认 2）
        max_results: 最多返回多少个结果（按次数降序，默认 100）

    Returns:
        列表，每项为 (子串, 出现次数, 位置列表)，按次数降序
    """
    n = len(s)
    if n < 2 or min_length < 1:
        return []

    if max_length <= 0:
        max_length = n // 2
    max_length = min(max_length, n - 1)

    if min_length > max_length:
        return []

    # 按长度分组：对每个长度 L，用一个临时 dict 累计所有 L-长度子串位置
    # 出现次数 < min_count 的子串丢弃（节省内存）
    aggregated: Dict[str, Tuple[int, List[int]]] = {}

    for length in range(min_length, max_length + 1):
        # 扫描所有 L-长度子串
        positions: Dict[str, List[int]] = {}
        for i in range(n - length + 1):
            sub = s[i:i + length]
            if sub in positions:
                positions[sub].append(i)
            else:
                positions[sub] = [i]
                # 注意：这里不能直接 discard，因为我们不知道是否还有后续出现
                # 实际上一个子串一旦加入就继续 append

        # 合并到 aggregated
        for sub, pos_list in positions.items():
            if len(pos_list) >= min_count:
                if sub in aggregated:
                    # 同长度已经记录过，累加（理论上不会，因为同长度只算一次）
                    old_count, old_pos = aggregated[sub]
                    merged = sorted(set(old_pos + pos_list))
                    aggregated[sub] = (len(merged), merged)
                else:
                    aggregated[sub] = (len(pos_list), pos_list)

    # 排序：次数降序，次数相同按长度降序，再按首次出现位置
    results = []
    for sub, (count, positions) in aggregated.items():
        results.append((sub, count, positions))

    results.sort(key=lambda x: (-x[1], -len(x[0]), x[2][0]))
    return results[:max_results]


def analyze_one(s: str, min_length: int = 2, max_length: int = 0,
                min_count: int = 2, max_results: int = 100) -> RepeatResult:
    return RepeatResult(
        substrings=find_repeat_substrings(
            s, min_length=min_length, max_length=max_length,
            min_count=min_count, max_results=max_results
        )
    )


def analyze(strings: List[str], min_length: int = 2, max_length: int = 0,
            min_count: int = 2, max_results: int = 100) -> List[RepeatResult]:
    return [
        analyze_one(s, min_length=min_length, max_length=max_length,
                    min_count=min_count, max_results=max_results)
        for s in strings
    ]
