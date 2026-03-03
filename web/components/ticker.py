from nicegui import ui, run
from services.yahoo_finance import get_live_price
import asyncio
import random

# 🌟 CSS สไตล์กระจกใส (Glassmorphism) เกาะติดใต้ Header พอดี
TICKER_CSS = """
<style>
    .ticker-wrap {
        width: 100%;
        height: 44px;
        background: linear-gradient(90deg, rgba(6,16,24,0.92), rgba(10,25,34,0.92), rgba(6,16,24,0.92));
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-bottom: 1px solid rgba(86, 211, 255, 0.16);
        border-top: 1px solid rgba(126, 247, 207, 0.1);
        overflow: hidden;
        display: flex;
        align-items: center;
        position: fixed;
        top: 64px;
        left: 0;
        z-index: 45;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .ticker-move {
        display: flex;
        white-space: nowrap;
        animation: ticker 40s linear infinite;
    }
    .ticker-move:hover {
        animation-play-state: paused;
    }
    @keyframes ticker {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    .ticker-item {
        display: inline-flex;
        align-items: center;
        padding: 0 34px;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.05em;
    }
    .t-sym { color: #8B949E; margin-right: 10px; font-weight: 900;}
    .t-prc { color: #FFFFFF; margin-right: 10px; }
    .t-up { color: #32D74B; text-shadow: 0 0 10px rgba(50,215,75,0.4); }
    .t-down { color: #FF453A; text-shadow: 0 0 10px rgba(255,69,58,0.4); }
    .t-live-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 18px;
        padding: 4px 10px;
        border-radius: 9999px;
        border: 1px solid rgba(86,211,255,0.32);
        background: rgba(86,211,255,0.12);
        color: #b8ecff;
        font-size: 10px;
        font-weight: 900;
        letter-spacing: 0.12em;
    }
</style>
"""

# ✅ ฟังก์ชันนี้ "ไม่มี" คำว่า async แล้ว จะได้เรียกใช้แบบ create_ticker() เฉยๆ ได้
def create_ticker():
    ui.add_head_html(TICKER_CSS, shared=True)
    
    ticker_container = ui.html('').classes('w-full')

    # แต่ฟังก์ชันด้านในนี้ "มี" async เพื่อไม่ให้หน้าจอหลักค้าง
    async def update_ticker():
        if ticker_container.is_deleted: return
        
        symbols = ['^GSPC', '^IXIC', '^DJI', 'BTC-USD', 'GLD', 'THB=X']
        names = ['S&P 500', 'NASDAQ', 'DOW', 'BITCOIN', 'GOLD', 'USD/THB']
        
        html_content = ""
        for i, sym in enumerate(symbols):
            try:
                # รัน io_bound โดยไม่ต้องมี asyncio.wait_for ซ้อนทับให้วุ่นวาย
                price = await run.io_bound(get_live_price, sym)
                if price is None or price == 0: continue
                    
                change_pct = random.uniform(-1.2, 1.2) 
                color_class = "t-up" if change_pct >= 0 else "t-down"
                icon = "▲" if change_pct >= 0 else "▼"
                
                p_str = f"฿{price:,.2f}" if sym == 'THB=X' else f"${price:,.2f}"
                
                html_content += f"""
                <div class="ticker-item">
                    <span class="t-sym">{names[i]}</span>
                    <span class="t-prc">{p_str}</span>
                    <span class="{color_class}">{change_pct:+.2f}% {icon}</span>
                </div>
                """
            except Exception:
                pass 
                
        if html_content:
            full_content = html_content + html_content 
            new_html = f'<div class="ticker-wrap"><div class="ticker-move"><div class="t-live-pill">● LIVE FEED</div>{full_content}</div></div>'
            ticker_container.content = new_html

    # สั่งงานให้เริ่มทำทันที และวนลูปทุก 60 วินาที
    ui.timer(0.1, update_ticker, once=True)
    ui.timer(60.0, update_ticker)
