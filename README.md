# AI Customer Service

网站内嵌式 AI 智能客服一期骨架，按 [REQUIREMENTS.md](REQUIREMENTS.md) 组织。核心是 Customer Service Runtime：感知客户 → 维护会话记忆 → 规划客服动作 → 生成自然回复。

## 当前一期范围

- FastAPI Chat API、Session API、图片上传接口、人工接管接口
- SSE 消息流接口
- Perception / Memory / Dialogue Planner / Response Generator 分层
- React + TypeScript + Vite Chat Widget
- 结构化输出 Schema 与能力开关配置样例
- `CustomerServiceRuntime → LLMGateway → ToolRegistry → Capability → LLM` 主链路
- GPT / DeepSeek OpenAI-compatible Chat Completions、原生 Tool Calling、真实模型 SSE 流式转发
- 未配置模型时仅使用明确标注的本地 fallback；生产配置见 `.env.example`
- Session 默认使用内存实现，也可通过 `MEMORY_PROVIDER=redis|postgres` 切换持久化后端
- Vision/RAG/Pricing 仍属于后续 Phase

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

## 主要目录

```text
backend/app/customer_service/  客服运行时
backend/app/api/               Chat / Session / Upload API
backend/app/schemas/           统一结构化输出模型
apps/chat-widget/              可嵌入的 React 客服窗口
```
