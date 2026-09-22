# AI 智能客服系统需求文档

> 项目名称：AI Customer Service  
> 仓库建议：`ai-customer-service`  
> 文档版本：v0.2  
> 项目定位：网站内嵌式 AI 智能客服  
> 目标行业：不锈钢珠宝制造 / 外贸型制造企业  
> 当前阶段：一期需求定义

---

## 1. 项目背景

公司拥有大量珠宝产品、产品图片、产品规格、历史报价、知识资料等业务数据。

当前希望在公司网站中增加一个 AI 对话客服，使网站访客能够像与真人客服沟通一样，通过自然语言完成：

- 产品咨询
- 产品规格咨询
- 找款 / 相似款咨询
- 材质、电镀、尺寸、MOQ 等咨询
- 基础价格咨询
- 公司及业务知识咨询
- 连续追问
- 必要时转人工客服

本项目的核心不是为客户提供一套“AI 工具箱”，而是构建一个能够理解客户、记住上下文、主动引导并调用后台能力完成服务的 AI 客服。

客户只看到自然的对话体验。

数据库、RAG、图片搜索、Jev、Tool Calling 等均属于客服内部能力，不直接暴露给客户。

---

## 2. 项目边界

### 2.1 一期包含

一期只建设“网站 AI 智能客服”。

入口：

```text
公司网站
   ↓
AI 客服聊天窗口
```

一期支持：

1. 文本对话
2. 图片上传
3. 多轮会话
4. 产品咨询
5. 产品规格查询
6. 图片找款 / 相似款搜索
7. MOQ 咨询
8. 基础价格/询价咨询
9. 企业知识问答
10. 客服主动澄清和引导
11. 无法处理时转人工
12. 后台能力独立配置

### 2.2 一期明确不包含

以下功能不属于本项目一期：

- 邮件自动读取
- 邮件自动回复
- Gmail / Outlook 接入
- WhatsApp 接入
- CRM 自动跟单
- ERP 自动操作
- 自动创建订单
- 自动退款
- 自动修改库存
- 多 Agent 协作平台
- 通用 Agent 开发平台
- 面向客户暴露数据库、RAG 或工具调用界面

邮件系统后续作为独立项目建设，通过标准接口与本项目共享产品、知识、报价等底层能力。

---

## 3. 产品目标

AI 客服需要表现得像“一个了解公司产品和业务规则的客服人员”，而不是搜索引擎或工具调用器。

核心能力分为三部分：

```text
感知 Perception
        ↓
记忆 Memory
        ↓
对话规划 Dialogue Planning
        ↓
客服动作
        ↓
自然语言回复
```

后台工具仅在客服需要事实信息时调用：

```text
AI 客服
   ↓
判断是否需要查询
   ↓
后台能力
├── 产品数据库
├── 图片搜索
├── 报价数据
└── RAG 知识库
   ↓
得到事实
   ↓
AI 客服继续对话
```

---

## 4. 核心原则

### 4.1 客服优先

系统第一目标是完成客服服务，而不是展示 AI 技术。

客户不需要知道：

- 调用了什么 Tool
- 使用了什么数据库
- 是否使用 RAG
- 是否使用向量搜索
- 是否经过 Jev
- 使用了哪个模型

### 4.2 先理解，再查询

客户说：

> I am looking for simple stainless steel men's rings.

系统不应立即返回数据库中所有戒指。

客服应该先理解需求，并根据缺失信息自然继续询问，例如：

> Do you prefer silver, gold, or black finish?

当信息足够后，再调用产品搜索。

### 4.3 事实不能由模型猜测

以下内容必须来自真实数据源：

- SKU
- 材质
- 尺寸
- 电镀
- MOQ
- 产品价格
- 产品图片
- 产品状态

LLM 只负责理解、规划和表达，不负责凭空生成业务事实。

### 4.4 后台能力模块化

数据库、RAG、图片搜索、报价、模型等均独立配置。

任何一个模块替换后，不应影响客服核心逻辑。

---

# 5. 系统总体架构

```text
┌──────────────────────────────────────────┐
│              Website Frontend            │
│                                          │
│              AI Chat Widget              │
│         文本 / 图片 / 会话展示            │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│                Chat API                  │
│                                          │
│ Session / Message / Streaming / Auth     │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│          AI Customer Service Core        │
│                                          │
│  Perception                              │
│       ↓                                  │
│  Memory                                  │
│       ↓                                  │
│  Dialogue Planning                       │
│       ↓                                  │
│  Response Generation                     │
└────────────────────┬─────────────────────┘
                     │
             需要后台事实时
                     │
                     ▼
┌──────────────────────────────────────────┐
│              Capability Layer            │
│                                          │
│ Product Service                          │
│ Vision Search                            │
│ Pricing Service                          │
│ Knowledge / RAG                          │
│ Human Handoff                            │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│                 Data Layer               │
│                                          │
│ Product DB                               │
│ Vector DB                                │
│ Knowledge Base                           │
│ Price Data                               │
│ Object Storage                           │
└──────────────────────────────────────────┘
```

---

# 6. 核心模块一：感知 Perception

## 6.1 目标

感知层回答：

> 客户现在表达了什么？

感知层只负责理解当前输入，不负责解决问题。

## 6.2 输入

一期输入类型：

```text
Text
Image
Session Context
```

后续可扩展：

```text
Audio
File
Video
```

## 6.3 感知内容

需要识别：

### 用户意图

一期至少支持：

