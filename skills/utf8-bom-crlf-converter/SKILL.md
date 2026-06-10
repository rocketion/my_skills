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

执行分支：

- Step 1 通过：进入 Step 2。
- Step 1 未通过：停止当前流程，依据命令输出处理环境问题。

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

执行分支：

- 转换成功：进入 Step 3。
- 转换失败：停止当前流程，保留脚本结构化输出作为失败原因。

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

执行分支：

- 校验成功：文件视为有效产物。
- 校验失败：文件不视为有效产物，保留脚本结构化输出作为校验结果。

## 注意事项

- 本 Skill 处理文本文件，不处理二进制文件、压缩包、Office 文档、图片或数据库文件。
- 转换前确认输入文件来源和文件路径。
- 低置信度编码检测结果不作为可靠转换依据。
- 严格解码失败时不生成有效产物。
- 结构化日志用于审查转换过程和定位失败原因。
