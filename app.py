from nicegui import ui, app, run
from core.config import COLORS

# นำเข้าชิ้นส่วน UI สุดล้ำของคุณ
from web.components.ticker import create_ticker
from web.components.stats import create_stats_cards
from web.components.table import create_portfolio_table
from web.components.charts import show_candlestick_chart

# นำเข้าบริการดึงข้อมูล
from services.yahoo_finance import get_sparkline_data, get_live_price
from services.news_fetcher import fetch_stock_news_summary

# นำเข้า Database และ Auth
from core.models import get_portfolio, update_portfolio_stock, delete_portfolio_stock
from web.auth import login_page, require_login, logout

# --- ตั้งค่าหน้าเว็บ ---
def apply_global_style():
    """ตั้งค่า CSS พื้นฐานและ Font"""
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">')

# --- ฟังก์ชันจัดการปุ่มกด (Callbacks) ---
async def handle_edit(ticker):
    user_id = app.storage.user.get('user_id')
    portfolio = get_portfolio(user_id)
    asset = next((a for a in portfolio if a['ticker'] == ticker), None)
    
    if not asset: 
        ui.notify('ไม่พบข้อมูลหุ้นนี้ในพอร์ต', type='negative')
        return

    with ui.dialog() as dialog, ui.card().classes('w-96 bg-[#161B22] border border-gray-800 p-6 rounded-xl shadow-xl'):
        ui.label(f'✏️ แก้ไขข้อมูลพอร์ต: {ticker}').classes('text-xl font-bold text-white mb-4')
        
        shares_input = ui.number('จำนวนหุ้น', value=float(asset['shares']), format='%.4f').classes('w-full mb-4').props('outlined dark step=0.01')
        cost_input = ui.number('ราคาต้นทุนเฉลี่ย', value=float(asset['avg_cost']), format='%.2f').classes('w-full mb-6').props('outlined dark step=0.01')
        
        def save_edit():
            if update_portfolio_stock(user_id, ticker, shares_input.value, cost_input.value):
                ui.notify(f'✅ บันทึกข้อมูล {ticker} เรียบร้อย!', type='positive')
                dialog.close()
                ui.navigate.reload() # รีเฟรชหน้าเว็บให้ข้อมูลอัปเดต
            else:
                ui.notify('❌ เกิดข้อผิดพลาดในการบันทึกข้อมูล', type='negative')
                
        def delete_asset():
            if delete_portfolio_stock(user_id, ticker):
                ui.notify(f'🗑️ ลบ {ticker} ออกจากพอร์ตแล้ว', type='warning')
                dialog.close()
                ui.navigate.reload()
            else:
                ui.notify('❌ เกิดข้อผิดพลาดในการลบข้อมูล', type='negative')
        
        with ui.row().classes('w-full justify-between mt-2'):
            ui.button('ลบหุ้นนี้', on_click=delete_asset).classes('bg-red-500 text-white font-bold px-4 py-2 rounded-lg hover:bg-red-700')
            with ui.row().classes('gap-2'):
                ui.button('ยกเลิก', on_click=dialog.close).classes('bg-gray-600 text-white font-bold px-4 py-2 rounded-lg hover:bg-gray-500')
                ui.button('บันทึก', on_click=save_edit).classes('bg-[#D0FD3E] text-black font-black px-4 py-2 rounded-lg hover:bg-[#b5e62b]')
    
    dialog.open()