```text
general_chat            普通交流
product_search          找产品
similar_product_search  找相似款
product_question        产品咨询
spec_question           规格咨询
material_question       材质咨询
plating_question        电镀咨询
size_question           尺寸咨询
moq_question            MOQ咨询
price_question          价格咨询
recommendation          产品推荐
company_question        公司/业务咨询
human_service           请求人工
unknown                 无法识别
```

### 业务实体

一期需要提取：

```text
SKU
Product Category
Material
Plating
Color
Size
Quantity
MOQ
Style
Gender
Stone
Target Price
```

### 对话状态

感知还需要识别：

```text
是否为追问
是否存在指代
是否缺少必要信息
是否表达不满意
是否请求人工
```

例如：

```text
Customer:
How much is the second one?
```

结合上下文应识别：

```json
{
  "intent": "price_question",
  "reference": {
    "type": "previous_product",
    "position": 2
  }
}
```

---

## 6.4 感知输出

统一结构：

```json
{
  "intent": "product_search",
  "entities": {
    "category": "ring",
    "material": "316L",
    "style": "simple"
  },
  "has_image": false,
  "references": [],
  "missing_information": [
    "color"
  ],
  "confidence": 0.94
}
```

---

# 7. 核心模块二：记忆 Memory

## 7.1 目标

Memory 回答：

> 当前这次客服对话已经知道什么？

一期优先做好“会话记忆”，长期客户画像不是第一优先级。

---

## 7.2 Session Memory

每个聊天 Session 保存：

```text
当前客户表达的需求
已确认的条件
候选产品
当前正在讨论的产品
前几轮消息
客服已经问过的问题
客服已经给过的答案
尚未解决的问题
```

例如：

```json
{
  "session_id": "S001",
  "requirements": {
    "category": "ring",
    "gender": "men",
    "style": "simple",
    "material": "316L",
    "plating": "black_pvd",
    "quantity": 500
  },
  "candidate_products": [
    "R1001",
    "R1002",
    "R1003"
  ],
  "selected_product": "R1002",
  "unresolved": []
}
```

---

## 7.3 指代理解

必须支持：

```text
the first one
the second one
this one
that design
same material
same color
similar one
```

例如：

```text
AI:
I found:
1. R1001
2. R1002
3. R1003

Customer:
How much is the second one?
```

系统必须解析：

```text
second one = R1002
```

---

## 7.4 长对话压缩

不允许无限把完整聊天历史发送给 LLM。

需要逐步形成：

```text
Recent Messages
+
Conversation Summary
+
Current Requirements
+
Current Product Context
```

例如：

```json
{
  "summary": "Customer is looking for simple men's 316L rings with black PVD.",
  "requirements": {
    "quantity": 500
  },
  "current_product": "R1002"
}
```

---

## 7.5 Customer Memory

二期能力。

登录客户可以建立长期记忆，例如：

```text
常买产品类别
常用材料
常用颜色
常见数量
语言偏好
历史咨询
```

但一期系统不得依赖 Customer Memory 才能正常工作。

---

# 8. 核心模块三：对话规划 Dialogue Planning

## 8.1 目标

Planner 回答：

> 作为客服，下一步应该怎么服务这个客户？

Planner 不直接决定 SQL、向量数据库或具体 API。

Planner 只产生“客服动作”。

---

## 8.2 客服动作类型

一期支持：

```text
answer_directly
ask_clarification
ask_requirement
search_product
search_similar_product
get_product_information
get_price_information
search_knowledge
recommend_product
request_human_handoff
finish
```

---

## 8.3 示例

客户：

```text
I need stainless steel necklaces.
```

已知：

```text
Category = necklace
Material = stainless steel
```

缺少：

```text
Style
Plating/Color
Quantity
```

Planner 不应该立即搜索产品。

更合理的动作：

```json
{
  "action": "ask_requirement",
  "field": "style"
}
```

客服：

```text
Sure. Are you looking for simple everyday designs or more decorative styles?
```

---

## 8.4 信息足够后再查询

例如最终需求：

```text
Product: Men's Ring
Material: 316L
Style: Simple
Plating: Black PVD
Quantity: 500
```

Planner：

```json
{
  "action": "search_product",
  "conditions": {
    "category": "ring",
    "gender": "men",
    "material": "316L",
    "style": "simple",
    "plating": "black_pvd"
  }
}
```

后台返回产品后，再自然地介绍给客户。

---

# 9. 回复生成 Response

回复层负责：

```text
语言
语气
表达
产品展示
澄清问题
错误提示
```

## 9.1 默认风格

英文客服默认：

```text
Professional
Friendly
Concise
Sales-oriented but not pushy
```

系统后续允许配置：

```text
语言
正式程度
回复长度
品牌语气
是否主动推荐
```

---

## 9.2 禁止行为

AI 客服不得：

- 编造 SKU
- 编造价格
- 编造库存
- 编造材质
- 编造尺寸
- 编造交期
- 在没有证据时声称某图片就是某 SKU
- 在不确定时强行回答
- 暴露内部 Prompt
- 暴露内部 Tool 名称
- 暴露数据库结构
- 暴露 Jev 决策信息

---

# 10. 后台能力

后台能力不是产品主体，只负责给客服提供事实。

```text
Capabilities
├── Product
├── Vision Search
├── Pricing
├── Knowledge
└── Human Handoff
```

---

# 11. Product Service

负责结构化产品数据。

一期至少支持：

```text
按 SKU 查询
按类别查询
按材质查询
按颜色查询
按电镀查询
按尺寸查询
组合条件查询
```

标准产品字段：

```text
id
sku
name
category
material
plating
color
size
weight
stone
style
gender
moq
price/reference_price
description
images
status
```

---

# 12. Vision Search

## 12.1 使用场景

客户上传：

