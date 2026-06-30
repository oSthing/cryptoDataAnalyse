"""单串重复子串测试。"""
from analyzer.repeat_substring import find_repeat_substrings, analyze_one, analyze


def test_repeat_basic():
    """abcabc 重复 'abc' 2 次。"""
    results = find_repeat_substrings("abcabc", min_length=2, min_count=2)
    substrs = {r[0]: r[1] for r in results}
    # 'abc' 出现 2 次
    assert substrs.get("abc") == 2
    # 'ab' 出现 2 次（位置 0 和 3）
    assert substrs.get("ab") == 2
    # 'bc' 出现 2 次
    assert substrs.get("bc") == 2
    # 默认 min_length=2 不包含长度 1 的 'a'


def test_repeat_min_length_1():
    """min_length=1 包含单字符。"""
    results = find_repeat_substrings("abcabc", min_length=1, min_count=2)
    substrs = {r[0]: r[1] for r in results}
    assert substrs.get("a") == 2
    assert substrs.get("b") == 2
    assert substrs.get("c") == 2


def test_repeat_no_repeat():
    """无重复。"""
    results = find_repeat_substrings("abcdef", min_length=2, min_count=2)
    assert results == []


def test_repeat_overlapping():
    """重叠匹配：'aaaa' 中 'aa' 出现 3 次（位置 0, 1, 2）。"""
    results = find_repeat_substrings("aaaa", min_length=2, min_count=2)
    substrs = {r[0]: r[1] for r in results}
    assert substrs.get("aa") == 3


def test_repeat_three_chars():
    """'aaa' 太短不够（n=3, min=2, max=1），返回空。"""
    results = find_repeat_substrings("aaa", min_length=2, min_count=2)
    assert results == []


def test_repeat_sorted_by_count():
    """结果按出现次数降序。"""
    results = find_repeat_substrings("abababab", min_length=2, min_count=2)
    # 期望 "ab" 4 次排在 "aba" 2 次之前
    assert results[0][0] == "ab"
    assert results[0][1] == 4
    assert results[0][2] == [0, 2, 4, 6]


def test_repeat_min_length_filter():
    """min_length 过滤。"""
    # 'aaa' 中 'a' 出现 3 次，'aa' 出现 2 次，'aaa' 1 次
    results_min1 = find_repeat_substrings("aaaa", min_length=1, min_count=2)
    results_min3 = find_repeat_substrings("aaaa", min_length=3, min_count=2)
    # min=1 应包含 "a" 和 "aa"
    substrs1 = {r[0] for r in results_min1}
    assert "a" in substrs1
    assert "aa" in substrs1
    # min=3 只能有 "aaa" (但 1 次不到 2)，所以空
    assert results_min3 == []


def test_repeat_positions_included():
    """返回结果应包含位置列表。"""
    results = find_repeat_substrings("xyxyxy", min_length=2, min_count=2)
    xy_results = [r for r in results if r[0] == "xy"]
    assert len(xy_results) == 1
    assert xy_results[0][2] == [0, 2, 4]


def test_repeat_max_results():
    """max_results 限制。"""
    results = find_repeat_substrings("ababababab", min_length=2, min_count=2, max_results=3)
    assert len(results) <= 3


def test_repeat_empty_string():
    results = find_repeat_substrings("", min_length=2)
    assert results == []


def test_repeat_too_short():
    results = find_repeat_substrings("a", min_length=2)
    assert results == []


def test_analyze_one():
    r = analyze_one("abcabcabc", min_length=3, min_count=2)
    substrs = {res[0]: res[1] for res in r.substrings}
    assert substrs.get("abc") == 3


def test_analyze_multiple():
    results = analyze(["abcabc", "xyzxyz"], min_length=2, min_count=2)
    assert len(results) == 2
    substrs0 = {r[0]: r[1] for r in results[0].substrings}
    assert substrs0.get("abc") == 2  # 出现 2 次
    substrs1 = {r[0]: r[1] for r in results[1].substrings}
    assert substrs1.get("xyz") == 2
