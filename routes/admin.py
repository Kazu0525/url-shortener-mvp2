# routes/admin.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# データベース接続
def get_db_connection():
    conn = sqlite3.connect(os.getenv("DB_PATH", "url_shortener.db"))
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/", response_class=HTMLResponse)
async def admin_page():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 統計取得
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT u.id) as total_urls,
                COUNT(c.id) as total_clicks,
                COUNT(DISTINCT c.ip_address) as unique_clicks,
                COUNT(CASE WHEN c.source = 'qr' THEN 1 END) as qr_clicks
            FROM urls u
            LEFT JOIN clicks c ON u.id = c.url_id
            WHERE u.is_active = 1
        """)
        
        stats = cursor.fetchone()
        total_urls = stats["total_urls"] if stats else 0
        total_clicks = stats["total_clicks"] if stats else 0
        unique_clicks = stats["unique_clicks"] if stats else 0
        qr_clicks = stats["qr_clicks"] if stats else 0
        
        # URL一覧取得
        cursor.execute("""
            SELECT u.short_code, u.original_url, u.created_at, u.custom_name, u.campaign_name,
                   COUNT(c.id) as click_count,
                   COUNT(DISTINCT c.ip_address) as unique_count
            FROM urls u
            LEFT JOIN clicks c ON u.id = c.url_id
            WHERE u.is_active = 1
            GROUP BY u.id
            ORDER BY u.created_at DESC
            LIMIT 50
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        # テンプレートに渡すデータ
        context = {
            "total_urls": total_urls,
            "total_clicks": total_clicks,
            "unique_clicks": unique_clicks,
            "qr_clicks": qr_clicks,
            "urls": results,
            "base_url": os.getenv("BASE_URL", "https://link-shortcut-flow-analysis.onrender.com")
        }
        
        return templates.TemplateResponse("admin.html", {"request": {}, "context": context})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