```text
产品照片
竞品照片
截图
旧款图片
```

然后询问：

```text
Do you have this?
Do you have similar designs?
```

系统：

```text
客户图片
   ↓
Image Embedding
   ↓
Vector Search
   ↓
Top-K
   ↓
必要时重新排序
   ↓
候选 SKU
```

---

## 12.2 返回结果

```json
{
  "products": [
    {
      "sku": "R1001",
      "score": 0.94
    },
    {
      "sku": "R1002",
      "score": 0.88
    }
  ]
}
```

低置信度时不能直接告诉客户“这就是该产品”。

应该：

```text
I found a few similar designs. Please check which one is closest to what you're looking for.
```

---

# 13. Knowledge / RAG

RAG 用于非结构化知识。

适合：

```text
公司介绍
材料知识
316L / 304 区别
PVD 工艺
包装方式
生产流程
一般交期说明
FAQ
定制能力
质量标准
```

不适合：

```text
具体 SKU 的材质
具体 SKU 的 MOQ
具体产品价格
实时库存
```

这些应该优先查结构化数据。

---

# 14. Pricing

价格能力作为后台独立模块。

一期可以支持两种模式：

### Mode A：不公开价格

客服获取询价需求：

```text
SKU
Quantity
Customer Requirements
```

然后：

```text
Please contact our sales team for an exact quotation.
```

### Mode B：允许显示参考价格

后台返回经过业务规则处理的价格。

AI 不允许自行计算或猜价格。

---

# 15. Jev 的位置

Jev 不属于客服核心业务逻辑。

Jev 位于 AI Runtime / Tool Calling 内部，用于具体工具选择。

```text
Dialogue Planner
      ↓
客服动作：
get_product_information
      ↓
Executor / LLM Runtime
      ↓
Jev
      ↓
Tool Selection
      ↓
Product Tool
```

职责：

```text
Planner：
客服下一步应该做什么？

Jev：
完成这个动作应该调用哪个后台工具？
```

Jev 不直接决定客服要问客户什么，也不直接生成最终回复。

---

# 16. 模块独立配置要求

所有后台能力必须支持独立启用 / 禁用。

示例：

```yaml
customer_service:
  perception:
    enabled: true

  memory:
    session:
      enabled: true
    customer:
      enabled: false

  planning:
    enabled: true

  capabilities:
    product:
      enabled: true

    vision_search:
      enabled: true

    pricing:
      enabled: false

    knowledge_rag:
      enabled: true

  tool_calling:
    jev:
      enabled: true
```

一期即使关闭某个能力，系统也必须优雅降级。

例如关闭 Pricing：

```text
Customer:
How much?

AI:
I can help you confirm the product and quantity first, then our sales team can provide an exact quotation.
```

---

# 17. 配置管理

一期需要支持：

```text
LLM Provider
LLM Model
Temperature
System Prompt
Response Language
Session Memory Length
Summary Threshold
RAG Top-K
Vision Top-K
Vision Minimum Confidence
Enabled Capabilities
Human Handoff Rule
```

后续可增加可视化管理后台。

---

# 18. Tool 接口标准

后台 Tool 统一接口。

输入：

```json
{
  "action": "get_product",
  "arguments": {},
  "context": {}
}
```

输出：

```json
{
  "success": true,
  "data": {},
  "confidence": 1.0,
  "sources": [],
  "error": null
}
```

必须统一处理：

```text
成功
无结果
多结果
低置信度
超时
数据源异常
权限错误
```

---

# 19. 数据存储建议

一期建议：

```text
PostgreSQL
├── sessions
├── messages
├── products
├── product_images
├── customer_service_config
└── tool_logs

pgvector / Vector DB
├── product_image_embedding
└── knowledge_embedding

Object Storage
├── product_images
└── customer_uploaded_images

Redis
├── session cache
├── temporary state
└── rate limiting
```

---

# 20. 核心数据模型

## Session

```text
id
user_id
status
language
created_at
updated_at
summary
```

## Message

```text
id
session_id
role
content
message_type
created_at
```

## ConversationState

```text
session_id
current_intent
requirements
candidate_products
selected_product
missing_information
last_action
```

## Product

```text
id
sku
name
category
material
plating
color
size
weight
style
gender
moq
price
description
status
```

---

# 21. API 需求

一期核心接口：

```text
POST /api/chat/session
创建会话

POST /api/chat/message
发送消息

GET /api/chat/session/{id}
读取会话

POST /api/chat/upload-image
上传图片

POST /api/chat/handoff
请求人工客服
```

建议聊天接口支持 Streaming。

---

# 22. 网站 Chat Widget

一期至少具备：

```text
右下角悬浮入口
展开 / 收起
文本输入
图片上传
消息列表
产品卡片
加载状态
流式输出
重新发送
转人工入口
```

产品搜索结果以卡片展示：

```text
[Image]

SKU: R1001
316L Stainless Steel
Black PVD

[View Product]
```

不要显示：

```text
ProductTool Success
Vector Score
SQL Result
Jev Decision
```

---

# 23. 人工接管

出现以下情况，应允许转人工：

```text
客户主动要求人工
连续无法理解
数据源连续失败
图片无法可靠匹配
价格需要人工确认
敏感投诉
AI 无法确认事实
```

一期至少需要：

```text
标记当前 Session 为 human_required
保留完整会话
向客户显示人工联系提示
```

真正的在线坐席系统可以二期实现。

---

# 24. 日志与可观察性

后台至少记录：

```text
session_id
message_id
intent
planner_action
tool_call
tool_result
latency
token_usage
model
error
human_handoff
```

日志用于：

```text
查错
评估客服效果
优化 Prompt
优化产品数据
发现高频问题
```