async def handle_news(ticker):
    with ui.dialog() as dialog, ui.card().classes('w-[500px] max-w-full bg-[#161B22] border border-gray-800 p-6 rounded-xl shadow-xl'):
        ui.label(f'📰 เจาะลึกข่าวล่าสุด: {ticker}').classes('text-xl font-bold text-[#D0FD3E] mb-2')
        ui.label('ให้ AI ช่วยสรุปข่าวด่วนประจำสัปดาห์...').classes('text-gray-400 text-sm mb-4')
        
        loading_spinner = ui.spinner(size='lg', color='#D0FD3E').classes('mx-auto my-8')
        news_container = ui.column().classes('w-full gap-2')
        
        ui.button('ปิดหน้าต่าง', on_click=dialog.close).classes('w-full mt-6 bg-gray-700 text-white font-bold rounded-lg py-2 hover:bg-gray-600')
    
    dialog.open()
    
    # รันฟังก์ชันดึงข่าว AI เป็น Background Task
    summary = await run.io_bound(fetch_stock_news_summary, ticker)
    
    loading_spinner.delete()
    with news_container:
        ui.markdown(summary).classes('text-gray-200 leading-relaxed text-sm')

async def handle_chart(ticker):
    # เรียกใช้ Modal ขั้นเทพที่คุณเขียนไว้ใน charts.py
    await show_candlestick_chart(ticker)

# --- หน้า Login ---
@ui.page('/login')
def login_route():
    apply_global_style()
    login_page()

# --- หน้าหลัก (Dashboard) ---
@ui.page('/')
async def main_page():
    if not require_login():
        return
        
    apply_global_style()
    
    # 1. แถบ Ticker วิ่งๆ (กระจกฝ้าของคุณ)
    create_ticker()

    with ui.column().classes('w-full max-w-7xl mx-auto p-6 gap-8 pt-12'): # เพิ่ม pt-12 หลบแถบ Ticker
        
        with ui.row().classes('w-full justify-between items-end mt-4'):
            with ui.column().classes('gap-0'):
                ui.label('APEX WEALTH MASTER').classes('text-5xl font-black italic text-[#D0FD3E] tracking-tighter shadow-neon')
                ui.label('INSTITUTIONAL GRADE DASHBOARD').classes('text-gray-500 text-xs tracking-[0.3em] font-bold')
            
            with ui.row().classes('gap-4'):
                ui.button('LOGOUT', icon='logout', on_click=logout) \
                    .classes('bg-[#FF453A] text-white font-black rounded-full px-6 hover:bg-red-700 transition-colors')

        # ดึงข้อมูลจากฐานข้อมูลจริง
        user_id = app.storage.user.get('user_id')
        raw_portfolio = get_portfolio(user_id)
        
        assets = []
        for item in raw_portfolio:
            assets.append({
                'ticker': item['ticker'],
                'shares': float(item['shares']),
                'avg_cost': float(item['avg_cost']),
                'last_price': 0,
                'sparkline': [],
                'is_up': True
            })

        total_invested = 0
        net_worth = 0 # 🌟 เปลี่ยนมาใช้ตัวแปร net_worth ให้ตรงกับ stats.py ของคุณ

        for asset in assets:
            price = get_live_price(asset['ticker'])
            spark, is_up = get_sparkline_data(asset['ticker'])
            
            asset['last_price'] = price
            asset['sparkline'] = spark
            asset['is_up'] = is_up
            
            total_invested += asset['shares'] * asset['avg_cost']
            net_worth += asset['shares'] * price

        total_profit = net_worth - total_invested

        # 2. แสดงการ์ดสรุปผล (Stats) แบบเรืองแสง
        create_stats_cards(total_invested, net_worth, total_profit)

        # 3. แสดงตารางหุ้น (Table) ที่มี ECharts ฝังอยู่
        create_portfolio_table(
            assets, 
            on_edit=handle_edit, 
            on_news=handle_news, 
            on_chart=handle_chart
        )

# --- เริ่มต้นระบบ ---
if __name__ in {"__main__", "__mp_main__"}:
    try:
        app.add_static_files('/static', 'static')
    except ValueError:
        pass 
        
    ui.run(
        title='Apex Wealth Master',
        favicon='🚀',
        dark=True,
        port=8080,
        reload=True,
        storage_secret='apex_super_secret_key_2026'
    )
