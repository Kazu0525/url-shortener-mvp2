from fastapi import FastAPI
import os
from routes import admin, api, main as main_routes

app = FastAPI(
    title="LinkTrack Pro",
    description="URL短縮・分析プラットフォーム",
    version="1.0.0"
)

app.include_router(main_routes.router)
app.include_router(admin.router, prefix="/admin")
app.include_router(api.router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