客户界面不可显示内部日志。

---

# 25. 一期关键场景

## 场景 A：普通产品咨询

```text
Customer:
Do you sell stainless steel bracelets?

AI:
Yes. We offer a range of stainless steel bracelets.
Are you looking for men's, women's, or unisex designs?
```

---

## 场景 B：需求逐步收集

```text
Customer:
I need rings.

AI:
Sure. Are you looking for men's, women's, or unisex rings?

Customer:
Men's.

AI:
Do you prefer silver, gold, black, or another finish?

Customer:
Black, simple style.

AI:
Got it. Do you have a preferred material, such as 316L stainless steel?
```

---

## 场景 C：图片找款

```text
Customer:
Do you have something like this?

[image]

AI:
I found several similar designs. Here are the closest options...
```

---

## 场景 D：连续追问

```text
AI:
1. R1001
2. R1002
3. R1003

Customer:
What material is the second one?

AI:
R1002 is made from 316L stainless steel.

Customer:
MOQ?

AI:
The MOQ for R1002 is 100 pcs.
```

必须保证第二、第三轮不丢失当前产品上下文。

---

## 场景 E：知识咨询

```text
Customer:
What is the difference between 304 and 316L?

AI:
...
```

走 Knowledge / RAG。

---

## 场景 F：信息不足

```text
Customer:
How much?

AI:
Which product are you asking about?
```

不能随意猜产品。

---

# 26. 一期性能目标

建议目标：

```text
普通对话首 Token：< 2 秒
结构化产品查询：< 2 秒
RAG 查询：< 3 秒
图片搜索：< 4 秒
```

以上为目标值，不作为绝对架构限制。

---

# 27. 一期质量目标

重点评估：

```text
意图识别准确率
业务实体抽取准确率
多轮指代正确率
产品事实准确率
产品搜索 Top-K 命中率
RAG 有依据回答率
幻觉率
转人工准确性
平均响应时间
```

---

# 28. 安全要求

系统不得：

```text
输出后台密钥
输出数据库连接信息
泄露其他客户信息
泄露内部价格规则
执行未经授权的写操作
把一位客户的 Session Memory 带到另一位客户
```

所有 Session 必须隔离。

客户上传图片需要：

```text
类型校验
大小限制
安全存储
过期策略
```

---

# 29. 推荐项目结构

```text
ai-customer-service/
│
├── README.md
├── REQUIREMENTS.md
│
├── frontend/
│   └── chat-widget/
│
├── backend/
│   └── app/
│       ├── api/
│       ├── customer_service/
│       │   ├── perception/
│       │   ├── memory/
│       │   ├── dialogue/
│       │   ├── response/
│       │   └── handoff/
│       │
│       ├── runtime/
│       │   ├── llm/
│       │   ├── jev/
│       │   └── tool_calling/
│       │
│       ├── capabilities/
│       │   ├── product/
│       │   ├── vision/
│       │   ├── pricing/
│       │   └── knowledge/
│       │
│       ├── connectors/
│       │   ├── product_db/
│       │   ├── vector_db/
│       │   └── external_api/
│       │
│       ├── models/
│       └── config/
│
├── tests/
│   ├── conversation/
│   ├── perception/
│   ├── memory/
│   ├── product/
│   ├── vision/
│   └── rag/
│
└── docs/
```

重点：

```text
customer_service/
```

是项目主体。

```text
runtime/
capabilities/
connectors/
```

只是支持客服工作的后台基础设施。

---

# 30. 开发阶段

## Phase 1：客服最小闭环

实现：

```text
Chat Widget
Text Chat
Session
Perception
Session Memory
Dialogue Planning
LLM Reply
```

要求：

即使暂时没有产品库，也必须能完成正常连续客服交流。

---

## Phase 2：产品能力

加入：

```text
Product Service
Product DB
产品卡片
规格查询
MOQ 查询
```

---

## Phase 3：图片找款

加入：

```text
图片上传
Image Embedding
Vector Search
Top-K
产品候选
```

---

## Phase 4：知识库

加入：

```text
Knowledge RAG
FAQ
公司知识
材质/工艺知识
引用来源
```

---

## Phase 5：价格能力

加入：

```text
Pricing Service
报价规则
是否允许公开价格
价格权限控制
```

---

## Phase 6：优化

加入：

```text
Jev Tool Calling
Prompt Evaluation
Memory Compression
模型切换
性能优化
Observability
```

---

# 31. Phase 1 验收标准

一期第一阶段必须通过：

### 对话

- [ ] 客户可在网站打开客服窗口
- [ ] 客户可发送文本
- [ ] AI 支持流式回复
- [ ] 同一 Session 支持连续对话

### 感知

- [ ] 能识别基础客服意图
- [ ] 能抽取基本产品需求
- [ ] 信息不足时能够发现缺失字段

### 记忆

- [ ] 能记住当前会话需求
- [ ] 不重复询问已经确认的信息
- [ ] 能正确理解 `first one / second one / this one` 等上下文引用

### 规划

- [ ] 能选择直接回答
- [ ] 能选择继续询问
- [ ] 能选择澄清
- [ ] 能决定何时需要后台查询
- [ ] 能决定何时应该转人工

### 回复

- [ ] 回复自然
- [ ] 回复符合客服身份
- [ ] 不暴露内部技术组件
- [ ] 不编造业务事实

---

# 32. 最终定位

本项目不是：

```text
AI 搜索工具
AI 数据库工具
RAG Demo
Agent 平台
Tool Calling Demo
```

本项目是：

```text
一个部署在企业网站上的 AI 智能客服。
```

