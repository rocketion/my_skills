# my_skills

这个仓库用于收纳与维护多套 Agent Skill（每个 Skill 以 `SKILL.md` 为入口文档）。

## 目录结构

- `skills/<skill-name>/SKILL.md`：该 Skill 的入口说明，负责定义定位、适用场景、执行原则与 SOP。
- `skills/<skill-name>/references/`：模板、参考资料与补充说明，供 `SKILL.md` 引用。
- `skills/<skill-name>/agents/`：可选的 agent/interface 配置文件。

## Skills

| 名称 | 简述 | 入口 |
| --- | --- | --- |
| `doc-driven-dev` | 以文档驱动开发：在 `SKILL.md` 中定义 `project/task` 主线与 `finding` 并行记录规则，并要求用 `project.md` 承载项目级规则、介绍、目标与设计 | `skills/doc-driven-dev/SKILL.md` |

## 新增 Skill 约定

1. 在 `skills/` 下创建新目录：`skills/<skill-name>/`。
2. 提供入口文档：`skills/<skill-name>/SKILL.md`，用于定义该 Skill 的定位、原则、流程与主要产物。
3. 如需模板、参考资料或补充说明，放到 `skills/<skill-name>/references/` 并在 `SKILL.md` 中引用。
