from analyzer.periodicity import detect_period, analyze


def test_detect_period_basic():
    period = detect_period("abcabcabc")
    assert period == 3


def test_detect_period_no_period():
    period = detect_period("abcdef")
    assert period is None


def test_detect_period_single_char():
    period = detect_period("aaaaaaaa")
    assert period == 1


def test_detect_period_short():
    period = detect_period("ab")
    assert period is None


def test_detect_period_complex():
    period = detect_period("abababab")
    assert period == 2


def test_analyze():
    result = analyze(["abcabc", "hello"])
    assert result[0].min_period == 3
    assert result[0].pattern == "abc"
    assert result[1].min_period is None
