from analyzer.multi_string import analyze, MultiStringResult


def test_two_strings():
    result = analyze(["abc", "abd"])
    assert result.length_progression is None  # 仅 2 串不计算递进


def test_three_strings_increasing():
    result = analyze(["ab", "abc", "abcd"])
    assert result.length_progression == "递增"


def test_three_strings_decreasing():
    result = analyze(["abcd", "abc", "ab"])
    assert result.length_progression == "递减"


def test_three_strings_irregular():
    result = analyze(["abc", "ab", "abcd"])
    assert result.length_progression == "无规律"


def test_concatenation_possible():
    # "ab" + "cd" = "abcd"
    result = analyze(["ab", "cd"], full_string="abcd")
    assert result.can_concatenate is True


def test_concatenation_not_possible():
    result = analyze(["ab", "cd"], full_string="abce")
    assert result.can_concatenate is False


def test_pairwise_matrix():
    result = analyze(["abc", "abc", "xyz"])
    # (0,1) 公共子串 = 3, (0,2) = 0, (1,2) = 0
    assert result.common_substring_matrix[0][1] == 3
    assert result.common_substring_matrix[0][2] == 0
