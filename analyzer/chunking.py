"""字符串分块分析：固定长度、滑动窗口、Hex 模式。"""
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Chunk:
    index: int
    content: str
    sha256: str
    hex_preview: str
    is_duplicate: bool


@dataclass
class ChunkingConfig:
    chunk_size: int = 8
    window_size: int = 8
    window_step: int = 1
    is_hex: bool = False
    mode: str = "fixed"  # "fixed" or "sliding"


@dataclass
class ChunkingResult:
    chunks: Dict[int, List[Chunk]] = field(default_factory=dict)
    duplicates: Dict[int, List[int]] = field(default_factory=dict)
    config: Optional[ChunkingConfig] = None


def _make_chunk(index: int, content: str) -> Chunk:
    sha = hashlib.sha256(content.encode('utf-8')).hexdigest()
    # 十六进制预览：取前 16 个字符对应的 hex
    hex_preview = content[:16].encode('utf-8').hex() if content else ""
    return Chunk(
        index=index,
        content=content,
        sha256=sha,
        hex_preview=hex_preview,
        is_duplicate=False,
    )


def _mark_duplicates(chunks: List[Chunk]) -> List[int]:
    """标记重复块，返回重复块的索引列表。"""
    seen = {}
    duplicates = []
    for chunk in chunks:
        if chunk.sha256 in seen:
            chunk.is_duplicate = True
            seen[chunk.sha256].is_duplicate = True
            duplicates.append(chunk.index)
        else:
            seen[chunk.sha256] = chunk
    return duplicates


def fixed_chunk(s: str, size: int) -> List[Chunk]:
    if size <= 0 or not s:
        return []
    chunks = []
    for i in range(0, len(s), size):
        content = s[i:i+size]
        chunks.append(_make_chunk(i // size, content))
    _mark_duplicates(chunks)
    return chunks


def sliding_window(s: str, window: int, step: int) -> List[Chunk]:
    if window <= 0 or step <= 0 or not s:
        return []
    chunks = []
    i = 0
    idx = 0
    while i + window <= len(s):
        content = s[i:i+window]
        chunks.append(_make_chunk(idx, content))
        i += step
        idx += 1
    _mark_duplicates(chunks)
    return chunks


def analyze(strings: List[str], config: ChunkingConfig) -> ChunkingResult:
    result = ChunkingResult(config=config)
    for idx, s in enumerate(strings):
        if config.is_hex:
            # Hex 模式：每两个 hex 字符 = 1 字节，按字节切分（chunk_size 表示字节数）
            # 内容以 hex 字符串形式呈现
            hex_text = s.strip()
            if config.mode == "sliding":
                # 滑窗以 hex 字符为单位，window 为字节数
                chunks = sliding_window(hex_text, config.window_size * 2, config.window_step * 2)
            else:
                chunks = fixed_chunk(hex_text, config.chunk_size * 2)
        else:
            if config.mode == "sliding":
                chunks = sliding_window(s, config.window_size, config.window_step)
            else:
                chunks = fixed_chunk(s, config.chunk_size)
        result.chunks[idx] = chunks
        result.duplicates[idx] = [c.index for c in chunks if c.is_duplicate]
    return result
