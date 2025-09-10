# routes/api.py
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
import sqlite3
import os
from datetime import datetime
from ..utils.helpers import generate_short_code, validate_url, clean_url

router = APIRouter()

# データベース接続
def get_db_connection():
    conn = sqlite3.connect(os.getenv("DB_PATH", "url_shortener.db"))
    conn.row_factory = sqlite3.Row
    return conn

@router.post("/shorten-form")
async def shorten_form(url: str = Form(...), custom_name: str = Form(""), campaign_name: str = Form("")):
    try:
        if not validate_url(url):
            raise HTTPException(status_code=400, detail="無効なURLです")
        
        # 短縮コード生成
        short_code = generate_short_code()
        
        # 保存
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO urls (short_code, original_url, custom_name, campaign_name, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (short_code, clean_url(url), custom_name or None, campaign_name or None, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return JSONResponse({
            "success": True,
            "short_code": short_code,
            "short_url": f"{os.getenv('BASE_URL', 'https://link-shortcut-flow-analysis.onrender.com')}/{short_code}",
            "original_url": url,
            "custom_name": custom_name,
            "campaign_name": campaign_name
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-process")
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
                """, (short_code, clean_url(url), datetime.now().isoformat()))
                
                results.append({
                    "url": url,
                    "short_url": f"{os.getenv('BASE_URL', 'https://link-shortcut-flow-analysis.onrender.com')}/{short_code}",
                    "success": True
                })
            else:
                results.append({"url": url, "success": False, "error": "無効なURL"})
        
        conn.commit()
        conn.close()
        
        return JSONResponse({"results": results})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