其核心循环为：

```text
客户说话
   ↓
感知客户需求
   ↓
结合会话记忆
   ↓
规划客服下一步行为
   ↓
必要时查询后台事实
   ↓
自然回复客户
   ↓
继续对话
```

数据库、RAG、图片搜索、Jev、LLM、Tool Calling 都服务于这个目标，不反过来主导产品形态。

---

# 33. 后续扩展方向

一期稳定后，可独立增加：

```text
Customer Long-term Memory
人工在线坐席
订单查询
实时库存
个性化推荐
询盘线索收集
CRM Connector
WhatsApp Connector
多语言自动切换
语音客服
```

邮件系统保持为单独项目，通过共享接口复用：

```text
Product Service
Knowledge Service
Pricing Service
Vision Search
```

而不是把邮件逻辑直接塞入网站智能客服核心。


---

# 34. 技术架构

## 34.1 技术架构原则

本项目采用：

```text
客服核心轻量自研
+
基础设施采用成熟组件
+
所有能力通过接口隔离
```

目标：

```text
数据库可替换
RAG 可替换
LLM 可替换
Embedding 可替换
图片搜索可替换
Jev 可启用 / 禁用
Pricing 可启用 / 禁用
```

但无论底层能力如何变化，智能客服的核心业务结构保持：

```text
Perception
   ↓
Memory
   ↓
Dialogue Planning
   ↓
Action / Query
   ↓
Response
```

不允许基础设施反向主导客服业务结构。

---

## 34.2 技术选型

| 层级 | 技术 | 用途 |
| --- | --- | --- |
| Chat Widget | React + TypeScript + Vite | 可嵌入企业现有网站 |
| 管理后台 | Next.js | 会话、配置、知识库、数据管理 |
| API | FastAPI + Python | 智能客服主后端 |
| Schema | Pydantic | 感知、规划、Tool Result 等结构化对象 |
| ORM | SQLAlchemy 2 | 数据访问 |
| Migration | Alembic | 数据库版本管理 |
| 主数据库 | PostgreSQL | Session、Message、产品、配置、日志 |
| 向量能力 | pgvector | RAG 与产品图片向量检索 |
| Cache | Redis | Session State、短期记忆、缓存、限流 |
| 对象存储 | MinIO / S3-compatible | 客户上传图片、产品图片、知识文件 |
| LLM Gateway | 自研 Adapter，可接 LiteLLM | 多模型统一调用 |
| RAG | 自研薄层 | Retrieval / Filter / Rerank / Context |
| Tool Calling | Tool Registry + Jev | 后台工具选择与执行 |
| 流式传输 | SSE | LLM 回复流式输出 |
| 日志与 Trace | Structured Log + OpenTelemetry | 调试、链路跟踪、性能分析 |
| 部署 | Docker Compose | 一期开发与部署 |

一期不强制引入 LangChain / LangGraph。

如后期复杂 Workflow 明显增加，可通过接口新增实现，而不是重写客服核心。

---

# 35. 总体技术框架

```text
客户网站
    │
    ▼
┌────────────────────────────┐
│ AI Chat Widget             │
│ React + TypeScript         │
└─────────────┬──────────────┘
              │ HTTPS / SSE
              ▼
┌────────────────────────────┐
│ FastAPI                    │
│                            │
│ Chat API                   │
│ Session API                │
│ Upload API                 │
│ Streaming                  │
└─────────────┬──────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│ Customer Service Runtime             │
│                                      │
│ Perception                           │
│      ↓                               │
│ Memory                               │
│      ↓                               │
│ Dialogue Planner                     │
│      ↓                               │
│ Action Executor                      │
│      ↓                               │
│ Response Generator                   │
│      ↓                               │
│ Human Handoff                        │
└──────────────────┬───────────────────┘
                   │
          需要业务事实时
                   ▼
┌──────────────────────────────────────┐
│ Capability Layer                     │
│                                      │
│ Product Service                      │
│ Vision Search                        │
│ Knowledge / RAG                      │
│ Pricing Service                      │
└───────────┬──────────┬───────────────┘
            │          │
            ▼          ▼
      PostgreSQL    pgvector
            │
            ├────────── Redis
            │
            └────────── MinIO / S3
```

AI Runtime 独立存在：

```text
Customer Service Runtime
          │
          ▼
      AI Runtime
          │
   ┌──────┼───────────────┐
   ▼      ▼               ▼
LLM     Structured       Tool Calling
Gateway Output             │
                            ▼
                           Jev
                            │
                            ▼
                       Tool Registry
```

---

# 36. Customer Service Runtime

Customer Service Runtime 是整个项目的业务核心。

不使用通用 Agent Runtime 作为项目主体。

建议核心接口：

```python
class PerceptionService:
    async def perceive(self, message, context):
        ...

class MemoryService:
    async def build_context(self, session_id):
        ...

class DialoguePlanner:
    async def plan(self, perception, memory):
        ...

class ActionExecutor:
    async def execute(self, action, context):
        ...

class ResponseGenerator:
    async def generate(self, context):
        ...
```

核心运行链：

```text
New Message
    ↓
Perception
    ↓
Memory Build
    ↓
Dialogue Planning
    ↓
Direct Reply / Clarify / Query / Recommend / Handoff
    ↓
必要时执行 Capability
    ↓
Update Memory
    ↓
Response Generation
    ↓
Stream Response
```

---

# 37. 感知层技术实现

一期不训练专用模型。

采用：

```text
用户当前消息
+
必要的 Session Context
+
Structured Output Schema
        ↓
LLM
        ↓
PerceptionResult
```

建议 Schema：

