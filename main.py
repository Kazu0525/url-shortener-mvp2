# main.py - エントリーポイント（修正版）
from fastapi import FastAPI
import os
from routes import admin, api, main as main_routes
from utils.database import init_db

# データベース初期化
init_db()

# 設定
BASE_URL = os.getenv("BASE_URL", "https://link-shortcut-flow-analysis.onrender.com")
DB_PATH = os.getenv("DB_PATH", "url_shortener.db")

# FastAPIアプリ
app = FastAPI(
    title="LinkTrack Pro",
    description="URL短縮・分析プラットフォーム",
    version="1.0.0"
)

# ルーターの登録
app.include_router(main_routes.router)
app.include_router(admin.router, prefix="/admin")
app.include_router(api.router, prefix="/api")

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-09-10T00:00:00Z"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
