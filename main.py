import os
from fastapi import FastAPI
from routes import bulk

app = FastAPI(title="LinkTracker Pro")
app.include_router(bulk.router)

@app.get("/")
async def root():
    return {"message": "LinkTracker Pro API is running", "docs_url": "/docs"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))  # Renderの環境変数PORTを優先
    uvicorn.run(app, host="0.0.0.0", port=port)