```python
class PerceptionResult(BaseModel):
    intent: str
    entities: dict
    references: list
    missing_information: list[str]
    sentiment: str | None
    confidence: float
```

示例：

```text
Customer:
I need simple men's rings, black, maybe 500pcs.
```

输出：

```json
{
  "intent": "product_search",
  "entities": {
    "category": "ring",
    "gender": "men",
    "style": "simple",
    "color": "black",
    "quantity": 500
  },
  "references": [],
  "missing_information": [
    "material"
  ],
  "sentiment": "neutral",
  "confidence": 0.95
}
```

### 37.1 感知层约束

感知层不得：

```text
直接查询数据库
直接做产品推荐
直接计算价格
直接决定具体 Tool
直接生成最终回复
```

感知只回答：

```text
客户说了什么？
客户想做什么？
已经知道哪些条件？
缺少哪些条件？
是否存在上下文指代？
```

---

# 38. Memory 技术实现

一期 Memory 使用：

```text
Redis
+
PostgreSQL
```

职责：

```text
Redis：
Working Memory
当前 Session State
当前产品
候选产品
当前需求
临时状态

PostgreSQL：
完整 Message History
Session Metadata
Conversation Summary
长期持久化状态
```

---

## 38.1 Working Memory

示例：

```json
{
  "session_id": "S1001",
  "requirements": {
    "category": "ring",
    "material": "316L",
    "color": "black",
    "quantity": 500
  },
  "candidate_products": [
    "R001",
    "R002",
    "R003"
  ],
  "selected_product": "R002",
  "last_action": "product_recommendation"
}
```

---

## 38.2 长对话 Context Builder

不允许把完整历史无限塞给 LLM。

Context Builder 只组装：

```text
System / Brand Instructions
+
Conversation Summary
+
Current Requirements
+
Current Product Context
+
Recent Messages
+
必要的 Capability Results
```

推荐：

```text
Recent Messages：最近 6~12 轮
Conversation Summary：超过阈值后自动更新
```

实际阈值可配置。

---

## 38.3 Memory 接口

```python
class MemoryStore:
    async def load_session(...): ...
    async def save_session(...): ...
    async def append_message(...): ...
    async def update_summary(...): ...
```

业务层不得直接操作 Redis Key 或 SQL 表。

---

# 39. Dialogue Planner 技术实现

Dialogue Planner 是“客服规划”，不是 Tool Planner。

Planner 只输出客服业务动作。

建议：

```python
class DialogueAction(str, Enum):
    ANSWER_DIRECTLY = "answer_directly"
    ASK_CLARIFICATION = "ask_clarification"
    ASK_REQUIREMENT = "ask_requirement"
    SEARCH_PRODUCT = "search_product"
    SEARCH_SIMILAR_PRODUCT = "search_similar_product"
    GET_PRODUCT_INFORMATION = "get_product_information"
    GET_PRICE_INFORMATION = "get_price_information"
    SEARCH_KNOWLEDGE = "search_knowledge"
    RECOMMEND_PRODUCT = "recommend_product"
    HUMAN_HANDOFF = "human_handoff"
    FINISH = "finish"
```

输出示例：

```json
{
  "action": "ask_requirement",
  "field": "plating",
  "reason_code": "MISSING_RELEVANT_FILTER"
}
```

其中：

```text
reason_code
```

用于工程调试和评估。

不记录模型隐藏思维过程。

---

# 40. Action Executor

Executor 把客服业务动作转成后台执行请求。

例如：

```text
Planner:
get_product_information
        ↓
Executor
        ↓
resolve required capability
        ↓
AI Runtime / Tool Calling
        ↓
Product Tool
```

Executor 不负责：

```text
理解用户意图
生成最终文案
存储业务数据
```

---

# 41. Jev 的技术位置

Jev 位于 AI Runtime / Tool Calling 内部。

```text
Dialogue Planner
       │
       │ get_product_information
       ▼
Action Executor
       │
       ▼
Tool Calling Runtime
       │
       ▼
      Jev
       │
       ▼
Tool Registry
       │
       ▼
Product Tool
```

职责边界：

```text
Dialogue Planner：
客服下一步应该做什么？

Jev：
为了完成这个后台动作，
当前应该调用哪个 Tool？
```

Jev 不负责：

```text
决定客服要问什么
维护 Session Memory
生成最终客服回复
决定整体会话流程
```

Jev 必须可以配置关闭：

```yaml
tool_calling:
  jev:
    enabled: true
```

关闭后可使用：

```text
Rule-based Tool Resolver
```

作为 fallback。

---

# 42. Tool Registry

所有后台 Tool 统一注册。

一期：

```text
ProductTool
VisionSearchTool
KnowledgeTool
PricingTool
HumanHandoffTool
```

统一抽象：

```python
class Tool:
    name: str
    description: str
    input_schema: dict

    async def execute(self, args, context):
        ...
```

统一返回：

```python
class ToolResult(BaseModel):
    success: bool
    data: dict
    confidence: float | None
    sources: list
    error: dict | None
```

不得让不同 Tool 返回完全不同的随机结构。

---

# 43. Product Capability

Product Service 负责真实产品事实。

一期接口：

```text
get_product_by_sku
search_products
filter_products
get_product_spec
get_product_moq
```

产品事实优先来自结构化数据库。

推荐：

```text
Product Service
      ↓
Product Repository
      ↓
Product Connector
      ↓
PostgreSQL / 外部 ERP / 外部 Commerce API
```

未来替换数据源时：

```text
客服核心不修改
Product Service 不修改
只替换 Connector
```

---

# 44. RAG 技术框架

RAG 只属于 Knowledge Capability。

