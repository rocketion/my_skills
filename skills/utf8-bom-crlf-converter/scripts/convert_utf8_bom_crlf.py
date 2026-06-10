#!/usr/bin/env python3
"""Convert text files to UTF-8 BOM + CRLF and validate the result."""

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


def validate_utf8_bom_crlf(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"路径是目录: {path}")

    raw = path.read_bytes()
    has_bom = raw.startswith(codecs.BOM_UTF8)
    has_double_bom = raw.startswith(codecs.BOM_UTF8 + codecs.BOM_UTF8)

    utf8_sig_strict = True
    utf8_sig_error = None
    try:
        raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        utf8_sig_strict = False
        utf8_sig_error = str(exc)

    body = raw[len(codecs.BOM_UTF8):] if has_bom else raw
    without_crlf = body.replace(b"\r\n", b"")
    has_bare_lf = b"\n" in without_crlf
    has_bare_cr = b"\r" in without_crlf
    crlf_only = not has_bare_lf and not has_bare_cr
    passed = has_bom and not has_double_bom and crlf_only and utf8_sig_strict

    result: dict[str, Any] = {
        "file": str(path),
        "has_utf8_bom": has_bom,
        "has_double_utf8_bom": has_double_bom,
        "crlf_only": crlf_only,
        "has_bare_lf": has_bare_lf,
        "has_bare_cr": has_bare_cr,
        "utf8_sig_strict_decode": utf8_sig_strict,
        "passed": passed,
    }
    if utf8_sig_error:
        result["utf8_sig_error"] = utf8_sig_error
    return result


def convert_file(path: Path, min_confidence: float = DEFAULT_MIN_CONFIDENCE) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"输入文件不存在: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"输入路径是目录: {path}")

    raw = path.read_bytes()
    detected, confidence, detection_result = detect_encoding(raw, min_confidence)

    try:
        text = raw.decode(detected, errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"严格解码失败: detected={detected}, "
            f"confidence={confidence:.4f}, error={exc}"
        ) from exc

    path.write_text(normalize_crlf(text), encoding="utf-8-sig", newline="")
    validation = validate_utf8_bom_crlf(path)
    if not validation["passed"]:
        raise ValueError(f"输出校验失败: {validation}")

    return {
        "action": "convert",
        "file": str(path),
        "detected_encoding": detected,
        "confidence": round(confidence, 4),
        "min_confidence": min_confidence,
        "detection": detection_result,
        "output_format": "UTF-8 BOM + CRLF",
        "validation": validation,
    }


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def run_convert(args: argparse.Namespace) -> int:
    result = convert_file(args.file, min_confidence=args.min_confidence)
    print_json(result)
    return 0


def run_validate(args: argparse.Namespace) -> int:
    result = validate_utf8_bom_crlf(args.file)
    print_json({"action": "validate", **result})
    return 0 if result["passed"] else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="转换并校验 UTF-8 BOM + CRLF 文本文件。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser("convert", help="原地转换文本文件为 UTF-8 BOM + CRLF")
    convert_parser.add_argument("file", type=Path, help="待转换文本文件")
    convert_parser.add_argument(
        "--min-confidence",
        type=float,
        default=DEFAULT_MIN_CONFIDENCE,
        help=f"最低编码检测置信度，默认 {DEFAULT_MIN_CONFIDENCE:.2f}",
    )
    convert_parser.set_defaults(func=run_convert)

    validate_parser = subparsers.add_parser("validate", help="校验文本文件是否为 UTF-8 BOM + CRLF")
    validate_parser.add_argument("file", type=Path, help="待校验文本文件")
    validate_parser.set_defaults(func=run_validate)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print_json({"error": str(exc), "passed": False})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
