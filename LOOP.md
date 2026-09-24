# SmartCustomerService Long-Running Engineering Loop

本文件定义本仓库持续推进功能的工程流程。Loop 的目的不是持续产出代码，而是让每项变更都有预先确定的验收标准、独立验证、失败记录和可追溯状态。

## 1. 完成定义

一个 Task 只有同时满足以下条件才能标记为 `ACCEPTED`：

1. 预先冻结的 Acceptance Criteria 全部满足。
2. 所需自动化测试及回归测试通过，失败项有明确归因且不被隐藏。
3. 独立 Verifier 对照 Task、验收标准、diff 和测试证据给出 `PASS`。
4. 文档和 `PROJECT_STATE.md` 已同步，新增失败已记入 `FAILURES.md`。
5. 不存在未处理的 P0/P1 缺陷，也没有把公开参考数据说成公司事实。

代码已写完或测试通过都不单独代表任务完成。Phase 完成、生产部署、破坏性数据操作、权限/安全变更及真实业务写操作仍需项目负责人确认。

## 2. 角色与独立性

- **Planner**：依据 `ROADMAP.md`、`PROJECT_STATE.md`、`FAILURES.md` 和当前仓库选一个最小任务，先写任务范围及验收标准；不在 Planner 阶段改业务代码。
- **Builder**：实现已批准的 Task、补测试并报告变更；只能报告 `IMPLEMENTATION_READY`，不得自我宣布验收通过。
- **Test Agent**：独立执行测试并主动尝试反例、异常路径和回归场景；输出命令、结果和可复现证据。
- **Verifier / Acceptance Agent**：不实现该 Task；在独立上下文中检查原始标准、diff、测试结果、数据边界、安全性和失败历史，只能给出 `PASS`、`FAIL` 或 `BLOCKED`。
- **Human Product Owner**：对阶段验收和明确的人类关卡作最终决定。

Verifier 不得仅凭 Builder 的总结通过任务。优先使用另一个 Codex task/独立审查者；如果当前环境无法提供真正独立的 Reviewer，则标记 `BLOCKED — independent verifier unavailable`，不得把 Builder 自审伪装成独立验收。

## 3. 单轮流程

```text
读取当前仓库状态
  → 选定一个有界 Task
  → 冻结验收标准与测试计划
  → Builder 实现
  → Test Agent 执行并找反例
  → 独立 Verifier 验收
      ├─ FAIL：写入 FAILURES.md，限次修复后重测
      ├─ BLOCKED：记录阻塞和所需的人类动作，停止该 Task
      └─ PASS：同步状态/文档，满足授权与提交规则后提交
  → 判断是否需要阶段级/人工验收
  → 选择下一 Task
```

### 每轮开始必须读取

- `LOOP.md`
- `ROADMAP.md`
- `PROJECT_STATE.md`
- `FAILURES.md`
- `REQUIREMENTS.md` 中与本任务相关的章节
- 当前分支、工作区状态、最近提交及相关测试/迁移/配置

仓库事实优先于历史聊天摘要。不能因历史上下文说某功能已完成，就跳过代码和运行证据检查。

### Task 提案模板

```text
TASK-ID:
Priority: P0 | P1 | P2 | P3 | P4 | P5
目标：
背景/证据：
允许修改范围：
明确不修改：
Acceptance Criteria（编号、可验证）：
测试计划（unit / integration / regression / E2E）：
风险与数据边界：
Human gate：有 / 无，说明
```

没有可验证的 Acceptance Criteria 或范围明显超过单轮时，不开始实现。

## 4. 优先级与范围控制

优先级顺序：P0 数据损坏/安全/服务阻断；P1 当前阶段核心闭环；P2 正确性、可靠性和测试；P3 用户体验；P4 性能/维护性；P5 nice-to-have。

- 一轮只做一个目标，不把“完成整个 Phase”作为单个 Builder Task。
- 超过 15 个文件或跨越多个独立模块时，Planner 必须重新拆分并说明例外理由。
- 同一 Task 最多自动修复 3 轮；之后转 `BLOCKED`，新建根因 Task，不无限打补丁。
- 不为通过测试而删测试、放宽既定标准、屏蔽失败或伪造数据。
- 未经明确授权，不执行生产写入、真实客户数据操作、不可逆迁移、删除数据或外部系统写操作。
- 外部公开目录/价格必须保留来源和 external/reference 标记，不可描述为公司 SKU、库存、正式报价或承诺。

## 5. 测试与验收证据

