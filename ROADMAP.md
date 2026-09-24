# Project Roadmap

状态含义：`DONE` 有验收证据；`ACTIVE` 正在推进；`BLOCKED` 等待明确前置条件；`PLANNED` 尚未开始。代码存在不等于阶段验收通过。

| Phase | 范围 | 状态 | 说明 |
|---|---|---|---|
| 1 | 客服 Runtime、会话、模型 Tool Calling、Widget、基础人工转接 | DONE* | 现有实现与回归测试覆盖基础闭环；如需生产级验收，仍需独立重新验收。 |
| 2 | 产品/价格/知识/视觉数据接入、PostgreSQL Repository | ACTIVE | Repository、公开数据导入和迁移已存在；目标环境导入/权限/恢复流程仍需部署证据。 |
| 3 | Vision 商品图片向量检索并闭环至 SKU | ACTIVE | SKU 关联实现已提交；数据库 migration/向量实际索引和 100 图评估等仍未完成验收。 |
| 4 | Knowledge RAG | PLANNED | 当前是关键词/PostgreSQL Knowledge Search V1；未达到完整 RAG 验收标准。 |
| 5 | Pricing / 询价闭环 | PLANNED | 公开参考价与 Mock/查询能力不等于公司正式报价、审批或询价流程。 |
| 6 | Human Support Console | PLANNED | 当前有转人工标记/入口基础；队列、分配、接管、AI 暂停/恢复及审计闭环待建设。 |
| 7 | Admin 管理后台 | ACTIVE | 模型/能力配置已有基础界面；权限、操作审计及生产安全仍需评估。 |
| 8 | 客户账户与长期记忆 | PLANNED | 当前 Session 存储能力不等于完整客户账户/长期记忆产品。 |
| 9 | Observability / Security | PLANNED | 需补充结构化日志、指标、告警、权限和安全验收。 |
| 10 | Production Deployment | PLANNED | Docker 配置存在；生产部署、备份恢复、监控和真实依赖联调需人工批准与验收。 |

`DONE*` 表示当前功能范围已有基础实现，不替代本仓库建立 Loop 后的阶段级独立验收。只有 `LOOP.md` 规定的验收材料齐全并通过后，Planner 才可把阶段状态改为 `DONE`。

## 近期顺序

1. 处理 `FAILURES.md` 中 Vision PostgreSQL 认证阻塞；由项目负责人在本地配置/恢复数据库凭据，不将密码写进仓库或日志。
2. 在有权限的本地/目标数据库应用迁移并完成产品图向量索引，记录数量、跳过/失败 SKU 和可复现命令。
3. 完成 Vision 置信度/拒识策略、带标注评估集及集成/E2E 验收，按 `LOOP.md` 独立验收 Phase 3。
4. 再拆分 Phase 4 RAG 的文档摄取、分块、向量/混合检索、出处和无答案策略任务。
