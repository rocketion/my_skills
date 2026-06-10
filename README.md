# my_skills

这个仓库用于收纳与维护多套 Skill。

## 目录结构

- `skills/<skill-name>/SKILL.md`：必需，该 Skill 的入口文档。
- `skills/<skill-name>/scripts/`：可选，存放脚本或可执行工具。
- `skills/<skill-name>/references/`：可选，存放参考资料或模板。

## Skills

| 名称 | 简述 | 入口 |
| --- | --- | --- |
| `utf8-bom-crlf-converter` | 将文本文件转换为 UTF-8 with BOM + CRLF，并校验输出文件格式 | `skills/utf8-bom-crlf-converter/SKILL.md` |
| `handoff` | 将长对话或复杂任务整理为 `handoff.md`，作为下一个对话的继续工作重启点 | `skills/handoff/SKILL.md` |

## 新增 Skill 约定

1. 在 `skills/` 下创建独立目录：`skills/<skill-name>/`。
2. 必须提供入口文档：`skills/<skill-name>/SKILL.md`。
3. 如需脚本或可执行工具，放入 `skills/<skill-name>/scripts/`。
4. 如需模板、参考资料或补充说明，放入 `skills/<skill-name>/references/`。
