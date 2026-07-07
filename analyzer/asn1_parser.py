"""ASN.1 / DER 解析器。

支持：
- 检测输入是否为 ASN.1 DER 编码（hex 或二进制字节）
- 解析 TLV 结构为嵌套树
- 识别常见 OID（RSA、ECC、哈希算法、X.509 字段等）
- 识别常见类型（INTEGER, BIT STRING, OCTET STRING, NULL, SEQUENCE, OID, UTF8String 等）

ASN.1 标签:
  0x01 BOOLEAN
  0x02 INTEGER
  0x03 BIT STRING
  0x04 OCTET STRING
  0x05 NULL
  0x06 OBJECT IDENTIFIER
  0x0A ENUMERATED
  0x0C UTF8String
  0x13 PrintableString
  0x14 T61String
  0x16 IA5String
  0x17 UTCTime
  0x18 GeneralizedTime
  0x30 SEQUENCE (constructed)
  0x31 SET (constructed)
  0xA0 context-specific [0] (constructed)
  ...
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


# 通用标签名
UNIVERSAL_TAG_NAMES = {
    # 低 5 位 tag_number -> 名称
    0x01: "BOOLEAN",
    0x02: "INTEGER",
    0x03: "BIT STRING",
    0x04: "OCTET STRING",
    0x05: "NULL",
    0x06: "OID",
    0x0A: "ENUMERATED",
    0x0C: "UTF8String",
    0x10: "SEQUENCE",      # 0x30 & 0x1F = 0x10
    0x11: "SET",           # 0x31 & 0x1F = 0x11
    0x13: "PrintableString",
    0x14: "T61String",
    0x16: "IA5String",
    0x17: "UTCTime",
    0x18: "GeneralizedTime",
}

# 常见 OID -> 名称
KNOWN_OIDS = {
    "1.2.840.113549.1.1.1": "rsaEncryption",
    "1.2.840.113549.1.1.5": "sha1WithRSAEncryption",
    "1.2.840.113549.1.1.11": "sha256WithRSAEncryption",
    "1.2.840.113549.1.1.12": "sha384WithRSAEncryption",
    "1.2.840.113549.1.1.13": "sha512WithRSAEncryption",
    "1.2.840.113549.1.1.10": "RSASSA-PSS",
    "1.2.840.10045.2.1": "ecPublicKey",
    "1.2.840.10045.4.3.2": "ecdsaWithSHA256",
    "1.2.840.10045.4.3.3": "ecdsaWithSHA384",
    "1.2.840.10045.4.3.4": "ecdsaWithSHA512",
    "2.16.840.1.101.3.4.2.1": "sha256",
    "2.16.840.1.101.3.4.2.2": "sha384",
    "2.16.840.1.101.3.4.2.3": "sha512",
    "1.3.14.3.2.26": "sha1",
    "2.5.4.3": "commonName",
    "2.5.4.6": "countryName",
    "2.5.4.7": "localityName",
    "2.5.4.8": "stateOrProvinceName",
    "2.5.4.10": "organizationName",
    "2.5.4.11": "organizationalUnitName",
    "2.5.4.5": "serialNumber",
    "2.5.4.9": "streetAddress",
    "2.5.4.17": "postalCode",
    "2.5.4.15": "businessCategory",
    "1.2.840.113549.1.9.1": "emailAddress",
    "1.2.840.113549.1.9.2": "unstructuredName",
    "1.2.840.113549.1.9.3": "contentType",
    "1.2.840.113549.1.9.4": "messageDigest",
    "1.2.840.113549.1.9.5": "signingTime",
    "1.2.840.113549.1.9.7": "challengePassword",
    "1.2.840.113549.1.9.13": "signingDescription",
    "1.2.840.113549.1.9.14": "extensionRequest",
    "1.2.840.113549.1.9.15": "SMIMECapabilities",
    "1.2.840.113549.1.9.16.2.12": "signingCertificateV2",
    "1.2.840.113549.1.9.23": "signingCertificate",
    "1.2.840.113549.1.7.1": "data",
    "1.2.840.113549.1.7.2": "signedData",
    "1.2.840.113549.1.7.3": "envelopedData",
    "1.2.840.113549.1.7.4": "signedAndEnvelopedData",
    "1.2.840.113549.1.7.5": "digestedData",
    "1.2.840.113549.1.7.6": "encryptedData",
    "1.2.840.113549.1.12.10.1.3": "keyTransport",
    "1.2.840.113549.1.5.13": "pbeWithSHA1AndDESede",
    "1.2.840.113549.2.7": "HMAC-SHA1",
    "1.2.840.113549.2.9": "HMAC-SHA256",
    "1.2.840.113549.3.7": "3DES",
    "2.5.8.1.1": "RSA (deprecated)",
    "0.9.2342.19200300.100.1.25": "domainComponent",
    "1.2.840.113533.7.65.0": "entrustVersion",
    "1.2.840.10040.4.1": "dsa",
    "1.2.840.10040.4.3": "dsaWithSHA1",
}


@dataclass
class ASN1Node:
    """ASN.1 解析节点。"""
    tag_class: str          # "UNIVERSAL" / "CONTEXT" / "APPLICATION" / "PRIVATE"
    constructed: bool
    tag_number: int
    tag_name: str
    length: int
    value: Any              # 解析后的值或子节点列表
    raw_value: bytes        # 原始字节
    offset: int = 0         # 在原始数据中的起始偏移


def _decode_length(data: bytes, offset: int) -> Tuple[int, int]:
    """解码 ASN.1 长度字段，返回 (length, new_offset)."""
    if offset >= len(data):
        raise ValueError("Length field missing")
    first = data[offset]
    offset += 1
    if first < 0x80:
        return first, offset
    num_bytes = first & 0x7F
    if num_bytes == 0:
        # 不定长（仅用于 constructed）
        return -1, offset
    if offset + num_bytes > len(data):
        raise ValueError("Length field truncated")
    length = int.from_bytes(data[offset:offset + num_bytes], 'big')
    return length, offset + num_bytes


def _decode_tag(data: bytes, offset: int) -> Tuple[int, bool, str, int]:
    """解码 ASN.1 标签，返回 (tag_number, constructed, tag_class, new_offset)."""
    if offset >= len(data):
        raise ValueError("Tag field missing")
    first = data[offset]
    offset += 1
    tag_class_bits = (first >> 6) & 0x03
    constructed = bool((first >> 5) & 0x01)
    classes = {0: "UNIVERSAL", 1: "APPLICATION", 2: "CONTEXT", 3: "PRIVATE"}
    tag_class = classes[tag_class_bits]

    low5 = first & 0x1F
    if low5 < 0x1F:
        return low5, constructed, tag_class, offset

    # 长标签
    tag_number = 0
    while True:
        if offset >= len(data):
            raise ValueError("Long tag truncated")
        b = data[offset]
        offset += 1
        tag_number = (tag_number << 7) | (b & 0x7F)
        if not (b & 0x80):
            break
    return tag_number, constructed, tag_class, offset


def _tag_name(tag_class: str, tag_number: int) -> str:
    if tag_class == "UNIVERSAL" and tag_number in UNIVERSAL_TAG_NAMES:
        return UNIVERSAL_TAG_NAMES[tag_number]
    if tag_class == "CONTEXT":
        return f"[{tag_number}] CONTEXT"
    if tag_class == "APPLICATION":
        return f"[{tag_number}] APPLICATION"
    return f"[{tag_number}] PRIVATE"


def _decode_oid(data: bytes) -> str:
    """解码 OID 字节为点分十进制。"""
    if not data:
        return ""
    components = []
    first = data[0]
    components.append(first // 40)
    components.append(first % 40)
    value = 0
    for b in data[1:]:
        value = (value << 7) | (b & 0x7F)
        if not (b & 0x80):
            components.append(value)
            value = 0
    return ".".join(str(c) for c in components)


def _format_value(node: ASN1Node) -> Any:
    """将节点 value 转为可读字符串。"""
    if node.constructed:
        return node.value  # List[ASN1Node]
    raw = node.raw_value
    if node.tag_class == "UNIVERSAL":
        if node.tag_number == 0x02:  # INTEGER
            if not raw:
                return "0"
            n = int.from_bytes(raw, 'big', signed=True)
            return str(n)
        if node.tag_number == 0x06:  # OID
            oid_str = _decode_oid(raw)
            name = KNOWN_OIDS.get(oid_str, "")
            return f"{oid_str} ({name})" if name else oid_str
        if node.tag_number == 0x05:  # NULL
            return "NULL"
        if node.tag_number == 0x01:  # BOOLEAN
            return "TRUE" if raw and raw[-1] else "FALSE"
        if node.tag_number == 0x03:  # BIT STRING
            # 首字节是未使用位数
            if not raw:
                return "(empty)"
            unused = raw[0]
            bits = raw[1:]
            return f"bits({len(bits) * 8 - unused} used): {bits.hex()}"
        if node.tag_number == 0x0C:  # UTF8String
            try:
                return raw.decode('utf-8', errors='replace')
            except Exception:
                return raw.hex()
        if node.tag_number in (0x13, 0x16):  # PrintableString / IA5String
            try:
                return raw.decode('ascii', errors='replace')
            except Exception:
                return raw.hex()
        if node.tag_number == 0x17:  # UTCTime
            try:
                return raw.decode('ascii', errors='replace')
            except Exception:
                return raw.hex()
        if node.tag_number == 0x18:  # GeneralizedTime
            try:
                return raw.decode('ascii', errors='replace')
            except Exception:
                return raw.hex()
    # 默认 hex
    return raw.hex()


def parse_asn1(data: bytes, max_depth: int = 20) -> ASN1Node:
    """递归解析 ASN.1 DER 字节流。"""
    if not data:
        raise ValueError("Empty data")
    node, _ = _parse_one(data, 0, max_depth)
    return node


def _parse_one(data: bytes, offset: int, max_depth: int) -> Tuple[ASN1Node, int]:
    tag_number, constructed, tag_class, offset = _decode_tag(data, offset)
    length, offset = _decode_length(data, offset)

    if length == -1:
        # 不定长：扫描到 EOC (00 00)
        value_start = offset
        end = data.find(b'\x00\x00', value_start)
        if end == -1:
            raise ValueError("Indefinite length without EOC")
        raw_value = data[value_start:end]
        new_offset = end + 2
    elif offset + length > len(data):
        raise ValueError("Length exceeds available data")
    else:
        raw_value = data[offset:offset + length]
        new_offset = offset + length

    name = _tag_name(tag_class, tag_number)
    node = ASN1Node(
        tag_class=tag_class,
        constructed=constructed,
        tag_number=tag_number,
        tag_name=name,
        length=length if length >= 0 else len(raw_value),
        value=None,
        raw_value=raw_value,
        offset=offset - 2 if length >= 0 else value_start - 2,
    )

    if constructed and max_depth > 0:
        children: List[ASN1Node] = []
        child_offset = offset
        if length == -1:
            end = offset + len(raw_value)
        else:
            end = offset + length
        try:
            while child_offset < end:
                child, child_offset = _parse_one(data, child_offset, max_depth - 1)
                children.append(child)
        except ValueError:
            # 部分解析失败
            pass
        node.value = children
    else:
        node.value = _format_value(node)

    return node, new_offset


def is_likely_asn1(s: str) -> bool:
    """启发式判断字符串是否为 ASN.1 DER 编码（hex 或 raw bytes 形式）。

    简单启发式：开头是 ASN.1 tag (0x30 SEQUENCE / 0x02 INTEGER / 0x06 OID 等)
    且能成功解析至少一层 TLV。
    """
    if not s:
        return False
    data = _to_bytes(s)
    if data is None or len(data) < 2:
        return False
    first = data[0]
    # 常见 ASN.1 tag
    valid_first = {0x02, 0x03, 0x04, 0x05, 0x06, 0x0A, 0x0C, 0x13,
                   0x14, 0x16, 0x17, 0x18, 0x30, 0x31, 0xA0, 0xA1, 0xA3,
                   0xA4, 0x60, 0x61, 0x7F}
    if first not in valid_first:
        return False
    # 尝试解析
    try:
        parse_asn1(data, max_depth=2)
        return True
    except Exception:
        return False


def _to_bytes(s: str) -> Optional[bytes]:
    """尝试把字符串转为 bytes。hex 字符串或纯 ASCII bytes 都尝试。"""
    s = s.strip()
    if not s:
        return None
    # 优先尝试 hex
    compact = s.replace(" ", "").replace(":", "").replace("\n", "").replace("\r", "")
    if len(compact) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in compact):
        try:
            return bytes.fromhex(compact)
        except ValueError:
            pass
    # 否则按 latin-1 直接编码
    try:
        return s.encode('latin-1')
    except Exception:
        return None


def parse_string(s: str, max_depth: int = 20) -> Optional[ASN1Node]:
    """从字符串解析 ASN.1。返回 None 表示不是 ASN.1。"""
    data = _to_bytes(s)
    if data is None:
        return None
    try:
        return parse_asn1(data, max_depth=max_depth)
    except Exception:
        return None


def format_tree(node: ASN1Node, indent: int = 0, max_lines: int = 200) -> List[str]:
    """把 ASN1Node 渲染为可读字符串树。"""
    lines: List[str] = []
    if len(lines) >= max_lines:
        lines.append("  " * indent + "... (truncated)")
        return lines

    prefix = "  " * indent
    if node.constructed:
        header = f"{prefix}{node.tag_name} ({node.length} bytes)"
        lines.append(header)
        if isinstance(node.value, list):
            for child in node.value:
                lines.extend(format_tree(child, indent + 1, max_lines))
                if len(lines) >= max_lines:
                    break
    else:
        # 原子节点
        if isinstance(node.value, str):
            val_str = node.value
            if len(val_str) > 80:
                val_str = val_str[:77] + "..."
            lines.append(f"{prefix}{node.tag_name} = {val_str}")
        else:
            lines.append(f"{prefix}{node.tag_name} = (binary {node.length} bytes)")

    return lines


def summarize(node: ASN1Node) -> Dict[str, Any]:
    """提取 ASN.1 结构的摘要信息。"""
    info = {
        "root_tag": node.tag_name,
        "root_size": node.length,
        "oid_count": 0,
        "oids": [],
        "structure": [],
    }

    def walk(n: ASN1Node, depth: int = 0):
        if depth > 10:
            return
        if n.tag_class == "UNIVERSAL" and n.tag_number == 0x06:
            # OID
            info["oid_count"] += 1
            if isinstance(n.value, str):
                info["oids"].append(n.value)
        if n.constructed and isinstance(n.value, list):
            tag_summary = f"{n.tag_name}({len(n.value)})"
            if tag_summary not in info["structure"]:
                info["structure"].append(tag_summary)
            for child in n.value:
                walk(child, depth + 1)

    walk(node)
    return info