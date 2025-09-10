from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes import bulk

app = FastAPI(title="LinkTracker Pro")

# ルートのインポート
app.include_router(bulk.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
