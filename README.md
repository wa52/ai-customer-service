# AI Customer Service

网站内嵌式 AI 智能客服与公开珠宝商品目录，按 [REQUIREMENTS.md](REQUIREMENTS.md) 组织。核心是 Customer Service Runtime、商品数据检索，以及可关联 SKU 的图片找款。

## 当前一期范围

- FastAPI Chat API、Session API、图片上传接口、人工接管接口和商品目录 API
- SSE 消息流接口
- Perception / Memory / Dialogue Planner / Response Generator 分层
- React + TypeScript + Vite Chat Widget
- 结构化输出 Schema 与能力开关配置样例
- `CustomerServiceRuntime → LLMGateway → ToolRegistry → Capability → LLM` 主链路
- GPT / DeepSeek OpenAI-compatible Chat Completions、原生 Tool Calling、真实模型 SSE 流式转发
- 未配置模型时仅使用明确标注的本地 fallback；生产配置见 `.env.example`
- Session 默认使用内存实现，也可通过 `MEMORY_PROVIDER=redis|postgres` 切换持久化后端
- PostgreSQL 产品目录及公开参考价、Knowledge Search V1
- CLIP + pgvector 图片找款；商品图片向量可关联 SKU 并返回商品购买入口
- 图片 Embedding 依赖 `.[vision]` 可选依赖、已缓存的 CLIP 模型、已下载的商品图片和可访问的 PostgreSQL

## 启动后端

```powershell
cd D:\AiProjects\smart-customer-service\backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

## 启动 Widget

```powershell
cd D:\AiProjects\smart-customer-service\apps\chat-widget
npm install
npm run dev
```

## 建立商品图片向量索引

商品图片已由 `scripts/download_product_images.py` 按内容哈希缓存在 `data/products/images/`。先按后端配置确保 `DATABASE_URL` 指向已导入产品数据的 PostgreSQL，并确认 CLIP 模型权重已缓存到 Hugging Face 本地缓存（运行时采用离线加载）。然后在后端目录运行：

```powershell
cd D:\AiProjects\smart-customer-service\backend
.\.venv\Scripts\python.exe -m pip install -e ".[vision]"
.\.venv\Scripts\python.exe ..\scripts\index_product_image_embeddings.py
```

脚本会应用 `004_product_image_embeddings.sql`，分批写入并可续跑：已索引且图片 URL、模型版本未变化的 SKU 会跳过。图片搜索默认返回前三个相似 SKU，并保留旧 `vision_metadata` 向量作为尚未完成商品索引时的回退结果。

## 主要目录

```text
backend/app/customer_service/  客服运行时
backend/app/api/               Chat / Session / Upload API
backend/app/schemas/           统一结构化输出模型
apps/chat-widget/              可嵌入的 React 客服窗口
```
