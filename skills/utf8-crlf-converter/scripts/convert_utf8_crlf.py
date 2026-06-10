#!/usr/bin/env python3
"""将文本文件原地转换为 UTF-8 + CRLF，并按目标格式校验结果。

脚本提供两组功能：
- `convert-with-bom` / `validate-with-bom`：处理 UTF-8 with BOM + CRLF。
- `convert-without-bom` / `validate-without-bom`：处理 UTF-8 without BOM + CRLF。

设计原则：
- KISS：每个命令只做一件事，转换命令默认原地覆盖。
- DRY：带 BOM 和不带 BOM 共享同一套检测、解码、换行归一和校验逻辑。
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
FORMAT_WITH_BOM = "UTF-8 with BOM + CRLF"
FORMAT_WITHOUT_BOM = "UTF-8 without BOM + CRLF"


class ConversionError(RuntimeError):
    """表示文件不能被安全转换或校验。"""


@dataclass(frozen=True)
class EncodingDetection:
    """统一保存编码检测结果，避免在函数之间传递散乱字段。"""

    encoding: str
    confidence: float
    raw_result: dict[str, Any]


@dataclass(frozen=True)
class TargetFormat:
    """描述目标格式中是否需要 UTF-8 BOM。"""

    name: str
    include_bom: bool


WITH_BOM = TargetFormat(name=FORMAT_WITH_BOM, include_bom=True)
WITHOUT_BOM = TargetFormat(name=FORMAT_WITHOUT_BOM, include_bom=False)


def ensure_regular_file(path: Path) -> None:
    """确认路径是一个已存在的普通文件。"""

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

    空文件没有可检测内容，但可以安全视为 UTF-8 文本。
    """

    if raw == b"":
        return EncodingDetection(
            encoding="utf-8",
            confidence=1.0,
            raw_result={"encoding": "utf-8", "confidence": 1.0, "language": ""},
        )

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
    """使用检测出的编码严格解码原始字节。"""

    try:
        return raw.decode(detection.encoding, errors="strict")
    except UnicodeDecodeError as exc:
        raise ConversionError(
            "严格解码失败: "
            f"检测编码={detection.encoding}, "
            f"置信度={detection.confidence:.4f}, 错误={exc}"
        ) from exc


def write_utf8_crlf(path: Path, text: str, target: TargetFormat) -> None:
    """按目标格式覆盖写回原文件。"""

    encoding = "utf-8-sig" if target.include_bom else "utf-8"
    path.write_text(normalize_crlf(text), encoding=encoding, newline="")


def check_newlines(body: bytes) -> dict[str, bool]:
    """检查正文是否只使用 CRLF 换行。"""

    body_without_crlf_pairs = body.replace(b"\r\n", b"")
    has_bare_lf = b"\n" in body_without_crlf_pairs
    has_bare_cr = b"\r" in body_without_crlf_pairs
    return {
        "仅使用_CRLF_换行": not has_bare_lf and not has_bare_cr,
        "存在裸_LF": has_bare_lf,
        "存在裸_CR": has_bare_cr,
    }


def check_strict_utf8(raw: bytes, target: TargetFormat) -> tuple[bool, str | None]:
    """按目标格式执行 UTF-8 严格解码检查。"""

    encoding = "utf-8-sig" if target.include_bom else "utf-8"
    try:
        raw.decode(encoding, errors="strict")
        return True, None
    except UnicodeDecodeError as exc:
        return False, str(exc)


def validate_utf8_crlf(path: Path, target: TargetFormat) -> dict[str, Any]:
    """校验文件是否满足目标 UTF-8 + CRLF 格式。"""

    ensure_regular_file(path)
    raw = path.read_bytes()

    # BOM 是字节级格式要求，必须独立检查；解码成功不能证明 BOM 状态正确。
    has_bom = raw.startswith(codecs.BOM_UTF8)
    has_double_bom = raw.startswith(codecs.BOM_UTF8 + codecs.BOM_UTF8)
    bom_valid = has_bom if target.include_bom else not has_bom

    # 换行只检查正文部分；带 BOM 时先把 BOM 从正文检查范围中移除。
    body = raw[len(codecs.BOM_UTF8) :] if has_bom else raw
    newline_result = check_newlines(body)

    strict_decode_ok, strict_decode_error = check_strict_utf8(raw, target)
    passed = (
        bom_valid
        and not has_double_bom
        and newline_result["仅使用_CRLF_换行"]
        and strict_decode_ok
    )

    result: dict[str, Any] = {
        "文件": str(path),
        "目标格式": target.name,
        "要求_UTF8_BOM": target.include_bom,
        "存在_UTF8_BOM": has_bom,
        "存在双_UTF8_BOM": has_double_bom,
        "BOM_状态正确": bom_valid,
        **newline_result,
        "UTF8_严格解码通过": strict_decode_ok,
        "通过": passed,
    }
    if strict_decode_error:
        result["UTF8_严格解码错误"] = strict_decode_error
    return result


