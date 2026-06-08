# UTF-8 BOM + CRLF 转换脚本

`to_utf8_bom_crlf.py` 用于把未知编码的文本文件转换为 `UTF-8 with BOM + CRLF`。

## 运行前提

依赖和虚拟环境必须放在目标项目目录外，避免污染目标项目的 Git 工作区。

Linux/macOS 示例：

```bash
python -m venv /tmp/encoding-normalizer-venv
/tmp/encoding-normalizer-venv/bin/python -m pip install chardet
/tmp/encoding-normalizer-venv/bin/python to_utf8_bom_crlf.py input.txt output.txt
```

Windows 示例：

```powershell
python -m venv $env:TEMP\encoding-normalizer-venv
$env:TEMP\encoding-normalizer-venv\Scripts\python.exe -m pip install chardet
$env:TEMP\encoding-normalizer-venv\Scripts\python.exe to_utf8_bom_crlf.py input.txt output.txt
```

## 用法

指定更高置信度阈值：

```bash
/tmp/encoding-normalizer-venv/bin/python to_utf8_bom_crlf.py input.txt output.txt --min-confidence 0.85
```

覆盖已有输出文件：

```bash
/tmp/encoding-normalizer-venv/bin/python to_utf8_bom_crlf.py input.txt output.txt --overwrite
```

## 策略

- 使用 `chardet.detect` 获取编码和置信度。
- 置信度低于阈值时失败。
- 严格解码，不替换、不忽略坏字节。
- 所有换行统一为 CRLF。
- 使用 `utf-8-sig` 写出，输出文件带 UTF-8 BOM。
- 写出后验证 BOM、双 BOM、裸 LF 和裸 CR。
- 虚拟环境、依赖包和缓存目录不得写入目标项目目录。
