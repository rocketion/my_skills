#!/usr/bin/env python3
"""将文本文件原地转换为 UTF-8 BOM + CRLF，并校验转换结果。

脚本只提供两个命令：
- `convert <file>`：检测源文件编码，严格解码，统一换行，并以 UTF-8 BOM + CRLF 覆盖写回原文件。
- `validate <file>`：按字节级规则校验文件是否已经满足 UTF-8 BOM + CRLF 格式。

设计原则：
- KISS：命令数量和参数保持最小，转换默认原地覆盖。
- DRY：文件检查、编码检测、严格解码、校验逻辑只实现一次。
- YAGNI：不实现备份、批量处理、输出到新文件等当前未要求的能力。
- SOLID：命令行解析只负责分发，转换和校验逻辑保持独立函数。
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
    """表示文件不能被安全转换或校验。"""


@dataclass(frozen=True)
class EncodingDetection:
    """统一保存编码检测结果，避免在函数之间传递散乱字段。"""

    encoding: str
    confidence: float
    raw_result: dict[str, Any]


def ensure_regular_file(path: Path) -> None:
    """确认路径是一个已存在的普通文件。

    转换和校验都必须先读文件字节，因此这里集中处理文件路径前置条件。
    """

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"路径是目录: {path}")
    if not path.is_file():
        raise ConversionError(f"路径不是普通文件: {path}")


def normalize_crlf(text: str) -> str:
    """将 CRLF、CR、LF 三种换行统一为 CRLF。

    先统一为 LF，再统一写成 CRLF，可以避免把已有 CRLF 重复改成 CRCRLF。
    """

    lf_text = text.replace("\r\n", "\n").replace("\r", "\n")
    return lf_text.replace("\n", "\r\n")


def detect_encoding(raw: bytes, min_confidence: float) -> EncodingDetection:
    """检测源文件编码，并拒绝低置信度结果。

    低置信度继续转换容易静默损坏内容，因此这里直接抛出异常。
    """

    result = chardet.detect(raw)
    encoding = result.get("encoding")
    confidence = float(result.get("confidence") or 0.0)

    if not encoding:
        raise ConversionError(f"编码检测失败: {result}")
    if confidence < min_confidence:
        raise ConversionError(
            "编码检测置信度过低: "
            f"检测编码={encoding}, 置信度={confidence:.4f}, "
            f"最低置信度={min_confidence:.4f}"
        )

    return EncodingDetection(encoding=encoding, confidence=confidence, raw_result=result)


def decode_strict(raw: bytes, detection: EncodingDetection) -> str:
    """使用检测出的编码严格解码原始字节。

    严格解码不允许替换或忽略坏字节；失败时说明当前编码判断不能安全使用。
    """

    try:
        return raw.decode(detection.encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise ConversionError(
            "严格解码失败: "
            f"检测编码={detection.encoding}, "
            f"置信度={detection.confidence:.4f}, 错误={exc}"
        ) from exc


def write_utf8_bom_crlf(path: Path, text: str) -> None:
    """用 UTF-8 BOM + CRLF 覆盖写回原文件。"""

    path.write_text(normalize_crlf(text), encoding="utf-8-sig", newline="")


def validate_utf8_bom_crlf(path: Path) -> dict[str, Any]:
    """校验文件是否满足 UTF-8 BOM + CRLF，并返回结构化结果。"""

    ensure_regular_file(path)
    raw = path.read_bytes()

    # BOM 是字节级格式要求，必须独立检查；utf-8-sig 可解码并不能证明存在 BOM。
    has_bom = raw.startswith(codecs.BOM_UTF8)
    has_double_bom = raw.startswith(codecs.BOM_UTF8 + codecs.BOM_UTF8)

    # 严格解码只验证 UTF-8 合法性，不替代 BOM 或换行检查。
    utf8_sig_strict_decode = True
    utf8_sig_error = None
    try:
        raw.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        utf8_sig_strict_decode = False
        utf8_sig_error = str(exc)

    # 换行只检查正文部分；如果存在 BOM，先把 BOM 从正文检查范围中移除。
    body = raw[len(codecs.BOM_UTF8) :] if has_bom else raw

    # 移除所有合法 CRLF 后，剩余的 LF 或 CR 都是裸换行。
    body_without_crlf_pairs = body.replace(b"\r\n", b"")
    has_bare_lf = b"\n" in body_without_crlf_pairs
    has_bare_cr = b"\r" in body_without_crlf_pairs
    crlf_only = not has_bare_lf and not has_bare_cr

    passed = has_bom and not has_double_bom and crlf_only and utf8_sig_strict_decode
    result: dict[str, Any] = {
        "文件": str(path),
        "目标格式": TARGET_FORMAT,
        "存在_UTF8_BOM": has_bom,
        "存在双_UTF8_BOM": has_double_bom,
        "仅使用_CRLF_换行": crlf_only,
        "存在裸_LF": has_bare_lf,
        "存在裸_CR": has_bare_cr,
        "UTF8_SIG_严格解码通过": utf8_sig_strict_decode,
        "通过": passed,
    }
    if utf8_sig_error:
        result["UTF8_SIG_严格解码错误"] = utf8_sig_error
    return result


def convert_file(path: Path, min_confidence: float = DEFAULT_MIN_CONFIDENCE) -> dict[str, Any]:
    """原地转换文本文件，并在写回后立即校验。"""

    ensure_regular_file(path)

    # 转换流程保持单向流水线：读字节 -> 检测编码 -> 严格解码 -> 规范写回 -> 校验。
    raw = path.read_bytes()
    detection = detect_encoding(raw, min_confidence)
    text = decode_strict(raw, detection)
    write_utf8_bom_crlf(path, text)

    validation = validate_utf8_bom_crlf(path)
    if not validation["通过"]:
        raise ConversionError(f"转换后校验失败: {validation}")

    return {
        "动作": "转换",
        "文件": str(path),
        "检测编码": detection.encoding,
        "置信度": round(detection.confidence, 4),
        "最低置信度": min_confidence,
        "编码检测原始结果": detection.raw_result,
        "输出格式": TARGET_FORMAT,
        "校验结果": validation,
        "通过": True,
    }


def print_json(payload: dict[str, Any]) -> None:
    """输出稳定的中文 JSON，便于人工审查和自动化读取。"""

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def run_convert(args: argparse.Namespace) -> int:
    """执行 convert 命令。"""

    print_json(convert_file(args.file, min_confidence=args.min_confidence))
    return 0


def run_validate(args: argparse.Namespace) -> int:
    """执行 validate 命令，并用退出码表达校验结果。"""

    result = validate_utf8_bom_crlf(args.file)
    print_json({"动作": "校验", **result})
    return 0 if result["通过"] else 1


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。

    CLI 只负责参数解析和命令分发，不混入转换或校验细节。
    """

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
    """程序入口，统一把异常转为结构化中文输出。"""

    args = build_parser().parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print_json({"错误": str(exc), "通过": False})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
