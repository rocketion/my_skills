# UTF-8 BOM + CRLF 转换脚本

`to_utf8_bom_crlf.py` 用于把未知编码的文本文件转换为 `UTF-8 with BOM + CRLF`。

## 运行前提

默认使用目标项目根目录下的 `.venv` 作为本地虚拟环境。创建前必须确认 `.venv` 已被 Git 忽略；若未被忽略，必须停止并先处理忽略规则。

Linux/macOS 示例：

```bash
git check-ignore -q .venv || {
  echo ".venv 未被 Git 忽略，停止执行"
  exit 1
}

if [ ! -x .venv/bin/python ]; then
  python -m venv .venv
fi

.venv/bin/python -m pip install -q chardet
.venv/bin/python skills/encoding-normalizer/references/to_utf8_bom_crlf.py input.txt output.txt
```

Windows 示例：

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
& $Python skills\encoding-normalizer\references\to_utf8_bom_crlf.py input.txt output.txt
```

## 用法

指定更高置信度阈值：

```bash
.venv/bin/python skills/encoding-normalizer/references/to_utf8_bom_crlf.py input.txt output.txt --min-confidence 0.85
```

覆盖已有输出文件：

```bash
.venv/bin/python skills/encoding-normalizer/references/to_utf8_bom_crlf.py input.txt output.txt --overwrite
```

## 策略

- 使用 `chardet.detect` 获取编码和置信度。
- 置信度低于阈值时失败。
- 严格解码，不替换、不忽略坏字节。
- 所有换行统一为 CRLF。
- 使用 `utf-8-sig` 写出，输出文件带 UTF-8 BOM。
- 写出后验证 BOM、双 BOM、裸 LF 和裸 CR。
- `.venv`、依赖包和缓存目录不应出现在 `git status` 中。
