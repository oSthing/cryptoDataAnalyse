from analyzer.common_substring import (
    longest_common_substring,
    longest_common_subsequence,
    all_common_substrings,
    all_multi_common_substrings,
    common_prefix_length,
    common_suffix_length,
    analyze,
)


def test_lcs_substring_identical():
    substrs = longest_common_substring("hello", "hello")
    assert ("hello", 0, 0) in substrs


def test_lcs_substring_basic():
    substrs = longest_common_substring("abcdef", "xbcdyz")
    assert ("bcd", 1, 1) in substrs


def test_lcs_substring_no_common():
    substrs = longest_common_substring("abc", "xyz")
    assert substrs == []


def test_lcs_substring_multiple():
    substrs = longest_common_substring("ababc", "babca")
    # "babc" 长度 4
    assert all(s[0] == "babc" for s in substrs)


def test_lcs_subsequence_basic():
    length = longest_common_subsequence("abcde", "ace")
    assert length == 3


def test_lcs_subsequence_identical():
    length = longest_common_subsequence("abc", "abc")
    assert length == 3


def test_lcs_subsequence_no_common():
    length = longest_common_subsequence("abc", "xyz")
    assert length == 0


def test_common_prefix():
    assert common_prefix_length("hello", "help") == 3
    assert common_prefix_length("abc", "xyz") == 0
    assert common_prefix_length("", "abc") == 0


def test_common_suffix():
    assert common_suffix_length("testing", "running") == 3
    assert common_suffix_length("abc", "xyz") == 0


def test_analyze_two_strings():
    result = analyze(["abcdef", "xbcdyz"])
    assert ("bcd", 1, 1) in result.pairwise[(0, 1)]
    assert result.common_prefix == 0


def test_analyze_three_strings():
    result = analyze(["abcXYZ", "abc123", "abcDEF"])
    # "abc" 是公共前缀
    assert result.common_prefix == 3
    # 多串公共子串应包含 "abc"
    assert any(sub[0] == "abc" for sub in result.multi)


def test_analyze_single_string():
    result = analyze(["abc"])
    assert result.pairwise == {}
    assert result.common_prefix == 3


def test_all_common_substrings_basic():
    """找出所有公共子串（不只最长）。"""
    subs = all_common_substrings("abcdef", "xbcdyz", min_length=2)
    # 期望包含 bcd, cd? 实际上两串公共子串: bcd(1,1)
    substrs_set = {s[0] for s in subs}
    assert "bcd" in substrs_set


def test_all_common_substrings_sorted_by_length():
    """结果按长度降序。"""
    subs = all_common_substrings("abcabc", "xxabcabcxx", min_length=2)
    # 期望 "abcabc" (长度6) 在最前
    assert subs[0][0] == "abcabc"
    assert subs[0][1] == 0  # s1 起始位置
    assert subs[0][2] == 2  # s2 起始位置


def test_all_common_substrings_min_length():
    """最小长度过滤。"""
    subs_min1 = all_common_substrings("abcdef", "xbcdyz", min_length=1)
    subs_min3 = all_common_substrings("abcdef", "xbcdyz", min_length=3)
    assert all(len(s[0]) >= 1 for s in subs_min1)
    assert all(len(s[0]) >= 3 for s in subs_min3)
    # min=3 时应该少一些
    assert len(subs_min3) < len(subs_min1)


def test_all_common_substrings_user_example():
    """用户实际用例：hex 字符串包含 32 字符公共子串。"""
    s1 = "98fea6b8123d811480a1add915a34d4f"  # 简化版串1
    s2 = "98fea6b8123d811480a1add915a34d4fdbbfd86515a457e1b20bf4751ea00107123123123123"
    subs = all_common_substrings(s1, s2, min_length=8)
    # 期望 s1 整个 32 字符都在公共子串列表最前
    assert subs[0][0] == s1
    assert subs[0][1] == 0
    assert subs[0][2] == 0


def test_all_common_substrings_no_common():
    subs = all_common_substrings("abc", "xyz", min_length=1)
    assert subs == []


def test_all_multi_common_substrings():
    """3 串以上找出所有公共子串。"""
    subs = all_multi_common_substrings(["abcXYZ", "abc123", "abcDEF"], min_length=2)
    substrs_set = {s[0] for s in subs}
    assert "abc" in substrs_set


def test_analyze_includes_all_substrings():
    """analyze 返回值包含 all_pairwise 和 all_multi。"""
    result = analyze(["abcdef", "xbcdyz"], min_length=2)
    assert (0, 1) in result.all_pairwise
    # 最长应排在最前
    assert result.all_pairwise[(0, 1)][0][0] == "bcd"
