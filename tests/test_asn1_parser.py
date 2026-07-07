"""ASN.1 解析器测试。"""
import pytest
from analyzer.asn1_parser import (
    parse_asn1, parse_string, is_likely_asn1,
    format_tree, summarize, _to_bytes
)


# 一些已知测试向量
# 一个真实的小 RSA 公钥 DER（用 pyasn1 工具生成的小 256-bit 测试密钥）
# SubjectPublicKeyInfo 包装的 RSA 公钥
# 结构: SEQUENCE { AlgorithmIdentifier, BIT STRING { SEQUENCE { INTEGER n, INTEGER e } } }
RSA_PUBLIC_KEY_DER = (
    "3038020100300d06092a864886f70d0101010500030900300602010102010500"
    "2030120c303031303030303030303030303030313035303030303030303030"
    "30303530303030303030303030303031303530303030303030303030303030"
    "3030353030"
)


def _make_rsa_test_key():
    """用 pyasn1 生成一个真实的小 RSA 公钥 DER 用于测试。"""
    try:
        from pyasn1.type import univ, namedtype
        from pyasn1.codec.der import encoder
    except ImportError:
        return None
    # AlgorithmIdentifier
    algo = univ.Sequence()
    algo.setComponentByPosition(0, univ.ObjectIdentifier((1, 2, 840, 113549, 1, 1, 1)))
    algo.setComponentByPosition(1, univ.Null())
    # RSA 公钥 SEQUENCE { n, e }
    rsa_pub = univ.Sequence()
    rsa_pub.setComponentByPosition(0, univ.Integer(0xDEADBEEFCAFE1234))
    rsa_pub.setComponentByPosition(1, univ.Integer(65537))
    bit_str = univ.BitString(hexValue=encoder.encode(rsa_pub).hex())
    # SubjectPublicKeyInfo
    spki = univ.Sequence()
    spki.setComponentByPosition(0, algo)
    spki.setComponentByPosition(1, bit_str)
    return encoder.encode(spki).hex().upper()


def test_to_bytes_hex():
    data = _to_bytes("30 22 30 0d 06 09")
    assert data is not None
    assert data[:2] == b'\x30\x22'


def test_to_bytes_with_spaces():
    data = _to_bytes("30:22:30")
    assert data == b'\x30\x22\x30'


def test_is_likely_asn1_rsa_pubkey():
    # 优先使用 pyasn1 生成的真实 RSA 公钥
    real = _make_rsa_test_key()
    if real:
        assert is_likely_asn1(real) is True
    else:
        # fallback：直接用 SEQUENCE 开头的 hex
        assert is_likely_asn1("3003020101") is True


def test_is_likely_asn1_short_string():
    assert is_likely_asn1("hello") is False


def test_is_likely_asn1_empty():
    assert is_likely_asn1("") is False


def test_is_likely_asn1_invalid():
    assert is_likely_asn1("ff") is False  # 0xff 不是合法 ASN.1 tag


def test_parse_simple_sequence():
    # 30 03 02 01 01 = SEQUENCE { INTEGER 1 }
    data = bytes.fromhex("3003020101")
    node = parse_asn1(data)
    assert node.tag_name == "SEQUENCE"
    assert node.constructed is True
    assert len(node.value) == 1
    child = node.value[0]
    assert child.tag_name == "INTEGER"
    assert child.value == "1"


def test_parse_integer():
    # 02 01 0a = INTEGER 10
    data = bytes.fromhex("02010a")
    node = parse_asn1(data)
    assert node.tag_name == "INTEGER"
    assert node.value == "10"


def test_parse_integer_negative():
    # 02 01 ff = INTEGER -1
    data = bytes.fromhex("0201ff")
    node = parse_asn1(data)
    assert node.value == "-1"


def test_parse_oid():
    # 06 09 2a 86 48 86 f7 0d 01 01 01 = OID 1.2.840.113549.1.1.1 (rsaEncryption)
    data = bytes.fromhex("06092a864886f70d010101")
    node = parse_asn1(data)
    assert node.tag_name == "OID"
    assert "1.2.840.113549.1.1.1" in node.value
    assert "rsaEncryption" in node.value


def test_parse_null():
    # 05 00 = NULL
    data = bytes.fromhex("0500")
    node = parse_asn1(data)
    assert node.tag_name == "NULL"
    assert node.value == "NULL"


def test_parse_boolean_true():
    data = bytes.fromhex("0101ff")
    node = parse_asn1(data)
    assert node.value == "TRUE"


def test_parse_boolean_false():
    data = bytes.fromhex("010100")
    node = parse_asn1(data)
    assert node.value == "FALSE"


def test_parse_utf8_string():
    # 0c 05 68 65 6c 6c 6f = UTF8String "hello"
    data = bytes.fromhex("0c0568656c6c6f")
    node = parse_asn1(data)
    assert node.tag_name == "UTF8String"
    assert node.value == "hello"


def test_parse_octet_string():
    # 04 03 01 02 03 = OCTET STRING 0x010203
    data = bytes.fromhex("0403010203")
    node = parse_asn1(data)
    assert node.tag_name == "OCTET STRING"
    assert "010203" in node.value


