---
name: encoding-normalizer
description: 将未知编码的文本文件按检测置信度转换为 UTF-8 BOM + CRLF，低置信度或严格解码失败时拒绝转换。
---

# Encoding Normalizer

## 1. 定位

这是一个面向裸文本文件交付的编码归一化 skill。它处理的问题是：给定一个编码未知的输入文件，基于编码检测结果和置信度阈值，输出 `UTF-8 with BOM + CRLF`。

该 skill 不追求“无条件转换成功”，而是追求可审计、可拒绝、尽量避免误转。若检测置信度不足、严格解码失败或输入不像文本文件，应停止转换并报告原因。

## 2. 适用场景

- 用户提供单个或一批未知编码的文本文件。
- 目标交付格式明确为 `UTF-8 with BOM + CRLF`。
- 文件需要在 Windows 工具链、裸文件交换或人工打开场景中更稳定地识别为 UTF-8。
- 用户接受“低置信度失败”而不是强行吞错字节。

## 3. 不适用场景

- JSON、源码、协议 payload 或其他明确禁止/不推荐 BOM 的格式，除非用户确认目标系统接受 UTF-8 BOM。
- 二进制文件、压缩包、Office 文档、图片、数据库文件等非纯文本输入。
- 用户要求在编码无法可靠判断时仍强制转换。
- 需要保留原始换行风格而不是统一为 CRLF 的场景。

## 4. 核心原则

1. 检测必须带置信度阈值；默认阈值建议为 `0.80`。
2. 检测结果低于阈值时必须失败，不应猜测后继续转换。
3. 解码必须使用严格模式，不能使用 `replace`、`ignore` 或吞坏字节策略。
4. 输出统一为 `UTF-8 with BOM + CRLF`。
5. 对中文检测结果可做保守映射：`GB2312`、`GBK` 统一按 `GB18030` 解码。
6. 对 ASCII 检测结果可按 UTF-8 处理，因为 ASCII 是 UTF-8 的子集。
7. 转换结果必须可验证：有 UTF-8 BOM、无裸 LF、可严格按 UTF-8 解码。

## 5. 推荐实现

参考脚本：`references/to_utf8_bom_crlf.py`

脚本行为：

```text
输入文件
→ chardet 检测 encoding + confidence
→ 低于 min-confidence 则失败
→ 按映射后的编码严格解码
→ 将 CRLF / CR / LF 全部归一化为 CRLF
→ 写出 UTF-8 BOM 字节流
→ 可选执行输出校验
```

安装依赖：

```bash
pip install chardet
```

基本用法：

```bash
python references/to_utf8_bom_crlf.py input.txt output.txt
```

调整置信度阈值：

```bash
python references/to_utf8_bom_crlf.py input.txt output.txt --min-confidence 0.85
```

覆盖输出文件：

```bash
python references/to_utf8_bom_crlf.py input.txt output.txt --overwrite
```

## 6. SOP

### 6.1 输入确认

1. 确认输入目标是文本文件，不是二进制容器。
2. 明确输出是否确实需要 BOM；若文件格式规范禁止 BOM，先停下并说明风险。
3. 明确目标换行是 CRLF。

### 6.2 转换执行

1. 读取原始字节，不要先用系统默认编码打开文件。
2. 调用检测库获取 `encoding` 和 `confidence`。
3. 若无编码结果或置信度低于阈值，失败退出。
4. 对检测结果执行有限映射：
   - `ascii` → `utf-8`
   - `gb2312` → `gb18030`
   - `gbk` → `gb18030`
   - `iso-8859-1` → `windows-1252`
5. 使用映射后的编码严格解码。
6. 将所有换行归一为 LF，再统一转换为 CRLF。
7. 使用 `utf-8-sig` 编码写出，保证输出带 UTF-8 BOM。

### 6.3 验收检查

转换后至少检查：

1. 文件开头是 `EF BB BF`。
2. 文件可用 `utf-8-sig` 严格解码。
3. 正文中不存在裸 LF。
4. 正文中不存在裸 CR。
5. 未出现双 UTF-8 BOM。
6. 日志中记录检测编码、映射后编码、置信度、输入路径、输出路径。

## 7. 失败策略

遇到以下情况应失败而不是继续：

- 检测库没有返回编码。
- `confidence < min-confidence`。
- 严格解码抛出 `UnicodeDecodeError`。
- 输出文件已存在且未显式允许覆盖。
- 输出校验失败。

失败信息需要包含检测结果、置信度和失败阶段，方便人工确认编码后重试。

## 8. 常见风险

- 短文本、纯数字、英文标点较多的文件可能置信度不足。
- `Windows-1252`、`ISO-8859-1`、`Windows-1254` 等单字节编码容易互相误判。
- `GBK`、`GB2312`、`GB18030` 的检测结果通常可以按 `GB18030` 解码以扩大覆盖范围。
- BOM 适合裸文本交付，但不应无条件用于所有上层格式。
