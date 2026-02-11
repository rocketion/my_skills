---
name: doc-ssot-flow
description: 文档驱动的 SSOT 维护技能。用于创建/更新 doc/project.md 与 doc/ 任务文档体系，确保变更闭环回写。
---

# Doc-SSOT-Flow

## 概述

以 references/collab_rules.md 为唯一规则来源，执行文档驱动开发并维护项目单一事实源（SSOT）。任何流程与输出必须与规则文件一致，不在此重复规则细节。

## 工作流

1. 读取并遵循 references/collab_rules.md（后续所有动作以其为准）。
2. 确认 doc/ 是否存在；如不存在，先创建 doc/。
3. 若无 doc/project.md，按 references/collab_rules.md 的模板创建并替换 TODO。
4. 若已有 doc/project.md，仅按规则中的结构与约束进行增量更新。
5. 执行过程中必须采用任务工作模式：维护 doc/tasks.md 清单，并以 doc/task-xxx.md 进行迭代记录。

## 闭环规则

1. 以 references/collab_rules.md 的闭环要求为准；此处仅补充不重复的提醒。
2. 任何开发工作若改变模块职责、接口、数据流、依赖、权限或状态机，必须回写 doc/project.md。
3. 回写完成前，禁止宣告任务 DONE。
4. 若单文件修改超过 30% 且涉及核心架构，先说明理由并获得明确批准。

## 输出要求

1. 全中文。
2. 文档为 UTF-8 无 BOM。
3. 仅记录最终方案与原因，避免过程性叙述与空泛形容词。

## 资源

### references/
- collab_rules.md：协作规范与文档约束。

### assets/
