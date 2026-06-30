"""比特层分析测试。"""
from analyzer.bit_analysis import (
    string_to_bits,
    nist_monobit_test,
    nist_runs_test,
    analyze,
)


def test_string_to_bits_basic():
    bits = string_to_bits("A")  # 0x41 = 01000001
    assert bits == "01000001"


def test_string_to_bits_empty():
    assert string_to_bits("") == ""


def test_nist_monobit_pass():
    # 交替位串
    bits = "01" * 100
    assert nist_monobit_test(bits) is True


def test_nist_monobit_fail():
    # 全 0
    bits = "0" * 200
    assert nist_monobit_test(bits) is False


def test_nist_runs_pass():
    # 伪随机分布：16 位模式重复 50 次，共 800 位
    bits = "0011110110100001" * 50
    assert nist_runs_test(bits) is True


def test_nist_runs_fail():
    # 太少游程
    bits = "0" * 200
    assert nist_runs_test(bits) is False


def test_analyze_basic():
    result = analyze(["hello"])
    assert len(result) == 1
    assert result[0].zero_ratio + result[0].one_ratio == 1.0


def test_analyze_short_string():
    # 短串不跑 NIST 测试
    result = analyze(["ab"])
    assert result[0].nist_monobit_pass is None
    assert result[0].nist_runs_pass is None
