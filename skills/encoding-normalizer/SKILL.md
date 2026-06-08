---
name: encoding-normalizer
description: 将未知编码的文本文件按检测置信度转换为 UTF-8 BOM + CRLF，低置信度或严格解码失败时拒绝转换。
---

# Encoding Normalizer

## 定位

这个 skill 用于把编码未知的文本文件转换为 `UTF-8 with BOM + CRLF`。

目标不是无条件转换成功，而是在检测置信度不足或严格解码失败时拒绝转换，避免静默损坏内容。

## 适用场景

- 输入是裸文本文件。
- 输入编码未知。
- 输出格式要求为 `UTF-8 with BOM + CRLF`。
- 用户接受低置信度失败，不接受替换或忽略坏字节造成的数据损坏。

## 不适用场景

- 二进制文件、压缩包、Office 文档、图片、数据库文件。
- 需要在低置信度下仍强制转换的任务。

## 运行前提

1. 默认使用目标项目根目录下的 `.venv` 作为本地虚拟环境。
2. 创建 `.venv` 前必须先确认它不会进入 Git 工作区。
3. 若 `.venv` 已被 Git 忽略，则可以创建或复用。
4. 若 `.venv` 未被 Git 忽略，必须停止并提示用户先处理忽略规则。
5. 不允许为了安装依赖而直接污染系统 Python 环境。
6. 不允许在未确认 Git 忽略规则时创建虚拟环境、缓存目录或依赖包。

推荐检查命令：

```bash
git check-ignore -q .venv || {
  echo ".venv 未被 Git 忽略，停止执行"
  exit 1
}
```

推荐创建或复用虚拟环境：

```bash
if [ ! -x .venv/bin/python ]; then
  python -m venv .venv
fi

.venv/bin/python -m pip install -q chardet
.venv/bin/python skills/encoding-normalizer/scripts/to_utf8_bom_crlf.py input.txt output.txt
```

Windows PowerShell：

```powershell
git check-ignore -q .venv
if ($LASTEXITCODE -ne 0) {
    Write-Error ".venv 未被 Git 忽略，停止执行"
    exit 1
}

$Python = ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    python -m venv .venv
}

& $Python -m pip install -q chardet
& $Python skills\encoding-normalizer\scripts\to_utf8_bom_crlf.py input.txt output.txt
```

## 原则

1. 使用检测库获取编码和置信度。
2. 默认置信度阈值为 `0.80`。
3. 低于阈值时失败退出。
4. 解码必须使用严格模式。
5. 不使用替换、忽略或吞错字节策略。
6. 输出使用 `utf-8-sig`，即 UTF-8 BOM。
7. 换行统一为 CRLF。
8. 输出后校验 BOM、双 BOM、裸 LF、裸 CR 和 UTF-8 可解码性。

## 脚本

可执行脚本位于 `scripts/to_utf8_bom_crlf.py`。

执行：

```bash
.venv/bin/python skills/encoding-normalizer/scripts/to_utf8_bom_crlf.py input.txt output.txt
```

调整置信度：

```bash
.venv/bin/python skills/encoding-normalizer/scripts/to_utf8_bom_crlf.py input.txt output.txt --min-confidence 0.85
```

覆盖输出：

```bash
.venv/bin/python skills/encoding-normalizer/scripts/to_utf8_bom_crlf.py input.txt output.txt --overwrite
```

## 流程

1. 定位目标项目根目录。
2. 检查 `.venv` 是否被 Git 忽略。
3. 若未被忽略，停止并提示用户处理忽略规则。
4. 若已被忽略，复用现有 `.venv`；不存在时创建。
5. 在 `.venv` 中安装或确认检测依赖。
6. 读取原始字节。
7. 调用 `chardet.detect` 获取 `encoding` 和 `confidence`。
8. 若无编码结果或置信度不足，失败退出。
9. 使用检测到的编码严格解码。
10. 将 `CRLF`、`CR`、`LF` 统一归一为 `LF`。
11. 再将 `LF` 统一转换为 `CRLF`。
12. 使用 `utf-8-sig` 写出。
13. 校验输出格式。

## 验收

输出文件必须满足：

- 文件开头为 `EF BB BF`。
- 没有双 UTF-8 BOM。
- 正文中没有裸 LF。
- 正文中没有裸 CR。
- 可用 `utf-8-sig` 严格解码。
- 日志记录输入路径、输出路径、检测编码和置信度。
- `.venv`、依赖包和缓存目录不应出现在 `git status` 中。
