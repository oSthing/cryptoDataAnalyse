from analyzer.diff import (
    hamming_distance,
    levenshtein_distance,
    jaccard_similarity,
    analyze,
    DiffResult,
)


def test_hamming_identical():
    assert hamming_distance("hello", "hello") == 0


def test_hamming_basic():
    assert hamming_distance("karolin", "kathrin") == 3


def test_hamming_unequal_length():
    assert hamming_distance("abc", "abcd") == -1


def test_levenshtein_identical():
    assert levenshtein_distance("abc", "abc") == 0


def test_levenshtein_basic():
    assert levenshtein_distance("kitten", "sitting") == 3


def test_levenshtein_empty():
    assert levenshtein_distance("", "abc") == 3
    assert levenshtein_distance("abc", "") == 3


def test_levenshtein_completely_different():
    assert levenshtein_distance("abc", "xyz") == 3


def test_jaccard_identical():
    assert jaccard_similarity("abc", "abc", n=2) == 1.0


def test_jaccard_no_overlap():
    sim = jaccard_similarity("abc", "xyz", n=2)
    assert sim == 0.0


def test_jaccard_partial():
    sim = jaccard_similarity("abcde", "abcxy", n=2)
    # "ab", "bc", "cd", "de" vs "ab", "bc", "cx", "xy"
    # 交集: {"ab", "bc"} = 2
    # 并集: {"ab", "bc", "cd", "de", "cx", "xy"} = 6
    assert abs(sim - 2/6) < 0.01


def test_analyze_two_strings():
    result = analyze(["hello", "world"])
    assert result.hamming[(0, 1)] == 4
    assert result.levenshtein[(0, 1)] == 4
    assert 0.0 <= result.jaccard[(0, 1)] <= 1.0


def test_analyze_three_strings():
    result = analyze(["abc", "abd", "abe"])
    assert (0, 1) in result.hamming
    assert (0, 2) in result.hamming
    assert (1, 2) in result.hamming


def test_analyze_single_string():
    result = analyze(["abc"])
    assert result.hamming == {}