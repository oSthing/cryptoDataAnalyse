"""模式识别：编码格式、哈希族、密码学专项、对称密码特征。"""
import re
import math
import json
import base64
from collections import Counter
from typing import List


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counter = Counter(s)
    total = len(s)
    return -sum((c / total) * math.log2(c / total) for c in counter.values())


def _is_hex(s: str) -> bool:
    return bool(re.fullmatch(r'[0-9a-fA-F]+', s)) and len(s) % 2 == 0 and len(s) > 0


def _is_base64(s: str) -> bool:
    return bool(re.fullmatch(r'[A-Za-z0-9+/]+={0,2}', s)) and len(s) % 4 == 0 and len(s) >= 4


def _is_base32(s: str) -> bool:
    return bool(re.fullmatch(r'[A-Z2-7]+=*', s)) and len(s) >= 8


def _is_base58(s: str) -> bool:
    return bool(re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]+', s)) and len(s) >= 26


def _is_uuid(s: str) -> bool:
    pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
    return bool(re.fullmatch(pattern, s))


def _detect_hash(s: str) -> List[str]:
    if not re.fullmatch(r'[0-9a-fA-F]+', s):
        return []
    hex_len = len(s)
    if hex_len == 32:
        return ["MD5", "NTLM"]
    if hex_len == 40:
        return ["SHA-1"]
    if hex_len == 56:
        return ["SHA-224"]
    if hex_len == 64:
        return ["SHA-256"]
    if hex_len == 96:
        return ["SHA-384"]
    if hex_len == 128:
        return ["SHA-512"]
    return []


def _is_unix_seconds(s: str) -> bool:
    return bool(re.fullmatch(r'\d{10}', s)) and 100000000 <= int(s) <= 4102444800


def _is_unix_millis(s: str) -> bool:
    return bool(re.fullmatch(r'\d{13}', s)) and 100000000000 <= int(s) <= 4102444800000


def _is_windows_filetime(s: str) -> bool:
    return bool(re.fullmatch(r'\d{18}', s))


def _is_iso8601(s: str) -> bool:
    return bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?', s))


def _is_ipv4(s: str) -> bool:
    parts = s.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def _is_ipv6(s: str) -> bool:
    return ':' in s and bool(re.fullmatch(r'[0-9a-fA-F:]+', s)) and len(s) >= 3


