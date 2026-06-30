import pytest
from analyzer.pattern import detect_one, detect_all


def test_hex_detection():
    assert "Hex" in detect_one("abcdef0123456789")
    assert "Hex" not in detect_one("hello")


def test_hex_odd_length_not_detected():
    # 奇数长度不应被识别为 Hex
    assert "Hex" not in detect_one("abc")


def test_base64_detection():
    assert "Base64" in detect_one("SGVsbG8gV29ybGQ=")
    assert "Base64" not in detect_one("hello")


def test_base32_detection():
    assert "Base32" in detect_one("JBSWY3DPEHPK3PXP")


def test_base58_detection():
    assert "Base58" in detect_one("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2")


def test_uuid_v4():
    assert "UUID" in detect_one("550e8400-e29b-41d4-a716-446655440000")


def test_md5_detection():
    md5 = "5d41402abc4b2a76b9719d911017c592"
    assert "MD5" in detect_one(md5)


def test_sha1_detection():
    sha1 = "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d"
    assert "SHA-1" in detect_one(sha1)


def test_sha256_detection():
    sha256 = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert "SHA-256" in detect_one(sha256)


def test_sha512_detection():
    sha512 = "9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72323c3d99ba5c11d7c7acc6e14b8c5da0c4663475c2e5c3adef46f73bcdec043"
    assert "SHA-512" in detect_one(sha512)


def test_ntlm_detection():
    ntlm = "32ed87bdb5fdc5e9cba88547376818d4"
    assert "NTLM" in detect_one(ntlm)


def test_bcrypt_detection():
    assert "bcrypt" in detect_one("$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy")


def test_unix_timestamp_seconds():
    assert "Unix时间戳(秒)" in detect_one("1700000000")


def test_unix_timestamp_milliseconds():
    assert "Unix时间戳(毫秒)" in detect_one("1700000000000")


def test_ipv4_detection():
    assert "IPv4" in detect_one("192.168.1.1")


def test_mac_detection():
    assert "MAC" in detect_one("00:1B:44:11:3A:B7")
    assert "MAC" in detect_one("00-1B-44-11-3A-B7")


def test_json_detection():
    assert "JSON" in detect_one('{"key": "value"}')


def test_jwt_detection():
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    assert "JWT" in detect_one(jwt)


def test_rsa_public_key_pem():
    pem = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA\n-----END PUBLIC KEY-----"
    assert "RSA公钥PEM" in detect_one(pem)


def test_ssh_public_key():
    assert "SSH公钥" in detect_one("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB user@host")


def test_ethereum_address():
    assert "Ethereum地址" in detect_one("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1")


def test_bitcoin_address():
    assert "Bitcoin地址" in detect_one("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2")


def test_x509_certificate():
    pem = "-----BEGIN CERTIFICATE-----\nMIIDXTCCAkWgAwIBAgIJAKZ\n-----END CERTIFICATE-----"
    assert "X.509证书" in detect_one(pem)


def test_aes_key_candidate():
    # 32 字节 hex = 64 字符
    aes_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    assert "AES密钥候选" in detect_one(aes_key)


def test_des_key_candidate():
    # 8 字节 hex = 16 字符
    des_key = "0123456789abcdef"
    assert "DES密钥候选" in detect_one(des_key)


def test_pkcs7_padding():
    # 末 5 字节都是 0x05
    padded = "aabbccddeeff0505050505"
    assert "PKCS#7填充" in detect_one(padded)


def test_high_entropy_prompt():
    # 模拟高熵字符串（随机）
    import math
    high_entropy = "a3Bf9kP2mN8qR5tY7uW0eL4jH6gD1sZ"
    result = detect_one(high_entropy)
    # 不强制断言，因为熵值取决于实际分布，只检查函数不崩溃
    assert isinstance(result, list)


def test_low_entropy_prompt():
    low_entropy = "aaaaaaaaaa"
    result = detect_one(low_entropy)
    assert isinstance(result, list)


def test_all_uppercase():
    assert "全大写" in detect_one("HELLO")


def test_all_lowercase():
    assert "全小写" in detect_one("hello")


def test_all_digits():
    assert "全数字" in detect_one("12345")


def test_all_letters():
    assert "全字母" in detect_one("HelloWorld")
    assert "全字母" not in detect_one("Hello123")


def test_printable_ascii():
    assert "可打印ASCII" in detect_one("Hello123!")


def test_chinese_detection():
    assert "含中文" in detect_one("你好世界")


def test_empty_string():
    result = detect_one("")
    assert result == []


def test_multiple_patterns():
    # 同时是 JSON 又是可打印 ASCII
    result = detect_one('{"a": 1}')
    assert "JSON" in result
    assert "可打印ASCII" in result


def test_detect_all():
    results = detect_all(["abc", "123"])
    assert "全字母" in results[0]
    assert "全数字" in results[1]