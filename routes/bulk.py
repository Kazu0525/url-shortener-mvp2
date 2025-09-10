from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import string
import random
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# データベース接続
def get_db_connection():
    conn = sqlite3.connect("url_shortener.db")
    conn.row_factory = sqlite3.Row
    return conn

# 短縮コード生成
def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for _ in range(50):
        code = ''.join(random.choices(chars, k=length))
        cursor.execute("SELECT 1 FROM urls WHERE short_code = ?", (code,))
        if not cursor.fetchone():
            conn.close()
            return code
    
    conn.close()
    raise HTTPException(status_code=500, detail="短縮コード生成に失敗しました")

# URLバリデーション
def validate_url(url):
    return url.startswith(('http://', 'https://'))

@router.get("/bulk", response_class=HTMLResponse)
async def bulk_page():
    return templates.TemplateResponse("bulk.html", {"request": {}})

@router.post("/api/bulk-process")
async def bulk_process(urls: str = Form(...)):
    try:
        url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        results = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for url in url_list:
            if validate_url(url):
                short_code = generate_short_code()
                
                cursor.execute("""
                    INSERT INTO urls (short_code, original_url, created_at)
                    VALUES (?, ?, ?)
                """, (short_code, url, datetime.now().isoformat()))
                
                results.append({
                    "url": url,
                    "short_url": f"https://url-shortener-mvp.onrender.com/{short_code}",
                    "success": True
                })
            else:
                results.append({"url": url, "success": False, "error": "無効なURL"})
        
        conn.commit()
        conn.close()
        
        return JSONResponse({"results": results})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
