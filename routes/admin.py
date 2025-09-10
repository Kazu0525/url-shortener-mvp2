from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import sqlite3
import os

router = APIRouter()

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
        
        # HTMLコンテンツ生成
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>管理画面 - LinkTrack Pro</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
                .stat-card {{ background: #f9f9f9; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }}
                .stat-number {{ font-size: 2.5em; font-weight: bold; color: #4CAF50; }}
                .stat-label {{ color: #666; margin-top: 10px; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #4CAF50; color: white; }}
                tr:hover {{ background: #f5f5f5; }}
                .action-btn {{ 
                    padding: 5px 10px; margin: 2px; border: none; border-radius: 3px; 
                    cursor: pointer; text-decoration: none; display: inline-block; color: white;
                }}
                .analytics-btn {{ background: #2196F3; }}
                .qr-btn {{ background: #FF9800; }}
                .export-btn {{ background: #4CAF50; }}
                .refresh-btn {{ background: #9C27B0; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px 0; }}
                .nav-buttons {{ text-align: center; margin: 20px 0; }}
                .nav-buttons a {{ margin: 0 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 管理画面 - LinkTrack Pro</h1>
                
                <div class="nav-buttons">
                    <a href="/">🏠 ホーム</a>
                    <a href="/bulk">📦 一括生成</a>
                    <a href="/docs">📚 API文書</a>
                    <button class="refresh-btn" onclick="location.reload()">🔄 データ更新</button>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{total_urls}</div>
                        <div class="stat-label">総URL数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{total_clicks}</div>
                        <div class="stat-label">総クリック数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{unique_clicks}</div>
                        <div class="stat-label">ユニーク訪問者</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{qr_clicks}</div>
                        <div class="stat-label">QRコードクリック</div>
                    </div>
                </div>

                <h2>📋 URL一覧</h2>
                <table>
                    <thead>
                        <tr>
                            <th>短縮コード</th>
                            <th>元URL</th>
                            <th>カスタム名</th>
                            <th>キャンペーン</th>
                            <th>作成日</th>
                            <th>クリック数</th>
                            <th>ユニーク</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for row in results:
            short_code = row["short_code"]
            original_url = row["original_url"]
            display_url = original_url[:50] + "..." if len(original_url) > 50 else original_url
            
            html_content += f"""
                        <tr>
                            <td><strong>{short_code}</strong></td>
                            <td><a href="{original_url}" target="_blank" title="{original_url}">{display_url}</a></td>
                            <td>{row['custom_name'] or '-'}</td>
                            <td>{row['campaign_name'] or '-'}</td>
                            <td>{row['created_at']}</td>
                            <td>{row['click_count']}</td>
                            <td>{row['unique_count']}</td>
                            <td>
                                <a href="/analytics/{short_code}" target="_blank" class="action-btn analytics-btn">📈 分析</a>
                                <a href="/{short_code}" target="_blank" class="action-btn qr-btn">🔗 テスト</a>
                            </td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
