#!/usr/bin/env python3
"""将未知编码文本转换为 UTF-8 BOM + CRLF。"""

from __future__ import annotations

import argparse
import codecs
import json
from pathlib import Path
from typing import Any

import chardet


DEFAULT_MIN_CONFIDENCE = 0.80


def normalize_crlf(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\r\n")


def detect_encoding(raw: bytes, min_confidence: float) -> tuple[str, float, dict[str, Any]]:
    result = chardet.detect(raw)
    detected = result.get("encoding")
    confidence = float(result.get("confidence") or 0.0)

    if not detected:
        raise ValueError(f"编码检测失败: {result}")

    if confidence < min_confidence:
        raise ValueError(
            f"编码检测置信度过低: detected={detected}, "
            f"confidence={confidence:.4f}, threshold={min_confidence:.4f}"
        )

    return detected, confidence, result


def validate_output(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    has_bom = raw.startswith(codecs.BOM_UTF8)
    has_double_bom = raw.startswith(codecs.BOM_UTF8 + codecs.BOM_UTF8)

    raw.decode("utf-8-sig", errors="strict")

    body = raw[len(codecs.BOM_UTF8):] if has_bom else raw
    without_crlf = body.replace(b"\r\n", b"")
    has_bare_lf = b"\n" in without_crlf
    has_bare_cr = b"\r" in without_crlf

    return {
        "has_utf8_bom": has_bom,
        "has_double_utf8_bom": has_double_bom,
        "crlf_only": not has_bare_lf and not has_bare_cr,
        "has_bare_lf": has_bare_lf,
        "has_bare_cr": has_bare_cr,
    }


def convert_to_utf8_bom_crlf(
    input_file: Path,
    output_file: Path,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    overwrite: bool = False,
) -> dict[str, Any]:
    if not input_file.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_file}")

    if input_file.is_dir():
        raise IsADirectoryError(f"输入路径是目录: {input_file}")

    if output_file.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在: {output_file}")

    raw = input_file.read_bytes()
    detected, confidence, detection_result = detect_encoding(raw, min_confidence)

    try:
        text = raw.decode(detected, errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"严格解码失败: detected={detected}, "
            f"confidence={confidence:.4f}, error={exc}"
        ) from exc

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(normalize_crlf(text), encoding="utf-8-sig", newline="")

    validation = validate_output(output_file)
    if not validation["has_utf8_bom"]:
        raise ValueError(f"输出校验失败: 缺少 UTF-8 BOM: {output_file}")
    if validation["has_double_utf8_bom"]:
        raise ValueError(f"输出校验失败: 存在双 UTF-8 BOM: {output_file}")
    if not validation["crlf_only"]:
        raise ValueError(f"输出校验失败: 换行不是纯 CRLF: {output_file}")

    return {
        "input": str(input_file),
        "output": str(output_file),
        "detected_encoding": detected,
        "confidence": round(confidence, 4),
        "min_confidence": min_confidence,
        "detection": detection_result,
        "output_format": "UTF-8 BOM + CRLF",
        "validation": validation,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将未知编码文本转换为 UTF-8 BOM + CRLF。")
    parser.add_argument("input", type=Path, help="输入文本文件")
    parser.add_argument("output", type=Path, help="输出文本文件")
    parser.add_argument("--min-confidence", type=float, default=DEFAULT_MIN_CONFIDENCE, help="最低检测置信度")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖输出文件")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = convert_to_utf8_bom_crlf(
        input_file=args.input,
        output_file=args.output,
        min_confidence=args.min_confidence,
        overwrite=args.overwrite,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
