"""导出器：JSON / Markdown 格式。"""
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List


def _to_serializable(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(i) for i in obj]
    return obj


def to_json(data: Dict) -> str:
    serializable = _to_serializable(data)
    return json.dumps(serializable, ensure_ascii=False, indent=2)


def to_markdown(data: Dict) -> str:
    lines = ["# 数据分析报告", ""]
    lines.append(f"**时间**: {data.get('timestamp', '')}")
    lines.append("")

    inputs = data.get('inputs', [])
    basic = data.get('basic_features', [])
    patterns = data.get('patterns', [])

    if not inputs:
        lines.append("（无输入数据）")
        return "\n".join(lines)

    lines.append("## 输入数据")
    lines.append("")
    for i, s in enumerate(inputs):
        preview = s if len(s) <= 100 else s[:100] + "..."
        lines.append(f"{i+1}. `{preview}`")
    lines.append("")

    lines.append("## 基本特征")
    lines.append("")
    lines.append("| # | 长度 | 唯一字符 | 大写 | 小写 | 数字 | 其他 | 可打印 | 含中文 |")
    lines.append("|---|------|----------|------|------|------|------|--------|--------|")
    for i, bf in enumerate(basic):
        bf_dict = asdict(bf) if is_dataclass(bf) else bf
        cc = bf_dict.get('char_classes', {})
        lines.append(
            f"| {i+1} | {bf_dict.get('length', 0)} | {bf_dict.get('unique_chars', 0)} | "
            f"{cc.get('upper', 0)} | {cc.get('lower', 0)} | {cc.get('digit', 0)} | "
            f"{cc.get('other', 0)} | {'是' if bf_dict.get('is_printable') else '否'} | "
            f"{'是' if bf_dict.get('has_chinese') else '否'} |"
        )
    lines.append("")

    lines.append("## 模式识别")
    lines.append("")
    for i, p_list in enumerate(patterns):
        if p_list:
            badges = ", ".join(f"`{p}`" for p in p_list)
            lines.append(f"{i+1}. {badges}")
        else:
            lines.append(f"{i+1}. （无识别模式）")
    lines.append("")

    return "\n".join(lines)