# routes/main.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os
from datetime import datetime
from ..utils.helpers import generate_short_code, validate_url, clean_url

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# データベース接続
def get_db_connection():
    conn = sqlite3.connect(os.getenv("DB_PATH", "url_shortener.db"))
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM urls")
        total_links = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clicks")
        total_clicks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT ip_address) FROM clicks")
        unique_visitors = cursor.fetchone()[0]
        
        conn.close()
        
        context = {
            "request": request,
            "total_links": total_links,
            "total_clicks": total_clicks,
            "unique_visitors": unique_visitors,
            "system_status": "正常稼働中",
            "base_url": os.getenv("BASE_URL", "https://link-shortcut-flow-analysis.onrender.com")
        }
        return templates.TemplateResponse("index.html", context)
    except:
        context = {
            "request": request,
            "total_links": 0,
            "total_clicks": 0,
            "unique_visitors": 0,
            "system_status": "初期化中",
            "base_url": os.getenv("BASE_URL", "https://link-shortcut-flow-analysis.onrender.com")
        }
        return templates.TemplateResponse("index.html", context)

@router.get("/bulk", response_class=HTMLResponse)
async def bulk_page(request: Request):
    return templates.TemplateResponse("bulk.html", {"request": request})

@router.get("/analytics/{short_code}", response_class=HTMLResponse)
async def analytics_page(request: Request, short_code: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT original_url, created_at, custom_name FROM urls WHERE short_code = ?", (short_code,))
        url_data = cursor.fetchone()
        
        if not url_data:
            return HTMLResponse(content="<h1>404</h1><p>URLが見つかりません</p>", status_code=404)
        
        cursor.execute("""
            SELECT COUNT(*) as total_clicks, COUNT(DISTINCT ip_address) as unique_visitors
            FROM clicks c
            JOIN urls u ON c.url_id = u.id
            WHERE u.short_code = ?
        """, (short_code,))
        
        stats = cursor.fetchone()
        conn.close()
        
        context = {
            "request": request,
            "short_code": short_code,
            "original_url": url_data[0],
            "created_at": url_data[1],
            "custom_name": url_data[2],
            "total_clicks": stats[0] if stats else 0,
            "unique_visitors": stats[1] if stats else 0,
            "base_url": os.getenv("BASE_URL", "https://link-shortcut-flow-analysis.onrender.com")
        }
        return templates.TemplateResponse("analytics.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{short_code}")
async def redirect_url(short_code: str, request: Request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, original_url FROM urls WHERE short_code = ? AND is_active = 1", (short_code,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="無効な短縮コードです")
        
        url_id, original_url = result
        
        # クリック記録
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        referrer = request.headers.get("referer", "")
        source = request.query_params.get("source", "direct")
        
        cursor.execute("""
            INSERT INTO clicks (url_id, ip_address, user_agent, referrer, source, clicked_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (url_id, client_ip, user_agent, referrer, source, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return RedirectResponse(url=original_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="リダイレクトエラー")
