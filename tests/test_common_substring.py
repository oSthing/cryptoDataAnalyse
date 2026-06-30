from analyzer.common_substring import (
    longest_common_substring,
    longest_common_subsequence,
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
