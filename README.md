# my_skills

这个仓库用于收纳与维护多套 Agent Skill（每个 Skill 以 `SKILL.md` 为入口文档）。

## 目录结构

- `skills/<skill-name>/SKILL.md`：该 Skill 的入口说明（使用方式、产物、最小流程、唯一规则源等）。
- `skills/<skill-name>/references/`：规则源、模板与约束（供 `SKILL.md` 引用）。
- `skills/<skill-name>/agents/`：可选的 agent/interface 配置文件。

## Skills

| 名称 | 简述 | 入口 |
| --- | --- | --- |
| `doc-ssot-flow` | 文档单一事实源（SSOT）执行工作流：按规则完成 `doc/` 初始化、任务文档维护与 `project.md` 闭环回写 | `skills/doc-ssot-flow/SKILL.md` |

## 新增 Skill 约定

1. 在 `skills/` 下创建新目录：`skills/<skill-name>/`。
2. 提供入口文档：`skills/<skill-name>/SKILL.md`（保持内容精炼，细则放到 `references/`）。
3. 如需规则/模板/约束，放到 `skills/<skill-name>/references/` 并在 `SKILL.md` 中引用。
