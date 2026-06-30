import hashlib
from analyzer.chunking import (
    fixed_chunk,
    sliding_window,
    analyze,
    Chunk,
    ChunkingConfig,
)


def test_fixed_chunk_basic():
    chunks = fixed_chunk("abcdefgh", 2)
    assert len(chunks) == 4
    assert chunks[0].content == "ab"
    assert chunks[1].content == "cd"
    assert chunks[2].content == "ef"
    assert chunks[3].content == "gh"


def test_fixed_chunk_uneven():
    chunks = fixed_chunk("abcde", 2)
    assert len(chunks) == 3
    assert chunks[2].content == "e"


def test_fixed_chunk_sha256():
    chunks = fixed_chunk("abc", 1)
    expected = hashlib.sha256(b"a").hexdigest()
    assert chunks[0].sha256 == expected


def test_fixed_chunk_duplicates():
    chunks = fixed_chunk("aabbcc", 2)
    assert chunks[0].content == "aa"
    assert chunks[1].content == "bb"
    assert chunks[2].content == "cc"
    assert chunks[0].is_duplicate is False
    # 没有重复内容
    assert all(not c.is_duplicate for c in chunks)


def test_sliding_window_basic():
    chunks = sliding_window("abcde", window=2, step=1)
    assert len(chunks) == 4
    assert chunks[0].content == "ab"
    assert chunks[3].content == "de"


def test_sliding_window_step():
    chunks = sliding_window("abcde", window=2, step=2)
    assert len(chunks) == 2
    assert chunks[0].content == "ab"
    assert chunks[1].content == "cd"


def test_hex_mode_chunks_by_byte():
    config = ChunkingConfig(chunk_size=1, is_hex=True)
    result = analyze(["deadbeef"], config)
    # deadbeef 是 4 字节
    assert len(result.chunks[0]) == 4


def test_text_mode_chunks_by_char():
    config = ChunkingConfig(chunk_size=2, is_hex=False)
    result = analyze(["abc"], config)
    assert len(result.chunks[0]) == 2
    assert result.chunks[0][0].content == "ab"
    assert result.chunks[0][1].content == "c"


def test_analyze_with_duplicates():
    config = ChunkingConfig(chunk_size=2, is_hex=False)
    # "aaaa" 有重复的 "aa" 块（chunk 0 和 chunk 1 都是 "aa"）
    result = analyze(["aaaa"], config)
    assert result.chunks[0][0].is_duplicate is True
    assert result.chunks[0][1].is_duplicate is True


def test_empty_string():
    chunks = fixed_chunk("", 2)
    assert chunks == []


def test_hex_preview():
    chunks = fixed_chunk("ab", 1)
    assert chunks[0].hex_preview == "61"  # 'a' 的 ASCII hex
