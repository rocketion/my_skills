---
name: utf8-bom-crlf-converter
description: 将文本文件转换为 UTF-8 with BOM + CRLF，并校验输出文件格式。当用户要求统一文本编码、转换为 UTF-8 BOM、统一 CRLF 换行、校验文本文件编码或处理 Windows 文本格式时触发。
---

# UTF-8 BOM CRLF Converter

## 概述

本 Skill 用于将文本文件转换为 `UTF-8 with BOM + CRLF`，并校验文件是否满足目标格式。

该 Skill 面向文本文件处理场景。执行时先检查运行环境，再调用脚本原地转换文件，最后调用脚本校验结果。

## 目录结构

```text
skills/utf8-bom-crlf-converter/
  SKILL.md
  scripts/
    convert_utf8_bom_crlf.py
    requirements.txt
```

- `SKILL.md`：Skill 入口说明。
- `scripts/convert_utf8_bom_crlf.py`：文本格式转换与校验脚本。
- `scripts/requirements.txt`：脚本依赖声明。

## 功能清单

| 功能 | 说明 | 脚本 |
| --- | --- | --- |
| `convert-utf8-bom-crlf` | 将文本文件转换为 `UTF-8 with BOM + CRLF`，并校验文件格式 | `scripts/convert_utf8_bom_crlf.py` |

## 功能：convert-utf8-bom-crlf

### 目标

将一个文本文件原地转换为 `UTF-8 with BOM + CRLF` 格式。

输入为待格式化文本文件路径。脚本检测文件编码，按置信度判断是否继续，严格解码原始内容，统一换行后覆盖写回原文件。

文件必须满足：

- 文件开头是 UTF-8 BOM。
- 文件不存在双 UTF-8 BOM。
- 正文换行统一为 CRLF。
- 正文不存在裸 LF。
- 正文不存在裸 CR。
- 文件可用 `utf-8-sig` 严格解码。

### 执行步骤

#### Step 1：检查环境

目标：确认 Git、Python、项目 Git 状态和脚本依赖满足执行条件。

默认值：

- 默认在项目根目录执行命令。
- 默认使用当前系统 `python` 命令。
- 默认从 `skills/utf8-bom-crlf-converter/scripts/requirements.txt` 安装依赖。

Windows PowerShell：

```powershell
git --version
if ($LASTEXITCODE -ne 0) {
    Write-Error "Git 不可用。请先安装 Git，并确认 git 命令已加入 PATH。"
    exit 1
}

python --version
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python 不可用。请先安装 Python，并确认 python 命令已加入 PATH。"
    exit 1
}

git rev-parse --is-inside-work-tree
if ($LASTEXITCODE -ne 0) {
    Write-Error "当前目录不在 Git 仓库中。请切换到项目根目录；若项目尚未初始化，请先执行 git init。"
    exit 1
}

python -m pip install -r skills/utf8-bom-crlf-converter/scripts/requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "依赖安装失败。请检查 Python、pip、网络和 requirements.txt 后重试。"
    exit 1
}
```

macOS / Linux Shell：

```bash
git --version >/dev/null || {
  echo "Git 不可用。请先安装 Git，并确认 git 命令已加入 PATH。"
  exit 1
}

python --version >/dev/null || {
  echo "Python 不可用。请先安装 Python，并确认 python 命令已加入 PATH。"
  exit 1
}

git rev-parse --is-inside-work-tree >/dev/null || {
  echo "当前目录不在 Git 仓库中。请切换到项目根目录；若项目尚未初始化，请先执行 git init。"
  exit 1
}

python -m pip install -r skills/utf8-bom-crlf-converter/scripts/requirements.txt || {
  echo "依赖安装失败。请检查 Python、pip、网络和 requirements.txt 后重试。"
  exit 1
}
```

异常处理：

- Git 不可用：安装 Git，确认 `git --version` 可正常输出版本号。
- Python 不可用：安装 Python，确认 `python --version` 可正常输出版本号。
- 当前目录不在 Git 仓库中：切换到项目根目录；项目尚未初始化时先执行 `git init`。
- 依赖安装失败：检查 Python、pip、网络访问和 `scripts/requirements.txt`，修复后重新安装依赖。

#### Step 2：执行转换

目标：调用脚本将文本文件原地转换为 `UTF-8 with BOM + CRLF`。

命令格式：

```bash
python skills/utf8-bom-crlf-converter/scripts/convert_utf8_bom_crlf.py convert <file>
```

示例：

```bash
python skills/utf8-bom-crlf-converter/scripts/convert_utf8_bom_crlf.py convert input.txt
```

默认值：

- 默认原地覆盖输入文件。
- 默认最低编码检测置信度为 `0.80`。
- 默认输出格式为 `UTF-8 with BOM + CRLF`。
- 默认使用严格解码。
- 默认不使用替换、忽略或吞错字节策略。

指定最低编码检测置信度：

```bash
python skills/utf8-bom-crlf-converter/scripts/convert_utf8_bom_crlf.py convert input.txt --min-confidence 0.85
```

异常处理：

- 输入文件不存在：确认输入路径正确，重新传入存在的文本文件路径。
- 输入路径是目录：改为传入具体文本文件路径。
- 输入路径不是普通文件：改为传入普通文本文件路径。
- 编码检测失败：确认输入是文本文件；若文件来源明确，可先人工确认编码后再处理。
- 编码检测置信度低于阈值：降低 `--min-confidence` 前先人工确认文件编码；无法确认时不继续转换。
- 严格解码失败：说明检测编码无法可靠解码原始字节；确认源文件编码或更换输入文件。
- 转换后校验失败：保留脚本输出的结构化校验结果，按失败字段定位转换脚本问题。

#### Step 3：校验结果

目标：确认文件满足 `UTF-8 with BOM + CRLF` 格式要求。

命令格式：

```bash
python skills/utf8-bom-crlf-converter/scripts/convert_utf8_bom_crlf.py validate <file>
```

示例：

```bash
python skills/utf8-bom-crlf-converter/scripts/convert_utf8_bom_crlf.py validate input.txt
```

默认值：

- 默认校验目标文件本身。
- 默认按字节检查 UTF-8 BOM 和双 UTF-8 BOM。
- 默认按正文检查裸 LF 和裸 CR。
- 默认使用 `utf-8-sig` 严格解码验证 UTF-8 合法性。
- 默认校验失败返回非零退出码。

异常处理：

- 文件不存在：确认校验命令中的文件路径正确。
- 路径是目录：改为传入具体文本文件路径。
- 路径不是普通文件：改为传入普通文本文件路径。
- 缺少 UTF-8 BOM：该文件不符合目标格式。
- 存在双 UTF-8 BOM：该文件不符合目标格式。
- 存在裸 LF：该文件不符合目标格式。
- 存在裸 CR：该文件不符合目标格式。
- UTF-8 严格解码失败：该文件不符合目标格式。

## 注意事项

- 本 Skill 处理文本文件，不处理二进制文件、压缩包、Office 文档、图片或数据库文件。
- 转换前确认输入文件来源和文件路径。
- 低置信度编码检测结果不作为可靠转换依据。
- 严格解码失败时不生成有效产物。
- 结构化日志用于审查转换过程和定位失败原因。
