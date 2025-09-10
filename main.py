from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import bulk
import os

app = FastAPI(title="LinkTracker Pro")

# ルートのインポート
app.include_router(bulk.router)

@app.get("/")
async def root():
    return {"message": "LinkTracker Pro API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Renderの環境変数からポートを取得
    uvicorn.run(app, host="0.0.0.0", port=port)
