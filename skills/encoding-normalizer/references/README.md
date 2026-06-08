# UTF-8 BOM + CRLF 转换脚本

`to_utf8_bom_crlf.py` 用于把未知编码的文本文件转换为 `UTF-8 with BOM + CRLF`。

## 安装

```bash
pip install chardet
```

## 用法

```bash
python to_utf8_bom_crlf.py input.txt output.txt
```

指定更高置信度阈值：

```bash
python to_utf8_bom_crlf.py input.txt output.txt --min-confidence 0.85
```

覆盖已有输出文件：

```bash
python to_utf8_bom_crlf.py input.txt output.txt --overwrite
```

## 输出策略

- 使用 `chardet.detect` 获取 `encoding` 和 `confidence`。
- `confidence` 低于阈值时失败。
- 严格解码，禁止 `replace` / `ignore`。
- 所有换行统一为 CRLF。
- 使用 `utf-8-sig` 写出，输出文件带 UTF-8 BOM。
- 写出后验证 BOM、双 BOM、裸 LF 和裸 CR。

## 编码映射

脚本对部分检测结果做保守映射：

| 检测结果 | 实际解码 |
| --- | --- |
| `ascii` | `utf-8` |
| `gb2312` | `gb18030` |
| `gbk` | `gb18030` |
| `iso-8859-1` | `windows-1252` |

这些映射用于减少常见误差，但不会绕过置信度阈值和严格解码。
