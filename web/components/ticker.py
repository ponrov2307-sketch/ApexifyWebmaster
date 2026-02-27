from nicegui import ui
from services.yahoo_finance import get_market_summary

def create_ticker():
    """สร้างแถบวิ่ง (Marquee Ticker) แบบสมูท พร้อมเพิ่มค่าเงิน THB"""
    
    # 🌟 1. ใส่ CSS สำหรับแถบวิ่ง (Marquee)
    ui.add_head_html('''
        <style>
            .ticker-wrap {
                width: 100%;
                overflow: hidden;
                background-color: rgba(13, 17, 23, 0.9);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                padding: 6px 0;
                position: fixed;
                top: 64px; /* ให้อยู่ใต้ Header พอดี */
                z-index: 40;
            }
            .ticker-move {
                display: inline-block;
                white-space: nowrap;
                padding-right: 100%;
                animation: marquee 35s linear infinite;
            }
            .ticker-move:hover {
                animation-play-state: paused;
            }
            @keyframes marquee {
                0% { transform: translateX(100vw); }
                100% { transform: translateX(-100%); }
            }
        </style>
    ''', shared=True)

    # 🌟 2. โครงสร้างแถบวิ่ง
    with ui.element('div').classes('ticker-wrap'):
        ticker_container = ui.element('div').classes('ticker-move flex items-center gap-10 text-[11px] font-bold tracking-wider')

    def update():
        try:
            if ticker_container.is_deleted: return
            
            data = get_market_summary()
            
            # 🌟 3. บังคับเพิ่ม USD/THB เข้าไปในแถบวิ่ง
            has_thb = any('THB' in d.get('name', '') for d in data)
            if not has_thb:
                data.append({'name': 'USD/THB', 'value': '34.52', 'change': '0.15', 'is_up': False}) # Mock ค่าเงิน
                data.append({'name': 'Bitcoin', 'value': '65,852.95', 'change': '1600.83', 'is_up': False}) 
                data.append({'name': 'Gold', 'value': '2,361.90', 'change': '15.40', 'is_up': True}) 

            ticker_container.clear()
            with ticker_container:
                ui.label('● LIVE MARKET').classes('text-[#D0FD3E] font-black animate-pulse shadow-sm')
                
                for item in data:
                    with ui.row().classes('items-center gap-2 inline-flex'):
                        ui.label(item['name']).classes('text-gray-400')
                        ui.label(item['value']).classes('text-white')
                        
                        color_class = 'text-[#32D74B]' if item['is_up'] else 'text-[#FF453A]'
                        arrow = '▲' if item['is_up'] else '▼'
                        ui.label(f"{arrow} {item.get('change', '')}").classes(color_class)
                        
        except RuntimeError: pass
            
    update()
    # อัปเดตข้อมูลทุกๆ 1 นาที (ไม่ให้วิ่งกระตุก)
    ui.timer(60.0, update)