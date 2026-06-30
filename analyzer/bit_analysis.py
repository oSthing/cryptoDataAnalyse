"""比特层分析：将字符串视为字节序列，分析比特分布和 NIST 随机性测试。"""
import math
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BitResult:
    bit_count: int
    zero_ratio: float
    one_ratio: float
    nist_monobit_pass: Optional[bool]
    nist_runs_pass: Optional[bool]


def string_to_bits(s: str) -> str:
    return ''.join(format(b, '08b') for b in s.encode('utf-8'))


def nist_monobit_test(bits: str) -> Optional[bool]:
    """NIST 单比特频数测试：通过当 0/1 数量接近（5000 样本时阈值 ~2.575）。"""
    n = len(bits)
    if n < 100:
        return None  # 样本太少
    ones = bits.count('1')
    zeros = n - ones
    s_obs = abs(ones - zeros) / math.sqrt(n)
    # 阈值 1.96 对应 95% 置信度
    return s_obs < 1.96


def nist_runs_test(bits: str) -> Optional[bool]:
    """NIST 游程测试：通过当游程数接近期望值。"""
    n = len(bits)
    if n < 100:
        return None
    pi = bits.count('1') / n
    if abs(pi - 0.5) >= 2 / math.sqrt(n):
        return False
    # 计算游程数
    runs = 1
    for i in range(1, n):
        if bits[i] != bits[i-1]:
            runs += 1
    expected_runs = 1 + 2 * n * pi * (1 - pi)
    # NIST SP 800-22 游程测试标准方差
    variance = 2 * n * pi * (1 - pi) * (1 - 2 * pi * (1 - pi))
    if variance <= 0:
        return True
    p_value = abs(runs - expected_runs) / math.sqrt(variance)
    return p_value < 1.96


def analyze_one(s: str) -> BitResult:
    bits = string_to_bits(s)
    n = len(bits)
    if n == 0:
        return BitResult(0, 0.0, 0.0, None, None)
    zeros = bits.count('0')
    ones = n - zeros
    return BitResult(
        bit_count=n,
        zero_ratio=zeros / n,
        one_ratio=ones / n,
        nist_monobit_pass=nist_monobit_test(bits),
        nist_runs_pass=nist_runs_test(bits),
    )


def analyze(strings: List[str]) -> List[BitResult]:
    return [analyze_one(s) for s in strings]
