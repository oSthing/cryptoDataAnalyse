"""差异比对：汉明距离、编辑距离、Jaccard 相似度。"""
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class DiffResult:
    hamming: Dict[Tuple[int, int], int] = field(default_factory=dict)
    levenshtein: Dict[Tuple[int, int], int] = field(default_factory=dict)
    jaccard: Dict[Tuple[int, int], float] = field(default_factory=dict)


def hamming_distance(s1: str, s2: str) -> int:
    if len(s1) != len(s2):
        return -1
    return sum(1 for a, b in zip(s1, s2) if a != b)


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            ins = curr[j] + 1
            dele = prev[j + 1] + 1
            sub = prev[j] + (c1 != c2)
            curr.append(min(ins, dele, sub))
        prev = curr
    return prev[-1]


def _ngrams(s: str, n: int) -> set:
    if len(s) < n:
        return {s}
    return {s[i:i+n] for i in range(len(s) - n + 1)}


def jaccard_similarity(s1: str, s2: str, n: int = 3) -> float:
    set1 = _ngrams(s1, n)
    set2 = _ngrams(s2, n)
    if not set1 and not set2:
        return 1.0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union) if union else 0.0


def analyze(strings: list, ngram: int = 3) -> DiffResult:
    result = DiffResult()
    n = len(strings)
    for i in range(n):
        for j in range(i + 1, n):
            result.hamming[(i, j)] = hamming_distance(strings[i], strings[j])
            result.levenshtein[(i, j)] = levenshtein_distance(strings[i], strings[j])
            result.jaccard[(i, j)] = jaccard_similarity(strings[i], strings[j], n=ngram)
    return result