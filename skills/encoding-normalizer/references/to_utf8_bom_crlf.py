#!/usr/bin/env python3
"""Convert an unknown-encoding text file to UTF-8 BOM + CRLF.

Policy:
- Use chardet to detect encoding and confidence.
- Refuse conversion when confidence is below the configured threshold.
- Decode strictly; do not replace or ignore bad bytes.
- Normalize all line endings to CRLF.
- Write UTF-8 with BOM via utf-8-sig.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import chardet


DEFAULT_MIN_CONFIDENCE = 0.80

ENCODING_MAP = {
    "ascii": "utf-8",
    "gb2312": "gb18030",
    "gbk": "gb18030",
    "iso-8859-1": "windows-1252",
}


def normalize_encoding_name(encoding: str) -> str:
    """Normalize encoding names for lookup only."""
    return encoding.strip().lower().replace("_", "-")


def map_encoding(encoding: str) -> str:
    """Apply conservative decode-time aliases for common detector outputs."""
    key = normalize_encoding_name(encoding)
    return ENCODING_MAP.get(key, encoding)


def normalize_crlf(text: str) -> str:
    """Normalize CRLF, CR, and LF to CRLF."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.replace("\n", "\r\n")


def detect_encoding(raw: bytes, min_confidence: float) -> tuple[str, str, float, dict[str, Any]]:
    """Detect source encoding and enforce a confidence threshold."""
    result = chardet.detect(raw)
    detected = result.get("encoding")
    confidence = float(result.get("confidence") or 0.0)

    if not detected:
        raise ValueError(f"encoding detection failed: {result}")

    if confidence < min_confidence:
        raise ValueError(
            "encoding confidence below threshold: "
            f"detected={detected}, confidence={confidence:.4f}, "
            f"threshold={min_confidence:.4f}"
        )

    mapped = map_encoding(detected)
    return detected, mapped, confidence, result


def validate_utf8_bom_crlf(path: Path) -> dict[str, Any]:
    """Validate output bytes are UTF-8 BOM + CRLF and not double-BOM."""
    raw = path.read_bytes()
    has_utf8_bom = raw.startswith(b"\xef\xbb\xbf")
    has_double_utf8_bom = raw.startswith(b"\xef\xbb\xbf\xef\xbb\xbf")

    # Strict UTF-8 validation. utf-8-sig consumes one leading BOM if present.
    raw.decode("utf-8-sig", errors="strict")

    body = raw[3:] if has_utf8_bom else raw
    without_crlf = body.replace(b"\r\n", b"")
    has_bare_lf = b"\n" in without_crlf
    has_bare_cr = b"\r" in without_crlf

    return {
        "has_utf8_bom": has_utf8_bom,
        "has_double_utf8_bom": has_double_utf8_bom,
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
    """Convert one text file to UTF-8 BOM + CRLF."""
    if not input_file.exists():
        raise FileNotFoundError(f"input file does not exist: {input_file}")

    if input_file.is_dir():
        raise IsADirectoryError(f"input path is a directory: {input_file}")

    if output_file.exists() and not overwrite:
        raise FileExistsError(f"output file already exists: {output_file}")

    raw = input_file.read_bytes()
    detected, encoding, confidence, detection_result = detect_encoding(raw, min_confidence)

    try:
        text = raw.decode(encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "strict decode failed: "
            f"detected={detected}, mapped={encoding}, confidence={confidence:.4f}, "
            f"error={exc}"
        ) from exc

    text = normalize_crlf(text)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(text, encoding="utf-8-sig", newline="")

    validation = validate_utf8_bom_crlf(output_file)
    if not validation["has_utf8_bom"]:
        raise ValueError(f"output validation failed: missing UTF-8 BOM: {output_file}")
    if validation["has_double_utf8_bom"]:
        raise ValueError(f"output validation failed: double UTF-8 BOM: {output_file}")
    if not validation["crlf_only"]:
        raise ValueError(f"output validation failed: line endings are not CRLF-only: {output_file}")

    return {
        "input": str(input_file),
        "output": str(output_file),
        "detected_encoding": detected,
        "mapped_encoding": encoding,
        "confidence": round(confidence, 4),
        "min_confidence": min_confidence,
        "detection": detection_result,
        "output_format": "UTF-8 BOM + CRLF",
        "validation": validation,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert an unknown-encoding text file to UTF-8 BOM + CRLF."
    )
    parser.add_argument("input", type=Path, help="Input text file")
    parser.add_argument("output", type=Path, help="Output text file")
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=DEFAULT_MIN_CONFIDENCE,
        help=f"Minimum chardet confidence. Default: {DEFAULT_MIN_CONFIDENCE}",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output file.",
    )
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