def test_parse_nested_sequence():
    # SEQUENCE { SEQUENCE { INTEGER 1 }, INTEGER 2 }
    # 30 06 30 03 02 01 01 02 01 02
    data = bytes.fromhex("30063003020101020102")
    node = parse_asn1(data)
    assert len(node.value) == 2
    assert node.value[0].tag_name == "SEQUENCE"
    assert node.value[0].value[0].value == "1"
    assert node.value[1].value == "2"


def test_parse_string_from_hex():
    node = parse_string("3003020101")
    assert node is not None
    assert node.tag_name == "SEQUENCE"


def test_parse_string_from_non_asn1():
    node = parse_string("hello world")
    assert node is None


def test_parse_long_form_length():
    # 30 81 03 02 01 01 = SEQUENCE len=3 (long form, 1 byte)
    data = bytes.fromhex("308103020101")
    node = parse_asn1(data)
    assert node.tag_name == "SEQUENCE"
    assert node.length == 3
    assert len(node.value) == 1


def test_parse_rsa_public_key():
    """解析真实 RSA 公钥 DER。"""
    real = _make_rsa_test_key()
    if not real:
        pytest.skip("pyasn1 not available for RSA key generation")
    node = parse_string(real)
    assert node is not None
    assert node.tag_name == "SEQUENCE"
    assert len(node.value) >= 2
    algo_seq = node.value[0]
    assert algo_seq.tag_name == "SEQUENCE"
    info = summarize(node)
    assert info["oid_count"] >= 1
    assert any("rsaEncryption" in o for o in info["oids"])


def test_format_tree():
    node = parse_string("3003020101")
    lines = format_tree(node)
    assert len(lines) >= 2
    assert any("SEQUENCE" in l for l in lines)
    assert any("INTEGER" in l for l in lines)


def test_summarize():
    node = parse_string("3003020101")
    info = summarize(node)
    assert info["root_tag"] == "SEQUENCE"
    assert info["oid_count"] == 0  # 这个简单例子没有 OID


def test_summarize_with_oid():
    # SEQUENCE { OID }
    data = bytes.fromhex("300b06092a864886f70d010101")
    node = parse_asn1(data)
    info = summarize(node)
    assert info["oid_count"] == 1


def test_parse_context_specific():
    # A0 03 02 01 01 = [0] CONSTRUCTED { INTEGER 1 }
    data = bytes.fromhex("a003020101")
    node = parse_asn1(data)
    assert node.tag_class == "CONTEXT"
    assert node.constructed is True
    assert len(node.value) == 1
    assert node.value[0].value == "1"


def test_parse_x509_serial():
    """简单 X.509 序列号 0x1234。"""
    # INTEGER 0x1234 = 02 02 12 34
    node = parse_string("02021234")
    assert node.value == "4660"  # 0x1234


def test_bit_string_returns_dict():
    """BIT STRING 节点值是 dict（带 unused_bits / bytes / bit_count）。"""
    # 03 04 06 6e 6d 80 = BIT STRING unused=6, bytes="6e 6d 80"
    data = bytes.fromhex("0304066e6d80")
    node = parse_asn1(data)
    assert node.tag_name == "BIT STRING"
    assert isinstance(node.value, dict)
    assert node.value["unused_bits"] == 6
    assert node.value["bytes"] == bytes.fromhex("6e6d80")
    assert node.value["bit_count"] == 18  # 3*8 - 6


def test_bit_string_format_tree_full():
    """format_tree 完整显示 BIT STRING bytes（不截断）。"""
    # 一个长 BIT STRING（128 字节 = 1024 位）
    long_bytes = b"\xab" * 128
    payload = b"\x00" + long_bytes  # unused=0
    # tag=03, length=0x81 0x81 (long form 129 bytes), value=payload
    der = b"\x03\x81\x81" + payload
    hex_input = der.hex()
    node = parse_string(hex_input)
    lines = format_tree(node)
    # 第一行应是 "BIT STRING (1024 bits, 未使用 0 bits, 128 bytes)"
    first = lines[0]
    assert "BIT STRING" in first
    assert "1024 bits" in first
    assert "128 bytes" in first
    # 后续行应有完整内容（折行显示，跨多行）
    joined = "".join(l.strip() for l in lines[1:])
    # 完整内容应是 128 字节 = 256 个 'ab' 字符
    assert joined == "ab" * 128


def test_bit_string_format_tree_multiline():
    """长 BIT STRING 应折行显示，每行 64 hex 字符。"""
    long_bytes = b"\xcd" * 100
    payload = b"\x00" + long_bytes
    der = b"\x03\x81\x65" + payload
    node = parse_asn1(bytes.fromhex(der.hex()))
    lines = format_tree(node)
    # 找所有数据行（包含 cd 的 hex）
    data_lines = [l.strip() for l in lines if l.strip().startswith("cd")]
    # 100 字节 = 200 hex 字符，应分 4 行（64+64+64+8）
    assert len(data_lines) == 4
    # 第一行 64 字符，第二行 64，第三行 64，第四行 8
    assert len(data_lines[0]) == 64
    assert len(data_lines[1]) == 64
    assert len(data_lines[2]) == 64
    assert len(data_lines[3]) == 8