按风险选择并记录：unit、integration、regression、E2E、performance、security、AI evaluation。至少包含正常路径、边界条件、错误路径和旧功能回归。任何未运行的测试必须明确列为未验证，不得写成通过。

测试报告格式：

```text
命令：
结果：PASS | FAIL | NOT RUN
通过/失败/跳过数量：
关键输出或日志位置：
环境依赖及未覆盖项：
```

Verifier 检查：功能和范围、架构边界、测试质量、迁移可部署性、凭据和权限、外部数据标识、模型事实约束、错误处理、可维护性，以及 `FAILURES.md` 中相似历史问题是否复发。

验收输出必须采用：

```text
Verdict: PASS | FAIL | BLOCKED
Criteria: AC-1 PASS/FAIL — evidence
Tests: evidence and gaps
Risks / required fixes:
Failure record: ID or none
```

## 6. 失败记录规则

每次验收失败、测试回归、数据/部署阻塞或安全问题都登记在 `FAILURES.md`，类型限定为 `FUNCTIONAL`、`ARCHITECTURE`、`TEST`、`DATA`、`SECURITY`、`PERFORMANCE`、`AI_BEHAVIOR`、`UX`、`DEPLOYMENT`。

记录至少包含 ID、Task、日期、阶段、类型、失败描述、根因（未知则写 `TBD`）、证据、修复/下一步、回归测试、状态。相同根因连续失败 3 次，必须转为 `ROOT_CAUSE_TASK`，不能继续叠加局部补丁。关闭记录要附验证证据，历史记录不得删除。

## 7. 当前阶段的专项关卡

### Phase 3 — Vision Product Search

阶段验收项必须逐项有证据：

- [ ] 图片上传及大小/格式/损坏输入错误处理
- [ ] CLIP image/text embedding 与维数、模型版本一致性
- [ ] pgvector migration、索引及 SKU 外键/关联
- [ ] 商品图片向量成功入库，索引脚本可安全续跑
- [ ] 上传图查询返回真实商品 SKU、商品卡片及有效购买入口
- [ ] 每 SKU 多图策略
- [ ] 低置信度拒绝/澄清策略；不得无条件强推 Top-3
- [ ] 非珠宝、模糊、错误类别及低相似度拒绝测试
- [ ] 至少 100 张有标注评估图片；报告 Top-1、Top-3、拒识指标及数据划分
- [ ] 记录延迟、吞吐、资源消耗和数据库/模型不可用行为
- [ ] 关键路径集成及前端 E2E 回归通过

只有全部必需项通过独立验收并经产品负责人接受，才能将 Phase 3 标记为 `DONE`。评估数据必须有可追溯来源和许可信息；不能把未经验证的相似度数值直接宣称为概率置信度。

### Phase 4 — Knowledge RAG

阶段验收应覆盖文档导入与来源/版本追踪、chunking、embedding、pgvector、hybrid Top-K、可选 rerank、无答案策略、回答的来源支持、至少 100 条带依据 QA evaluation、幻觉/拒答评估、更新/删除与权限隔离。无可用证据时客服应澄清或拒答，不得编造企业政策。

## 8. Commit 与远端规则

- 只有测试通过、独立验收 `PASS`、状态文档同步后，Task 才能进入可提交状态。
- Commit 格式：`SmartCustomerService: <中文任务摘要>`。
- 本 Loop 不推断用户授权去 push、发布、部署或修改远端；只有用户明确要求时才执行对应外部动作。
- 提交前只暂存本项目且与任务相关的明确文件路径；不得使用会纳入无关文件的全量暂存方式。

## 9. 每轮交付格式

```text
LOOP RESULT
Task: ...
Status: ACCEPTED | IMPLEMENTATION_READY | FAIL | BLOCKED
Implementation: ...
Tests: ...
Independent acceptance: PASS | FAIL | BLOCKED — evidence
Failures: FAIL-xxxx / none
State/doc updates: ...
Next task: ...
Human action required: ... / none
```

## 10. 项目完成与人工关卡

生产就绪不是删除所有 TODO。至少需要关键端到端验收、无 P0/P1、可重复数据库部署、备份恢复演练、权限与密钥安全、日志/监控、Docker 部署、真实模型和 PostgreSQL 联调、可用的人工接管、AI evaluation 达标和完整部署文档。生产部署及涉及支付/正式报价/真实客户数据/权限/删除数据/外部写操作必须由项目负责人批准。

本流程描述的是执行约束，不声称仓库内有一个会在 Codex 关闭后自行运行的后台 Agent。每轮必须由被触发的 Codex task 按本文件读取仓库、执行、留痕和交接。
