from nicegui import ui
from services.yahoo_finance import get_market_summary

def create_ticker():
    """สร้างแถบวิ่ง (Ticker) แสดงดัชนีตลาดโลกที่ขอบจอบนสุด"""
    # สร้าง Header แบบมีกระจกฝ้า (backdrop-blur) ติดอยู่ด้านบนสุด
    with ui.header().classes('bg-[#11141C]/90 backdrop-blur-md border-b border-gray-800 py-2 z-50'):
        ticker_container = ui.row().classes('w-full justify-center items-center gap-8 text-xs font-bold')
        
        def update():
            ticker_container.clear()
            # 🌟 ดึงข้อมูลจาก Yahoo Finance ที่แก้บั๊ก Anti-block แล้ว
            data = get_market_summary()
            
            with ticker_container:
                # ไฟกระพริบ Live Market
                ui.label('● LIVE MARKET').classes('text-[#D0FD3E] text-[10px] font-black animate-pulse')
                
                # วนลูปสร้างตัวเลขดัชนีแต่ละตัว
                for item in data:
                    with ui.row().classes('items-center gap-2'):
                        ui.label(item['name']).classes('text-gray-400')
                        ui.label(item['value']).classes('text-white')
                        
                        # กำหนดสีเขียว/แดง และลูกศรชี้ขึ้น/ลง
                        color_class = 'text-[#32D74B]' if item['is_up'] else 'text-[#FF453A]'
                        arrow = '▲' if item['is_up'] else '▼'
                        ui.label(f"{arrow} {item['change']}%").classes(color_class)
        
        # ให้มันอัปเดตตัวเองทุกๆ 60 วินาที โดยที่หน้าเว็บไม่ต้องรีเฟรช
        ui.timer(60.0, update)
        update() # เรียกแสดงผลครั้งแรกทันที