def convert_file(
    path: Path,
    target: TargetFormat,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> dict[str, Any]:
    """原地转换文本文件，并在写回后立即校验。"""

    ensure_regular_file(path)

    # 转换流程保持单向流水线：读字节 -> 检测编码 -> 严格解码 -> 规范写回 -> 校验。
    raw = path.read_bytes()
    detection = detect_encoding(raw, min_confidence)
    text = decode_strict(raw, detection)
    write_utf8_crlf(path, text, target)

    validation = validate_utf8_crlf(path, target)
    if not validation["通过"]:
        raise ConversionError(f"转换后校验失败: {validation}")

    return {
        "动作": "转换",
        "文件": str(path),
        "目标格式": target.name,
        "检测编码": detection.encoding,
        "置信度": round(detection.confidence, 4),
        "最低置信度": min_confidence,
        "编码检测原始结果": detection.raw_result,
        "校验结果": validation,
        "通过": True,
    }


def print_json(payload: dict[str, Any]) -> None:
    """输出稳定的中文 JSON，便于人工审查和自动化读取。"""

    print(json.dumps(payload, ensure_ascii=False, indent=2))


def run_convert_with_bom(args: argparse.Namespace) -> int:
    """执行带 BOM 转换命令。"""

    print_json(convert_file(args.file, WITH_BOM, min_confidence=args.min_confidence))
    return 0


def run_convert_without_bom(args: argparse.Namespace) -> int:
    """执行不带 BOM 转换命令。"""

    print_json(convert_file(args.file, WITHOUT_BOM, min_confidence=args.min_confidence))
    return 0


def run_validate_with_bom(args: argparse.Namespace) -> int:
    """执行带 BOM 校验命令。"""

    result = validate_utf8_crlf(args.file, WITH_BOM)
    print_json({"动作": "校验", **result})
    return 0 if result["通过"] else 1


def run_validate_without_bom(args: argparse.Namespace) -> int:
    """执行不带 BOM 校验命令。"""

    result = validate_utf8_crlf(args.file, WITHOUT_BOM)
    print_json({"动作": "校验", **result})
    return 0 if result["通过"] else 1


def add_convert_command(subparsers: argparse._SubParsersAction, command: str, help_text: str, func: Any) -> None:
    """添加转换命令，保持两个转换命令的参数定义一致。"""

    parser = subparsers.add_parser(command, help=help_text)
    parser.add_argument("file", type=Path, help="待转换文本文件")
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=DEFAULT_MIN_CONFIDENCE,
        help=f"最低编码检测置信度，默认 {DEFAULT_MIN_CONFIDENCE:.2f}",
    )
    parser.set_defaults(func=func)


def add_validate_command(subparsers: argparse._SubParsersAction, command: str, help_text: str, func: Any) -> None:
    """添加校验命令，保持两个校验命令的参数定义一致。"""

    parser = subparsers.add_parser(command, help=help_text)
    parser.add_argument("file", type=Path, help="待校验文本文件")
    parser.set_defaults(func=func)


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""

    parser = argparse.ArgumentParser(description="转换并校验 UTF-8 + CRLF 文本文件。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_convert_command(
        subparsers,
        "convert-with-bom",
        "原地转换文本文件为 UTF-8 with BOM + CRLF",
        run_convert_with_bom,
    )
    add_convert_command(
        subparsers,
        "convert-without-bom",
        "原地转换文本文件为 UTF-8 without BOM + CRLF",
        run_convert_without_bom,
    )
    add_validate_command(
        subparsers,
        "validate-with-bom",
        "校验文本文件是否为 UTF-8 with BOM + CRLF",
        run_validate_with_bom,
    )
    add_validate_command(
        subparsers,
        "validate-without-bom",
        "校验文本文件是否为 UTF-8 without BOM + CRLF",
        run_validate_without_bom,
    )

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
