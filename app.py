from nicegui import ui, app
from core.config import COLORS

# นำเข้าชิ้นส่วน UI ที่เราสร้างไว้
from web.components.ticker import create_ticker
from web.components.stats import create_stats_cards
from web.components.table import create_portfolio_table
from web.components.charts import show_candlestick_chart

# นำเข้าบริการดึงข้อมูล
from services.yahoo_finance import get_sparkline_data, get_live_price

# --- ตั้งค่าหน้าเว็บ ---
def apply_global_style():
    """ตั้งค่า CSS พื้นฐานและ Font"""
    ui.query('body').style(f'background-color: {COLORS["bg"]}; font-family: "Inter", sans-serif;')
    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">')

# --- ฟังก์ชันจัดการปุ่มกด (Callbacks) ---
def handle_edit(ticker):
    ui.notify(f'Edit Stock: {ticker} (ฟังก์ชันนี้จะเชื่อมกับ DB เร็วๆ นี้)', type='info')

def handle_news(ticker):
    ui.notify(f'Fetching News for {ticker}... (Coming Soon)', type='warning')

async def handle_chart(ticker):
    ui.notify(f'Loading Chart for {ticker}...', color='positive')
    await show_candlestick_chart(ticker)

# --- หน้าหลัก (Dashboard) ---
@ui.page('/')
async def main_page():
    apply_global_style()
    
    # 1. ส่วนหัว Ticker (วิ่งตลอดเวลา)
    create_ticker()

    with ui.column().classes('w-full max-w-7xl mx-auto p-6 gap-8'):
        
        # 2. หัวข้อใหญ่ + ปุ่ม Add Asset
        with ui.row().classes('w-full justify-between items-end mt-4'):
            with ui.column().classes('gap-0'):
                ui.label('APEX WEALTH MASTER').classes('text-5xl font-black italic text-[#D0FD3E] tracking-tighter shadow-neon')
                ui.label('INSTITUTIONAL GRADE DASHBOARD').classes('text-gray-500 text-xs tracking-[0.3em] font-bold')
            
            ui.button('ADD ASSET', icon='add', on_click=lambda: ui.notify('ใช้ Telegram Bot เพื่อเพิ่มหุ้นนะครับ', type='info')) \
                .classes('bg-white text-black font-black rounded-full px-6 hover:bg-[#D0FD3E] transition-colors')

        # 3. ข้อมูลจำลอง (Mock Data) - เดี๋ยวเราจะเปลี่ยนไปดึงจาก Supabase ในขั้นตอนต่อไป
        # เพื่อให้เห็นหน้าตาสวยๆ ก่อน ผมขอใส่ข้อมูลตัวอย่างไว้ครับ
        mock_assets = [
            {'ticker': 'NVDA', 'shares': 10, 'avg_cost': 450.00, 'last_price': 0, 'sparkline': []},
            {'ticker': 'MSFT', 'shares': 20, 'avg_cost': 320.00, 'last_price': 0, 'sparkline': []},
            {'ticker': 'TSLA', 'shares': 50, 'avg_cost': 210.00, 'last_price': 0, 'sparkline': []},
            {'ticker': 'AAPL', 'shares': 100, 'avg_cost': 175.00, 'last_price': 0, 'sparkline': []},
        ]

        # โหลดข้อมูลจริง (ราคา + กราฟเส้นจิ๋ว)
        # หมายเหตุ: การทำแบบนี้ใน Loop อาจจะช้าถ้าหุ้นเยอะ เดี๋ยวเราจะย้ายไปทำ Background Task ทีหลัง
        total_invested = 0
        current_value = 0

        for asset in mock_assets:
            # ดึงราคาและ Sparkline จริงจาก Yahoo Finance
            price = get_live_price(asset['ticker'])
            spark, is_up = get_sparkline_data(asset['ticker'])
            
            asset['last_price'] = price
            asset['sparkline'] = spark
            asset['is_up'] = is_up
            
            total_invested += asset['shares'] * asset['avg_cost']
            current_value += asset['shares'] * price

        total_profit = current_value - total_invested

        # 4. แสดงการ์ดสรุปผล (Stats)
        create_stats_cards(total_invested, current_value, total_profit)

        # 5. แสดงตารางหุ้น (Table)
        # ส่งฟังก์ชัน handle_... เข้าไปเพื่อให้ปุ่มในตารางทำงานได้
        create_portfolio_table(
            mock_assets, 
            on_edit=handle_edit, 
            on_news=handle_news, 
            on_chart=handle_chart
        )

# --- เริ่มต้นระบบ ---
if __name__ in {"__main__", "__mp_main__"}:
    app.add_static_files('/static', 'static') # เผื่อใส่รูปโลโก้
    ui.run(
        title='Apex Wealth Master',
        favicon='🚀',
        dark=True,
        port=8080,
        reload=True # แก้โค้ดแล้วรีเฟรชเองไม่ต้องปิดเปิดใหม่
    )