不作为整个客服系统默认入口。

一期建议：

```text
PostgreSQL + pgvector
```

检索链：

```text
Question
   ↓
Query Normalize
   ↓
Vector Search
+
Keyword / Full-text Search
   ↓
Fusion
   ↓
Top-K Candidate
   ↓
Reranker（可选）
   ↓
Context Builder
   ↓
LLM
```

统一 Retriever：

```python
class Retriever:
    async def retrieve(
        self,
        query: str,
        filters: dict,
        top_k: int,
    ):
        ...
```

实现：

```text
PgVectorRetriever
```

以后可以增加：

```text
QdrantRetriever
MilvusRetriever
ElasticRetriever
```

而不影响 Knowledge Service。

---

# 45. RAG 数据边界

适合 RAG：

```text
公司介绍
材质说明
304 / 316L 区别
PVD 工艺
包装说明
定制流程
FAQ
交期通用说明
质量体系
```

不适合优先 RAG：

```text
具体 SKU 材质
具体 SKU MOQ
具体 SKU 尺寸
具体产品价格
实时库存
```

这些必须优先走结构化 Product / Pricing Capability。

---

# 46. Vision Search 技术框架

Vision Search 独立为 Capability。

```text
客户图片
   ↓
Image Preprocessor
   ↓
Image Embedding
   ↓
Vector Search
   ↓
Top-K
   ↓
Metadata Filter
   ↓
Visual Reranker（可选）
   ↓
Candidate Products
```

表结构示例：

```text
product_images

id
product_id
image_url
embedding
view_type
metadata
created_at
```

一个产品允许保存多张：

```text
front
side
detail
model
packaging
```

图片搜索输出：

```json
{
  "products": [
    {
      "sku": "R1001",
      "score": 0.94
    },
    {
      "sku": "R1002",
      "score": 0.87
    }
  ]
}
```

低于配置阈值时不得确认具体 SKU。

---

# 47. Pricing Capability

Pricing 独立于 Product Service。

原因：

```text
产品事实
和
价格业务规则
不是同一职责
```

接口：

```text
get_public_price
get_reference_price
can_show_price
```

输入示例：

```json
{
  "sku": "R1001",
  "quantity": 500,
  "session_id": "S1001"
}
```

输出示例：

```json
{
  "can_show": true,
  "price": 2.15,
  "currency": "USD",
  "price_type": "reference"
}
```

AI 不允许自行推算价格。

---

# 48. LLM Gateway

客服代码不得直接依赖某一家模型 SDK。

统一：

```text
Customer Service
      ↓
LLM Gateway
      │
      ├── OpenAI Adapter
      ├── Anthropic Adapter
      ├── OpenAI-Compatible Adapter
      └── Local Model Adapter
```

统一接口：

```python
class LLMGateway:
    async def generate(...): ...
    async def structured(...): ...
    async def stream(...): ...
```

配置示例：

```yaml
llm:
  provider: openai_compatible
  model: model-name
  temperature: 0.3
  timeout_seconds: 30
```

可在 Gateway 下使用 LiteLLM，但业务代码不直接依赖 LiteLLM。

---

# 49. Structured Output

以下模块必须优先使用 Structured Output：

```text
Perception
Dialogue Planning
Tool Decision
Tool Arguments
RAG Metadata
Handoff Decision
```

建议集中管理 Schema：

```text
backend/app/schemas/
├── perception.py
├── dialogue.py
├── tool.py
├── product.py
├── vision.py
└── response.py
```

禁止各模块私自定义不兼容 JSON。

---

# 50. Chat Widget 技术要求

Chat Widget 使用：

```text
React
TypeScript
Vite
```

原因：

```text
体积较小
可独立打包
容易嵌入不同网站
不要求宿主网站使用 Next.js
```

集成方式：

```html
<script src="customer-service-widget.js"></script>
```

或：

```text
npm package
```

一期 Widget：

```text
文本聊天
图片上传
产品卡片
流式回复
会话恢复
重新连接
人工客服入口
```

---

# 51. Admin Web

管理后台使用：

```text
Next.js
```

一期可只做必要页面：

```text
Dashboard
Sessions
Conversation Detail
Configuration
Products（可选）
Knowledge Base（可选）
Logs
```

管理后台不是客户入口。

---

# 52. API 技术规范

建议：

```text
REST
+
SSE
```

一期不强制 WebSocket。

接口：

```text
POST /api/v1/chat/sessions
POST /api/v1/chat/messages
GET  /api/v1/chat/sessions/{id}
POST /api/v1/chat/images
POST /api/v1/chat/handoff
GET  /api/v1/chat/stream/{message_id}
```

如使用单请求流式：

```text
POST /api/v1/chat/messages/stream
Content-Type: text/event-stream
```

---

# 53. 数据库框架

一期：

```text
PostgreSQL
```

建议 Schema：

```text
sessions
messages
conversation_states

products
product_images

knowledge_documents
knowledge_chunks

pricing_rules

tool_execution_logs
llm_usage_logs

customer_service_configs
```

向量字段直接使用：

```text
pgvector
```

不在一期引入多个数据库系统。

---

# 54. Redis 使用范围

Redis 只用于：

```text
Working Memory
Session Cache
Rate Limiting
临时状态
短期 Tool Cache
分布式锁（需要时）
```

PostgreSQL 才是持久化事实来源。

不得把唯一重要业务记录只放 Redis。

---

# 55. Object Storage

开发环境：

```text
MinIO
```

生产允许替换：

```text
AWS S3
Cloudflare R2
阿里 OSS
腾讯 COS
其他 S3-compatible 服务
```

统一接口：

