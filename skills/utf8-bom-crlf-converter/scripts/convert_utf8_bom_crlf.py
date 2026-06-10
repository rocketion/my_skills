#!/usr/bin/env python3
"""Convert text files in place to UTF-8 BOM + CRLF, and validate the result.

The script intentionally keeps the command surface small:
- `convert <file>` detects the source encoding, strictly decodes it, normalizes
  newlines, and overwrites the same file as UTF-8 with BOM + CRLF.
- `validate <file>` checks the target byte-level format.
"""

from __future__ import annotations

import argparse
import codecs
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chardet


DEFAULT_MIN_CONFIDENCE = 0.80
TARGET_FORMAT = "UTF-8 BOM + CRLF"


class ConversionError(RuntimeError):
    """Raised when a file cannot be safely converted."""


@dataclass(frozen=True)
class EncodingDetection:
    """Normalized encoding detection result used by the converter."""

    encoding: str
    confidence: float
    raw_result: dict[str, Any]


def ensure_regular_file(path: Path) -> None:
    """Require an existing regular file before reading or rewriting it."""

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"路径是目录: {path}")
    if not path.is_file():
        raise ConversionError(f"路径不是普通文件: {path}")


def normalize_crlf(text: str) -> str:
    """Normalize CRLF, CR, and LF input into CRLF-only output."""

    lf_text = text.replace("\r\n", "\n").replace("\r", "\n")
    return lf_text.replace("\n", "\r\n")


def detect_encoding(raw: bytes, min_confidence: float) -> EncodingDetection:
    """Detect source encoding and reject low-confidence results."""

    result = chardet.detect(raw)
    encoding = result.get("encoding")
    confidence = float(result.get("confidence") or 0.0)

    if not encoding:
        raise ConversionError(f"编码检测失败: {result}")
    if confidence < min_confidence:
        raise ConversionError(
            "编码检测置信度过低: "
            f"detected={encoding}, confidence={confidence:.4f}, "
            f"threshold={min_confidence:.4f}"
        )

    return EncodingDetection(encoding=encoding, confidence=confidence, raw_result=result)


def decode_strict(raw: bytes, detection: EncodingDetection) -> str:
    """Decode bytes using the detected encoding without replacement or ignore."""

    try:
        return raw.decode(detection.encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise ConversionError(
            "严格解码失败: "
            f"detected={detection.encoding}, "
            f"confidence={detection.confidence:.4f}, error={exc}"
        ) from exc


def write_utf8_bom_crlf(path: Path, text: str) -> None:
    """Overwrite the file with UTF-8 BOM and CRLF newlines."""

    path.write_text(normalize_crlf(text), encoding="utf-8-sig", newline="")


def validate_utf8_bom_crlf(path: Path) -> dict[str, Any]:
    """Validate the exact target format and return structured check results."""

    ensure_regular_file(path)
    raw = path.read_bytes()

    has_bom = raw.startswith(codecs.BOM_UTF8)
    has_double_bom = raw.startswith(codecs.BOM_UTF8 + codecs.BOM_UTF8)

    utf8_sig_strict_decode = True
    utf8_sig_error = None
    try:
        raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        utf8_sig_strict_decode = False
        utf8_sig_error = str(exc)

    # BOM is checked separately. Newline checks apply to the text body only.
    body = raw[len(codecs.BOM_UTF8) :] if has_bom else raw
    body_without_crlf_pairs = body.replace(b"\r\n", b"")
    has_bare_lf = b"\n" in body_without_crlf_pairs
    has_bare_cr = b"\r" in body_without_crlf_pairs
    crlf_only = not has_bare_lf and not has_bare_cr

    passed = has_bom and not has_double_bom and crlf_only and utf8_sig_strict_decode
    result: dict[str, Any] = {
        "file": str(path),
        "format": TARGET_FORMAT,
        "has_utf8_bom": has_bom,
        "has_double_utf8_bom": has_double_bom,
        "crlf_only": crlf_only,
        "has_bare_lf": has_bare_lf,
        "has_bare_cr": has_bare_cr,
        "utf8_sig_strict_decode": utf8_sig_strict_decode,
        "passed": passed,
    }
    if utf8_sig_error:
        result["utf8_sig_error"] = utf8_sig_error
    return result


def convert_file(path: Path, min_confidence: float = DEFAULT_MIN_CONFIDENCE) -> dict[str, Any]:
    """Convert a text file in place and validate the rewritten file."""

    ensure_regular_file(path)

    raw = path.read_bytes()
    detection = detect_encoding(raw, min_confidence)
    text = decode_strict(raw, detection)
    write_utf8_bom_crlf(path, text)

    validation = validate_utf8_bom_crlf(path)
    if not validation["passed"]:
        raise ConversionError(f"转换后校验失败: {validation}")

    return {
        "action": "convert",
        "file": str(path),
        "detected_encoding": detection.encoding,
        "confidence": round(detection.confidence, 4),
        "min_confidence": min_confidence,
        "detection": detection.raw_result,
        "output_format": TARGET_FORMAT,
        "validation": validation,
        "passed": True,
    }


def print_json(payload: dict[str, Any]) -> None:
    """Print stable, human-readable JSON for logs and automation."""

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def run_convert(args: argparse.Namespace) -> int:
    print_json(convert_file(args.file, min_confidence=args.min_confidence))
    return 0


def run_validate(args: argparse.Namespace) -> int:
    result = validate_utf8_bom_crlf(args.file)
    print_json({"action": "validate", **result})
    return 0 if result["passed"] else 1


def build_parser() -> argparse.ArgumentParser:
    """Build the command line interface without mixing in business logic."""

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

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print_json({"error": str(exc), "passed": False})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
