from nicegui import ui
from services.yahoo_finance import get_candlestick_data
from core.config import COLORS

async def show_candlestick_chart(ticker: str):
    """
    สร้าง Modal (หน้าต่างเด้ง) เพื่อแสดงกราฟแท่งเทียนของหุ้น
    """
    # 1. สร้างหน้าต่าง Dialog สีเข้ม
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-5xl h-[600px] bg-[#161B22] border border-gray-800 p-0 overflow-hidden relative'):
        
        # 2. แถบ Header ของหน้าต่างกราฟ
        with ui.row().classes('w-full bg-[#11141C] p-4 border-b border-gray-800 justify-between items-center z-10'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('candlestick_chart', size='sm').classes('text-[#D0FD3E]')
                ui.label(f'{ticker} - Live Candlestick (1M)').classes('text-xl font-black text-white tracking-wider')
            
            # ปุ่มปิดหน้าต่าง
            ui.button(icon='close', on_click=dialog.close).props('flat dense').classes('text-gray-400 hover:text-[#FF453A] transition-colors')

        # 3. พื้นที่วาดกราฟ
        with ui.column().classes('w-full h-[500px] p-4 relative'):
            # ดึงข้อมูลจาก Yahoo Finance (ใช้ await เพราะอาจจะใช้เวลาโหลดนิดนึง)
            # เราเขียนฟังก์ชัน get_candlestick_data ไว้แล้วใน services/yahoo_finance.py
            raw_data = get_candlestick_data(ticker, period="1mo")
            
            if not raw_data:
                ui.label(f'ไม่พบข้อมูลกราฟสำหรับ {ticker}').classes('text-gray-500 absolute-center')
            else:
                # แปลงข้อมูลให้เข้าฟอร์แมตของ ECharts
                # ECharts ต้องการ format: [open, close, lowest, highest]
                dates = [item['date'] for item in raw_data]
                values = [
                    [item['open'], item['close'], item['low'], item['high']]
                    for item in raw_data
                ]

                # 4. วาดกราฟด้วย ECharts
                ui.echart({
                    'tooltip': {
                        'trigger': 'axis',
                        'axisPointer': {'type': 'cross'}
                    },
                    'grid': {'left': '10%', 'right': '10%', 'bottom': '15%'},
                    'xAxis': {
                        'type': 'category',
                        'data': dates,
                        'boundaryGap': False,
                        'axisLine': {'onZero': False, 'lineStyle': {'color': '#8B949E'}},
                        'splitLine': {'show': False},
                        'min': 'dataMin',
                        'max': 'dataMax'
                    },
                    'yAxis': {
                        'scale': True,
                        'splitArea': {'show': True, 'areaStyle': {'color': ['rgba(255,255,255,0.02)', 'rgba(255,255,255,0.05)']}},
                        'axisLine': {'lineStyle': {'color': '#8B949E'}},
                        'splitLine': {'lineStyle': {'color': '#1C2128', 'type': 'dashed'}}
                    },
                    'dataZoom': [
                        {'type': 'inside', 'start': 0, 'end': 100},
                        {'show': True, 'type': 'slider', 'bottom': '5%', 'start': 0, 'end': 100, 'textStyle': {'color': '#8B949E'}}
                    ],
                    'series': [{
                        'name': ticker,
                        'type': 'candlestick',
                        'data': values,
                        'itemStyle': {
                            'color': COLORS['success'],       # แท่งเขียว (ราคาปิด > ราคาเปิด)
                            'color0': COLORS['danger'],       # แท่งแดง (ราคาปิด < ราคาเปิด)
                            'borderColor': COLORS['success'], 
                            'borderColor0': COLORS['danger']
                        }
                    }]
                }).classes('w-full h-full')

    # สั่งเปิดหน้าต่างทันทีที่เรียกฟังก์ชันนี้
    dialog.open()