```python
class ObjectStorage:
    async def upload(...): ...
    async def get_url(...): ...
    async def delete(...): ...
```

---

# 56. 项目代码结构

推荐：

```text
ai-customer-service/
│
├── README.md
├── REQUIREMENTS.md
├── docker-compose.yml
├── .env.example
│
├── apps/
│   ├── chat-widget/
│   └── admin-web/
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   └── app/
│       │
│       ├── main.py
│       │
│       ├── api/
│       │   ├── chat.py
│       │   ├── session.py
│       │   ├── upload.py
│       │   └── admin.py
│       │
│       ├── customer_service/
│       │   ├── runtime.py
│       │   ├── perception/
│       │   ├── memory/
│       │   ├── dialogue/
│       │   ├── response/
│       │   └── handoff/
│       │
│       ├── capabilities/
│       │   ├── product/
│       │   ├── vision/
│       │   ├── knowledge/
│       │   └── pricing/
│       │
│       ├── runtime/
│       │   ├── llm/
│       │   ├── jev/
│       │   ├── tool_calling/
│       │   └── structured_output/
│       │
│       ├── retrieval/
│       │   ├── base.py
│       │   ├── pgvector.py
│       │   ├── hybrid.py
│       │   └── reranker.py
│       │
│       ├── tools/
│       │   ├── registry.py
│       │   ├── product.py
│       │   ├── vision.py
│       │   ├── knowledge.py
│       │   └── pricing.py
│       │
│       ├── connectors/
│       │   ├── database/
│       │   ├── product/
│       │   ├── vector/
│       │   ├── storage/
│       │   └── external/
│       │
│       ├── repositories/
│       ├── schemas/
│       ├── models/
│       ├── config/
│       └── observability/
│
├── migrations/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── conversation/
│   └── evaluation/
│
└── docs/
```

---

# 57. 模块依赖规则

推荐依赖方向：

```text
API
 ↓
Customer Service
 ↓
Capabilities
 ↓
Interfaces
 ↓
Connectors
 ↓
Infrastructure
```

AI Runtime 是被 Customer Service / Capabilities 调用的基础设施。

禁止：

```text
Connector → Customer Service
Database → Dialogue Planner
RAG → Customer Service Runtime
Tool → Planner
```

也就是说底层实现不得反向控制客服业务。

---

# 58. 配置体系

所有可替换能力均通过配置注册。

示例：

```yaml
customer_service:
  perception:
    provider: llm
    enabled: true

  memory:
    session:
      enabled: true
      provider: redis

    persistent:
      enabled: true
      provider: postgres

  dialogue:
    planner: llm

  capabilities:
    product:
      enabled: true

    vision:
      enabled: true

    knowledge:
      enabled: true

    pricing:
      enabled: false

runtime:
  tool_calling:
    jev:
      enabled: true

  llm:
    provider: openai_compatible
    model: model-name

retrieval:
  provider: pgvector
  top_k: 10
  rerank: false

storage:
  provider: minio
```

---

# 59. 降级策略

每个后台能力关闭或故障时，客服必须继续工作。

例如：

### Product Service 故障

```text
I’m unable to confirm the exact product specifications at the moment.
I can connect you with our sales team for confirmation.
```

### Vision Search 关闭

```text
图片仍可接收
但不执行自动找款
引导客户提供 SKU 或产品描述
```

### RAG 关闭

```text
只回答模型可安全回答的一般问题
企业事实类问题转人工
```

### Pricing 关闭

```text
收集 SKU + Quantity
然后转销售询价
```

---

# 60. 测试框架

后端：

```text
pytest
pytest-asyncio
httpx
```

前端：

```text
Vitest
Testing Library
Playwright
```

测试分层：

```text
Unit Test
Integration Test
Conversation Test
Evaluation Test
E2E
```

客服对话必须建立固定测试集。

例如：

```text
询问产品
信息不完整
多轮追问
first one / second one
图片找款
RAG 问答
价格询问
要求人工
故障降级
```

---

# 61. Evaluation

项目后期需要建立独立 Evaluation。

一期先预留接口。

指标：

```text
Intent Accuracy
Entity Accuracy
Reference Resolution Accuracy
Dialogue Action Accuracy
Product Fact Accuracy
Vision Top-K Recall
RAG Retrieval Recall
Hallucination Rate
Handoff Accuracy
Latency
Token Usage
Cost
```

评估不是客户可见功能。

---

# 62. 一期技术开发顺序

不先做 RAG。

建议严格按照：

```text
Step 1
项目骨架
FastAPI
React Chat Widget
PostgreSQL
Redis

Step 2
Chat API
Session
Message
SSE Streaming

Step 3
Perception
Structured Output

Step 4
Session Memory
Conversation State
Context Builder

Step 5
Dialogue Planner
客服动作模型

Step 6
Response Generator
完整纯对话闭环

Step 7
Product Capability

Step 8
Vision Search

Step 9
Knowledge / RAG

Step 10
Pricing

Step 11
Jev Tool Calling

Step 12
Evaluation / Observability
```

第一阶段完成 Step 1~6 后，即使没有产品数据库，系统也必须已经是一个可连续交流的 AI 客服。

---

# 63. 技术架构最终边界

本项目技术框架的核心不是：

```text
LangChain
LangGraph
RAG
Jev
Tool Calling
Vector DB
```

而是：

```text
Customer Service Runtime
```

其上层产品行为始终为：

```text
感知客户
↓
记住当前对话
↓
规划下一步客服行为
↓
需要时调用后台事实能力
↓
自然回复客户
```

底层所有 AI 技术都只能作为这一客服流程的支撑能力。
