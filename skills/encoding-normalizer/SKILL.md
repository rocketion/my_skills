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

- JSON、源码、协议内容等明确不应写入 BOM 的格式，除非用户确认接收方接受 BOM。
- 二进制文件、压缩包、Office 文档、图片、数据库文件。
- 需要在低置信度下仍强制转换的任务。

## 原则

1. 使用检测库获取编码和置信度。
2. 默认置信度阈值为 `0.80`。
3. 低于阈值时失败退出。
4. 解码必须使用严格模式。
5. 不使用替换、忽略或吞错字节策略。
6. 输出使用 `utf-8-sig`，即 UTF-8 BOM。
7. 换行统一为 CRLF。
8. 输出后校验 BOM、双 BOM、裸 LF、裸 CR 和 UTF-8 可解码性。

## 推荐脚本

参考实现：`references/to_utf8_bom_crlf.py`

安装依赖：

```bash
pip install chardet
```

执行：

```bash
python references/to_utf8_bom_crlf.py input.txt output.txt
```

调整置信度：

```bash
python references/to_utf8_bom_crlf.py input.txt output.txt --min-confidence 0.85
```

覆盖输出：

```bash
python references/to_utf8_bom_crlf.py input.txt output.txt --overwrite
```

## 流程

1. 读取原始字节。
2. 调用 `chardet.detect` 获取 `encoding` 和 `confidence`。
3. 若无编码结果或置信度不足，失败退出。
4. 对常见检测结果做保守映射：
   - `ascii` → `utf-8`
   - `gb2312` → `gb18030`
   - `gbk` → `gb18030`
   - `iso-8859-1` → `windows-1252`
5. 使用映射后的编码严格解码。
6. 将 `CRLF`、`CR`、`LF` 统一归一为 `LF`。
7. 再将 `LF` 统一转换为 `CRLF`。
8. 使用 `utf-8-sig` 写出。
9. 校验输出格式。

## 验收

输出文件必须满足：

- 文件开头为 `EF BB BF`。
- 没有双 UTF-8 BOM。
- 正文中没有裸 LF。
- 正文中没有裸 CR。
- 可用 `utf-8-sig` 严格解码。
- 日志记录输入路径、输出路径、检测编码、映射编码和置信度。
