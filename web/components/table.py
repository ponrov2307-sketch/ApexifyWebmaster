from nicegui import ui
from core.config import COLORS

def create_portfolio_table(assets: list, on_edit, on_news, on_chart):
    """
    สร้างตารางหุ้นแบบ Custom
    assets: ข้อมูลหุ้นในพอร์ต (list of dicts)
    on_edit, on_news, on_chart: ฟังก์ชันที่จะให้ทำงานเมื่อกดปุ่ม
    """
    
    # 📦 กล่องคลุมตารางทั้งหมด (ใส่เงาและขอบโค้ง)
    with ui.column().classes('w-full bg-[#161B22] rounded-3xl border border-gray-800 overflow-hidden mt-6 shadow-xl gap-0'):
        
        # --- 1. แถวหัวตาราง (Header) ---
        with ui.row().classes('w-full bg-[#11141C] p-4 border-b border-gray-800 text-gray-500 text-xs font-bold uppercase tracking-wider items-center flex-nowrap'):
            ui.label('TICKER').classes('w-24 pl-4')
            ui.label('SHARES').classes('w-24 text-right')
            ui.label('AVG COST').classes('w-32 text-right')
            ui.label('LAST PRICE').classes('w-32 text-right')
            ui.label('TREND (7D)').classes('flex-1 text-center min-w-[120px]') # ช่องสำหรับกราฟ
            ui.label('PROFIT').classes('w-32 text-right')
            ui.label('ACTIONS').classes('w-32 text-center pr-4')

        # --- 2. เช็คว่ามีหุ้นไหม ---
        if not assets:
            with ui.row().classes('w-full p-8 justify-center'):
                ui.label('ไม่มีข้อมูลหุ้นในกลุ่มนี้ (No assets found)').classes('text-gray-500 font-bold')
            return

        # --- 3. วนลูปสร้างแถวข้อมูลหุ้น (Rows) ---
        for asset in assets:
            # ดึงค่าออกมาจาก dict
            ticker = asset.get('ticker', 'N/A')
            shares = asset.get('shares', 0)
            cost = asset.get('avg_cost', 0)
            last_price = asset.get('last_price', 0)
            profit = (last_price - cost) * shares
            sparkline = asset.get('sparkline', [])
            is_up = asset.get('is_up', True)

            # กำหนดสี
            color_class = 'text-[#32D74B]' if profit >= 0 else 'text-[#FF453A]'
            profit_sign = '+' if profit >= 0 else ''
            line_color = COLORS['success'] if is_up else COLORS['danger']

            # 🛠️ สร้างแถว (Row) สำหรับหุ้น 1 ตัว
            with ui.row().classes('w-full p-4 items-center border-b border-gray-800/50 hover:bg-[#1C2128] transition-colors group gap-0 flex-nowrap'):
                
                # คอลัมน์ที่ 1-4: ข้อมูลพื้นฐาน
                ui.label(ticker).classes('w-24 pl-4 text-xl font-black text-[#D0FD3E]')
                ui.label(f"{shares:.4f}").classes('w-24 text-right text-lg text-gray-300 font-medium')
                ui.label(f"${cost:,.2f}").classes('w-32 text-right text-lg text-gray-300 font-medium')
                ui.label(f"${last_price:,.2f}").classes('w-32 text-right text-lg text-white font-bold')
                
                # 📈 คอลัมน์ที่ 5: Trend (Sparkline ย้อนหลัง 7 วัน)
                with ui.element('div').classes('flex-1 h-12 px-4 min-w-[120px]'):
                    if sparkline:
                        # ใช้ ECharts ที่ฝังมากับ NiceGUI วาดกราฟเส้นแบบไม่มีแกน X/Y
                        ui.echart({
                            'xAxis': {'type': 'category', 'show': False, 'data': list(range(len(sparkline)))},
                            'yAxis': {'type': 'value', 'show': False, 'scale': True},
                            'series': [{
                                'data': sparkline,
                                'type': 'line',
                                'smooth': True,         # ทำให้เส้นโค้งสมูท
                                'showSymbol': False,    # ซ่อนจุดกลมๆ บนเส้น
                                'lineStyle': {'color': line_color, 'width': 2.5},
                            }],
                            'grid': {'left': 0, 'right': 0, 'top': 5, 'bottom': 5},
                        })
                    else:
                        ui.label('N/A').classes('text-gray-600 text-xs flex justify-center h-full items-center')

                # คอลัมน์ที่ 6: กำไร/ขาดทุน
                ui.label(f"{profit_sign}${profit:,.2f}").classes(f'w-32 text-right text-lg font-bold {color_class}')
                
                # 🎯 คอลัมน์ที่ 7: Actions (ปุ่มคำสั่ง)
                with ui.row().classes('w-32 justify-center gap-1 pr-4'):
                    # ใช้ lambda t=ticker: เพื่อส่งชื่อหุ้นไปให้ฟังก์ชันทำงานได้ถูกต้อง
                    ui.button(icon='edit', on_click=lambda t=ticker: on_edit(t)) \
                        .props('flat dense size=sm').classes('text-gray-400 hover:text-white')
                    
                    ui.button(icon='article', on_click=lambda t=ticker: on_news(t)) \
                        .props('flat dense size=sm').classes('text-gray-400 hover:text-white')
                    
                    # ปุ่มดูกราฟ (เด่นที่สุด)
                    ui.button(icon='candlestick_chart', on_click=lambda t=ticker: on_chart(t)) \
                        .props('flat dense size=sm').classes('text-[#D0FD3E] hover:text-white transform hover:scale-110 transition-transform')