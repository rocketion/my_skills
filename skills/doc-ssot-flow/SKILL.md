---
name: doc-ssot-flow
description: 文档单一事实源（SSOT）执行工作流：按规则完成 doc/ 初始化、任务文档维护与 project.md 闭环回写。
---

# Doc-SSOT-Flow

## 目标

- 用 `doc/` 作为单一事实源（SSOT）：先落文档，再改代码。
- 保持 `doc/project.md`、任务文档与代码变更一致（闭环回写）。

## 何时使用

- 新项目初始化、或引入新模块/子系统。
- 开始一个可交付任务（`task-xxx`）。
- 影响模块职责/接口/数据流/依赖/权限/状态机等全局规则。

## 产物

- `doc/project.md`：全局技术基准（结构与约束见规则源）。
- `doc/tasks.md`：任务注册表（仅索引与状态）。
- `doc/task-xxx.md`：单任务工作区（以 Issue-xxx 为单位追加记录）。

## 最小流程

1. 阅读并遵循唯一规则源 `references/ssot_rules.md`。
2. 初始化 `doc/`，补齐 `doc/project.md` 与 `doc/tasks.md`。
3. 新建/更新 `doc/task-xxx.md`，拆解 Issue 并按 Issue 记录测试与结果。
4. 开发中持续同步 `doc/task-xxx.md`；涉及全局变更则同步回写 `doc/project.md`。

## 参考（SSOT）

- `references/ssot_rules.md`
