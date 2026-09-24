from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.chat import router as chat_router
from app.api.admin import router as admin_router
from app.api.session import router as session_router
from app.api.upload import router as upload_router
from app.api.products import router as products_router

app = FastAPI(title="AI Customer Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(session_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.mount("/admin", StaticFiles(directory=Path(__file__).parent / "static" / "admin"), name="admin-static")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-customer-service"}


@app.get("/admin", include_in_schema=False)
def admin_page() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "admin" / "index.html")