def _is_mac(s: str) -> bool:
    return bool(re.fullmatch(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', s))


def _is_email(s: str) -> bool:
    return bool(re.fullmatch(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', s))


def _is_url(s: str) -> bool:
    return bool(re.match(r'^https?://', s))


def _is_json(s: str) -> bool:
    s = s.strip()
    if not (s.startswith('{') and s.endswith('}')) and not (s.startswith('[') and s.endswith(']')):
        return False
    try:
        json.loads(s)
        return True
    except (ValueError, json.JSONDecodeError):
        return False


def _is_xml(s: str) -> bool:
    return bool(re.match(r'<\?xml|<[a-zA-Z][^>]*>', s))


def _is_jwt(s: str) -> bool:
    parts = s.split('.')
    if len(parts) != 3:
        return False
    try:
        for p in parts:
            padded = p + '=' * (-len(p) % 4)
            base64.urlsafe_b64decode(padded)
        return True
    except Exception:
        return False


def _is_asn1_der(s: str) -> bool:
    return bool(re.fullmatch(r'30 82[0-9a-fA-F ]+', s)) or s.startswith('3082')


def _detect_pem(s: str) -> List[str]:
    results = []
    if '-----BEGIN PUBLIC KEY-----' in s:
        results.append("RSA公钥PEM")
    if '-----BEGIN RSA PRIVATE KEY-----' in s:
        results.append("RSA私钥PEM")
    if '-----BEGIN EC PRIVATE KEY-----' in s:
        results.append("EC私钥PEM")
    if '-----BEGIN PRIVATE KEY-----' in s:
        results.append("PKCS#8私钥PEM")
    if re.search(r'-----BEGIN PGP [A-Z ]+-----', s):
        results.append("PGP块")
    if '-----BEGIN CERTIFICATE-----' in s:
        results.append("X.509证书")
    return results


def _is_ssh_public_key(s: str) -> bool:
    return bool(re.match(r'^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp256|ssh-dss) ', s))


def _is_ethereum(s: str) -> bool:
    return bool(re.fullmatch(r'0x[0-9a-fA-F]{40}', s))


def _is_bitcoin(s: str) -> bool:
    return bool(re.fullmatch(r'[13][1-9A-HJ-NP-Za-km-z]{25,34}', s))


def _is_monero(s: str) -> bool:
    return bool(re.fullmatch(r'4[0-9AB][0-9a-zA-Z]{93}', s))


def _is_ipfs_cid(s: str) -> bool:
    return (s.startswith('Qm') and len(s) == 46 and _is_base58(s)) or s.startswith('bafy')


def _is_aes_key_candidate(s: str) -> bool:
    if not _is_hex(s):
        return False
    return len(s) in (32, 48, 64)  # AES-128/192/256


def _is_des_key_candidate(s: str) -> bool:
    return _is_hex(s) and len(s) == 16


def _is_pkcs7_padded(s: str) -> bool:
    """检测 PKCS#7 填充：hex 串，末 N 字节 = N（N<=16）。"""
    if not _is_hex(s) or len(s) < 2 or len(s) % 2 != 0:
        return False
    try:
        last_byte = int(s[-2:], 16)
        if last_byte == 0 or last_byte > 16:
            return False
        padded = bytes.fromhex(s)
        if len(padded) < last_byte:
            return False
        return all(b == last_byte for b in padded[-last_byte:])
    except ValueError:
        return False


def _is_ecb_mode_hint(s: str) -> bool:
    """检测 ECB 模式特征：hex 串可被 16 整除，存在重复 16 字节块。"""
    if not _is_hex(s) or len(s) < 64 or len(s) % 32 != 0:
        return False
    data = bytes.fromhex(s)
    blocks = [data[i:i+16] for i in range(0, len(data), 16)]
    return len(blocks) != len(set(blocks))


def _is_cbc_iv_candidate(s: str) -> bool:
    """检测 CBC IV 候选：16 字节 hex。"""
    return _is_hex(s) and len(s) == 32


def detect_one(s: str) -> List[str]:
    if not s:
        return []

    patterns = []

    # 编码类
    if _is_hex(s):
        patterns.append("Hex")
    if _is_base64(s):
        patterns.append("Base64")
    if _is_base32(s):
        patterns.append("Base32")
    if _is_base58(s):
        patterns.append("Base58")

    # UUID
    if _is_uuid(s):
        patterns.append("UUID")

    # 哈希类
    patterns.extend(_detect_hash(s))

    # 密码学格式
    if s.startswith('$2a$') or s.startswith('$2b$') or s.startswith('$2y$'):
        patterns.append("bcrypt")
    if s.startswith('$argon2i$') or s.startswith('$argon2id$') or s.startswith('$argon2d$'):
        patterns.append("Argon2")

    # 时间戳
    if _is_unix_seconds(s):
        patterns.append("Unix时间戳(秒)")
    elif _is_unix_millis(s):
        patterns.append("Unix时间戳(毫秒)")
    if _is_windows_filetime(s):
        patterns.append("Windows FILETIME")
    if _is_iso8601(s):
        patterns.append("ISO 8601")

    # 网络地址
    if _is_ipv4(s):
        patterns.append("IPv4")
    if _is_ipv6(s):
        patterns.append("IPv6")
    if _is_mac(s):
        patterns.append("MAC")

    # 邮箱和 URL
    if _is_email(s):
        patterns.append("邮箱")
    if _is_url(s):
        patterns.append("URL")

    # 结构化
    if _is_json(s):
        patterns.append("JSON")
    if _is_xml(s):
        patterns.append("XML")
    if _is_jwt(s):
        patterns.append("JWT")
    if _is_asn1_der(s):
        patterns.append("ASN.1 DER")

    # 密码学专项
    patterns.extend(_detect_pem(s))
    if _is_ssh_public_key(s):
        patterns.append("SSH公钥")
    if _is_ethereum(s):
        patterns.append("Ethereum地址")
    if _is_bitcoin(s):
        patterns.append("Bitcoin地址")
    if _is_monero(s):
        patterns.append("Monero地址")
    if _is_ipfs_cid(s):
        patterns.append("IPFS CID")

    # 对称/分组密码学特征
    if _is_ecb_mode_hint(s):
        patterns.append("ECB模式提示")
    if _is_cbc_iv_candidate(s) and not _is_aes_key_candidate(s):
        patterns.append("CBC IV候选")
    if _is_aes_key_candidate(s):
        patterns.append("AES密钥候选")
    if _is_des_key_candidate(s):
        patterns.append("DES密钥候选")
    if _is_pkcs7_padded(s):
        patterns.append("PKCS#7填充")

    # 熵值提示
    entropy = shannon_entropy(s)
    if entropy >= 4.5:
        patterns.append("高熵(像随机数/密钥/加密输出)")
    elif entropy <= 2.5 and len(s) >= 8:
        patterns.append("低熵(含重复模式)")

    # 字符类
    if s.isdigit():
        patterns.append("全数字")
    if s.isalpha():
        patterns.append("全字母")
    if s.isupper():
        patterns.append("全大写")
    if s.islower():
        patterns.append("全小写")
    if s.isprintable() and all(ord(c) < 128 for c in s):
        patterns.append("可打印ASCII")
    if any('一' <= c <= '鿿' for c in s):
        patterns.append("含中文")

    # 去重保持顺序
    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def detect_all(strings: List[str]) -> List[List[str]]:
    return [detect_one(s) for s in strings]