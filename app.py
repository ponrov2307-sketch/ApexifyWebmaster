from nicegui import ui, app, run
from core.config import COLORS
import random
import pandas as pd
from datetime import datetime
import asyncio

# Components & Services
from web.components.ticker import create_ticker
from web.components.stats import create_stats_cards
from web.components.table import create_portfolio_table
from web.components.charts import show_candlestick_chart
from services.yahoo_finance import get_sparkline_data, get_live_price, update_global_cache_batch, get_real_dividend_data, get_portfolio_historical_growth
from services.news_fetcher import fetch_stock_news_summary
from services.gemini_ai import generate_apexify_report

# DB & Auth
from core.models import get_portfolio, add_portfolio_stock, update_portfolio_stock, delete_portfolio_stock, get_user_by_telegram, get_all_unique_tickers
from web.auth import login_page, require_login, logout
from web.router import standard_page_frame

ui.add_head_html('''
    <style>
        @keyframes pulse-green {
            0%, 100% { text-shadow: 0 0 0px transparent; color: #32D74B; }
            50% { text-shadow: 0 0 15px rgba(50,215,75,0.6); color: #D0FD3E; }
        }
        @keyframes pulse-red {
            0%, 100% { text-shadow: 0 0 0px transparent; color: #FF453A; }
            50% { text-shadow: 0 0 15px rgba(255,69,58,0.6); color: #ff857f; }
        }
        .blink-green { animation: pulse-green 2s infinite ease-in-out; }
        .blink-red { animation: pulse-red 2s infinite ease-in-out; }
    </style>
''', shared=True)


# ==========================================
# 🌟 ระบบเบื้องหลัง (Background Worker)
# ==========================================
async def global_market_updater():
    """ตัวแทน 1 เดียวที่จะไปดึงราคาหุ้นทั้งหมดมาจาก Yahoo (กันเว็บโดนแบน)"""
    while True:
        try:
            # ดึงรายชื่อหุ้นทั้งหมดที่ไม่ซ้ำกันจากฐานข้อมูล
            tickers = get_all_unique_tickers()
            if tickers:
                # ให้รันใน thread แยกเพื่อไม่ให้หน้าเว็บกระตุก
                await run.io_bound(update_global_cache_batch, tickers)
        except Exception as e:
            print(f"Global Updater Error: {e}")
        
        # ถ้านอกเวลาตลาดปิด ให้พักผ่อน อัปเดตชั่วโมงละ 1 ครั้งพอ ประหยัดแบตเซิร์ฟเวอร์
        current_hour = datetime.now().hour
        is_market_open = (current_hour >= 20) or (current_hour <= 4)
        sleep_time = 30 if is_market_open else 3600
        
        await asyncio.sleep(sleep_time)

# 🌟 สั่งให้ Worker ทำงานทันทีที่เปิดรันโค้ด
app.on_startup(lambda: asyncio.create_task(global_market_updater()))


# ==========================================
# 🛠️ ฟังก์ชันช่วยเหลือ (MODALS & POPUPS)
# ==========================================

async def handle_add_asset():
    app.storage.client['modal_open'] = True
    user_id = app.storage.user.get('user_id')
    tid = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(tid) if tid else {}
    role = str(user_info.get('role', 'free')).lower()
    if not user_id: return

    portfolio = get_portfolio(user_id)
    current_count = len(portfolio)
    limit = 3 if role == 'free' else (10 if role == 'vip' else 9999) 
    
    # 🌟 ธีมพรีเมียมระดับโลก
    with ui.dialog() as dialog, ui.card().classes('w-[450px] bg-[#0D1117]/80 backdrop-blur-2xl border border-white/10 p-0 rounded-3xl overflow-hidden shadow-[0_0_40px_rgba(0,0,0,0.8)]'):
        with ui.row().classes('w-full bg-gradient-to-r from-[#161B22] to-[#1C2128] p-5 border-b border-white/5 justify-between items-center'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('add_circle', size='sm').classes('text-[#D0FD3E]')
                ui.label('ADD NEW ASSET').classes('text-xl font-black text-white tracking-[0.2em]')
            ui.button(icon='close', on_click=dialog.close).props('flat dense round').classes('text-gray-500 hover:text-[#FF453A] transition-colors')
        
        with ui.column().classes('p-6 w-full gap-5'):
            # 🌟 ลิงก์เพิ่มหุ้นผ่าน Telegram
            with ui.row().classes('w-full justify-center mb-1'):
                ui.button('เพิ่มหุ้นผ่าน Telegram Bot (สะดวกกว่า)', icon='telegram', on_click=lambda: ui.navigate.to('https://t.me/Apexify_Trading_bot', new_tab=True)).classes('w-full bg-[#0088cc] text-white font-bold py-2 rounded-xl shadow-lg hover:bg-[#0077b5] transition-all')
            
            ui.element('div').classes('w-full h-[1px] bg-gradient-to-r from-transparent via-gray-700 to-transparent my-1')

            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-[2] gap-1'):
                    ui.label('Ticker Symbol').classes('text-xs text-gray-400 font-bold tracking-wider')
                    ticker_input = ui.input(placeholder='เช่น AAPL').classes('w-full').props('outlined dark autofocus rounded')
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('Group').classes('text-xs text-gray-400 font-bold tracking-wider')
                    group_input = ui.select(['ALL', 'DCA', 'DIV', 'TRADING'], value='ALL').classes('w-full').props('outlined dark rounded')

            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('Shares (จำนวน)').classes('text-xs text-gray-400 font-bold tracking-wider')
                    shares_input = ui.number(format='%.6f').classes('w-full').props('outlined dark step=0.01 rounded')
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('Avg Cost (ต้นทุน)').classes('text-xs text-gray-400 font-bold tracking-wider')
                    cost_input = ui.number(format='%.4f').classes('w-full').props('outlined dark step=0.01 rounded')

            def save_new_asset():
                t, s, c, g = ticker_input.value, shares_input.value, cost_input.value, group_input.value
                if not t or s is None or c is None: 
                    ui.notify('⚠️ กรุณากรอกข้อมูลให้ครบถ้วน', type='warning')
                    return
                
                is_existing = any(a['ticker'] == t.upper() for a in portfolio)
                if not is_existing and current_count >= limit:
                    ui.notify(f'🔒 สิทธิ์ {role.upper()} สร้าง Watchlist ได้สูงสุด {limit} ตัวครับ กรุณาอัปเกรด!', type='warning')
                    dialog.close()
                    return

                if add_portfolio_stock(user_id, t.upper(), float(s), float(c), g): 
                    ui.notify(f'✅ เพิ่มหุ้น {t.upper()} เข้ากลุ่ม {g} สำเร็จ!', type='positive')
                    dialog.close()
                    ui.navigate.reload()

            ui.button('ADD TO PORTFOLIO', on_click=save_new_asset).classes('w-full bg-gradient-to-r from-[#D0FD3E] to-[#32D74B] text-black font-black py-3 rounded-xl mt-2 shadow-[0_0_15px_rgba(50,215,75,0.4)] hover:scale-[1.02] transition-all')

    dialog.on('hide', lambda: app.storage.client.update({'modal_open': False}))
    dialog.open()

async def handle_edit(ticker):
    app.storage.client['modal_open'] = True
    user_id = app.storage.user.get('user_id')
    if not user_id: return

    portfolio = get_portfolio(user_id)
    asset = next((a for a in portfolio if a['ticker'] == ticker), None)
    if not asset: return

    current_price = get_live_price(ticker)

    # 🌟 ธีม Glassmorphism พรีเมียม
    with ui.dialog() as dialog, ui.card().classes('w-[450px] bg-[#0D1117]/80 backdrop-blur-2xl border border-white/10 p-0 rounded-3xl overflow-hidden shadow-[0_0_40px_rgba(0,0,0,0.8)]'):
        with ui.row().classes('w-full bg-gradient-to-r from-[#161B22] to-[#1C2128] p-5 border-b border-white/5 justify-between items-center'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('tune', size='sm').classes('text-[#D0FD3E]')
                ui.label('EDIT ASSET').classes('text-xl font-black text-white tracking-[0.2em]')
            ui.button(icon='close', on_click=dialog.close).props('flat dense round').classes('text-gray-500 hover:text-[#FF453A] transition-colors')
        
        with ui.column().classes('p-6 w-full gap-5'):
            # ส่วนหัวโชว์ราคา
            with ui.row().classes('w-full justify-between items-center bg-[#11141C]/50 p-4 rounded-2xl border border-white/5 shadow-inner'):
                with ui.column().classes('gap-0'):
                    ui.label(ticker).classes('text-2xl font-black text-white tracking-wider')
                    ui.label('Current Market Price').classes('text-[10px] text-gray-500 uppercase tracking-widest font-bold')
                ui.label(f"${current_price:,.2f}").classes('text-3xl font-black text-[#D0FD3E] drop-shadow-[0_0_10px_rgba(208,253,62,0.3)]')
            
            ui.element('div').classes('w-full h-[1px] bg-gradient-to-r from-transparent via-gray-700 to-transparent my-1')

            # ฟอร์มแก้ไข
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('Shares (จำนวน)').classes('text-xs text-gray-400 font-bold tracking-wider')
                    shares_input = ui.number(value=float(asset['shares']), format='%.6f').classes('w-full').props('outlined dark step=0.01 rounded')
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('Avg Cost (ต้นทุน)').classes('text-xs text-gray-400 font-bold tracking-wider')
                    cost_input = ui.number(value=float(asset['avg_cost']), format='%.4f').classes('w-full').props('outlined dark step=0.01 rounded')

            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('Price Alert (แจ้งเตือน)').classes('text-xs text-gray-400 font-bold tracking-wider')
                    ui.number(value=current_price*0.95, format='%.2f').classes('w-full').props('outlined dark rounded')
                with ui.column().classes('flex-1 gap-1'):
                    ui.label('Strategy Group').classes('text-xs text-gray-400 font-bold tracking-wider')
                    asset_group_select = ui.select(['DCA', 'DIV', 'TRADING', 'ALL'], value=asset.get('asset_group', 'ALL')).classes('w-full').props('outlined dark rounded')

            def save_edit():
                if update_portfolio_stock(user_id, ticker, shares_input.value, cost_input.value, asset_group_select.value):
                    ui.notify(f'✅ บันทึกข้อมูล {ticker} สำเร็จ!', type='positive')
                    dialog.close()
                    ui.navigate.reload()

            def confirm_delete():
                if delete_portfolio_stock(user_id, ticker):
                    ui.notify(f'🗑️ ลบ {ticker} ออกจากพอร์ตแล้ว', type='warning')
                    dialog.close()
                    ui.navigate.reload()

            # กลุ่มปุ่มกด
            with ui.row().classes('w-full gap-4 mt-2'):
                ui.button('DELETE', on_click=confirm_delete).classes('flex-1 bg-[#FF453A]/10 text-[#FF453A] border border-[#FF453A]/30 font-black py-3 rounded-xl hover:bg-[#FF453A] hover:text-white transition-all')
                ui.button('SAVE CHANGES', on_click=save_edit).classes('flex-[2] bg-gradient-to-r from-[#D0FD3E] to-[#32D74B] text-black font-black py-3 rounded-xl shadow-[0_0_15px_rgba(50,215,75,0.4)] hover:scale-[1.02] transition-all')

    dialog.on('hide', lambda: app.storage.client.update({'modal_open': False}))
    dialog.open()

async def handle_news(ticker):
    app.storage.client['modal_open'] = True
    current_price = get_live_price(ticker)
    clean_ticker = ticker.replace('.BK', '').lower()
    
    logo_url = f"https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.{clean_ticker}.com&size=128"

    user_id = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(user_id) if user_id else {}
    role = str(user_info.get('role', 'free')).lower()

    # 🌟 จำลองข้อมูล Analyst Target (สามารถต่อ API ในอนาคต)
    target_price = current_price * random.uniform(1.05, 1.25)
    upside = ((target_price - current_price) / current_price) * 100

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl h-[750px] bg-[#0D1117] border border-gray-800 p-0 rounded-3xl shadow-2xl flex flex-col'):
        with ui.row().classes('w-full bg-[#161B22] p-6 border-b border-gray-800 items-center justify-between shrink-0'):
            with ui.row().classes('items-center gap-4'):
                ui.image(logo_url).classes('w-16 h-16 rounded-xl bg-white p-1 shadow-inner')
                with ui.column().classes('gap-0'):
                    ui.label(f"{ticker} Insights").classes('text-3xl font-black text-white tracking-widest')
                    ui.label(f"Current: ${current_price:,.2f}").classes('text-xl font-bold text-[#D0FD3E]')
            ui.button(icon='close', on_click=dialog.close).props('flat dense').classes('text-gray-400 hover:text-[#FF453A]')

        with ui.column().classes('p-6 w-full gap-6 overflow-y-auto custom-scrollbar flex-1'):
            
            # 🌟 สถิติ & Analyst Target
            with ui.row().classes('w-full gap-4 items-stretch'):
                with ui.grid(columns=3).classes('flex-[2] gap-4 bg-[#161B22] p-5 rounded-2xl border border-white/5'):
                    stats = [('Market Cap', '$3.01T'), ('P/E Ratio', '32.14'), ('EPS', '6.42'), ('Beta (Vol)', '1.25'), ('52W High', f"${current_price*1.3:.2f}"), ('52W Low', f"${current_price*0.7:.2f}")]
                    for label, val in stats:
                        with ui.column().classes('gap-0'):
                            ui.label(label).classes('text-xs text-gray-500 font-bold')
                            ui.label(val).classes('text-sm font-black text-white')
                
                # 🌟 Analyst Target Card
                with ui.column().classes('flex-1 bg-gradient-to-br from-[#1C2128] to-[#11141C] p-5 rounded-2xl border border-[#D0FD3E]/30 items-center justify-center text-center shadow-[0_0_20px_rgba(208,253,62,0.1)]'):
                    ui.label('ANALYST TARGET (12M)').classes('text-[10px] font-black text-[#D0FD3E] tracking-widest')
                    ui.label(f"${target_price:,.2f}").classes('text-3xl font-black text-white my-1')
                    ui.label(f"Upside: +{upside:.1f}%").classes('text-sm font-bold text-[#32D74B]')

            # AI Sentiment
            with ui.column().classes('w-full bg-[#161B22]/50 border border-gray-800 rounded-2xl p-6 items-center text-center relative'):
                ui.icon('smart_toy', size='sm').classes('text-[#D0FD3E] mb-1')
                ui.label('AI SENTIMENT ANALYSIS').classes('text-xs font-black text-[#D0FD3E] tracking-widest mb-2')
                loading_ai = ui.spinner('dots', size='lg', color='#D0FD3E')
                ai_content = ui.column().classes('items-center gap-2 hidden w-full')
                with ai_content:
                    ai_text = ui.label('').classes('text-sm text-gray-300 leading-relaxed text-center')

            # News
            ui.label('RECENT NEWS & IMPACT').classes('text-xs font-black text-gray-500 tracking-widest mt-2 -mb-2')
            loading_news = ui.spinner('dots', size='md', color='white').classes('mx-auto mt-4')
            news_container = ui.column().classes('w-full gap-3 hidden')
            with news_container:
                news_summary_text = ui.label('').classes('text-sm text-gray-300 bg-[#161B22] p-5 rounded-2xl border border-gray-800 w-full')

    dialog.on('hide', lambda: app.storage.client.update({'modal_open': False}))
    dialog.open()

    tech_data = {'symbol': ticker, 'price': current_price, 'rsi': random.randint(30,70), 'ema20': current_price*0.98, 'ema50': current_price*0.95, 'ema200': current_price*0.9}
    ai_report = await run.io_bound(generate_apexify_report, tech_data, role)
    news_summary = await run.io_bound(fetch_stock_news_summary, ticker)
    
    loading_ai.set_visibility(False)
    ai_content.classes(remove='hidden')
    ai_text.set_text(ai_report)

    loading_news.set_visibility(False)
    news_container.classes(remove='hidden')
    news_summary_text.set_text(news_summary)
async def handle_chart(ticker):
    app.storage.client['modal_open'] = True
    await show_candlestick_chart(ticker)


# ==========================================
# 1. หน้าต่างเข้าสู่ระบบ (LOGIN PAGE)
# ==========================================
@ui.page('/login')
def login_route():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    login_page()


# ==========================================
# 2. หน้าหลัก (DASHBOARD) - REAL-TIME
# ==========================================
@ui.page('/')
@standard_page_frame
async def main_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker() 

    @ui.refreshable
    def dashboard_content():
        user_id = app.storage.user.get('user_id')
        telegram_id = app.storage.user.get('telegram_id')
        
        # 🌟 ป้องกัน NoneType Error อย่างเด็ดขาด!
        user_info = get_user_by_telegram(telegram_id)
        if user_info is None:
            user_info = {} # 🌟 ถ้าหาไม่เจอ ให้คืนค่าเป็น Dictionary ว่างๆ ป้องกัน Error
            
        lang = app.storage.user.get('lang', 'TH')
        currency = app.storage.user.get('currency', 'USD')
        curr_sym = '฿' if currency == 'THB' else '$'
        curr_rate = 34.5 if currency == 'THB' else 1.0 
        
        username = user_info.get('username', f'User_{str(telegram_id)[-4:]}' if telegram_id else 'Guest')
        role = str(user_info.get('role', 'free')).upper()
        role_color = 'text-[#D0FD3E]' if role in ['PRO', 'VIP', 'ADMIN'] else 'text-gray-400'
        
        expiry = user_info.get('vip_expiry')
        expiry_txt = f'Valid till: {expiry}' if expiry else 'No Expiry'
        status_txt = expiry_txt if role in ['PRO', 'VIP', 'ADMIN'] else 'Ready to trade'
        
        # ... (โค้ดดึง Portfolio ดำเนินการต่อจากตรงนี้ตามปกติ) ...
        raw_portfolio = get_portfolio(user_id) if user_id else []
        current_group = app.storage.client.get('dashboard_group', 'ALL')
        
        assets = []
        total_invested, net_worth = 0, 0

        for item in raw_portfolio:
            # 🌟 ตัดหุ้นที่ไม่ตรงกรุ๊ปทิ้งไปเลย! (จะไม่มีโผล่มาในตารางหรือยอดรวมอีก)
            if current_group != 'ALL' and item.get('asset_group', 'ALL') != current_group:
                continue
                
            t = item['ticker']
            shares = float(item['shares'])
            base_cost = float(item['avg_cost'])
            price = get_live_price(t)
            spark, is_up = get_sparkline_data(t, days=7)
            
            profit_pct = ((price - base_cost) / base_cost * 100) if base_cost > 0 else 0
            assets.append({'ticker': t, 'shares': shares, 'avg_cost': base_cost, 'last_price': price, 'sparkline': spark, 'is_up': is_up, 'profit_pct': profit_pct})
            total_invested += shares * (base_cost * curr_rate)
            net_worth += shares * (price * curr_rate)

        total_profit = net_worth - total_invested
        is_profit_overall = total_profit >= 0
        
        sorted_assets = sorted(assets, key=lambda x: x['profit_pct'], reverse=True)
        top_gainer = sorted_assets[0] if sorted_assets and sorted_assets[0]['profit_pct'] > 0 else None
        top_loser = sorted_assets[-1] if sorted_assets and sorted_assets[-1]['profit_pct'] < 0 else None

        with ui.column().classes('w-full max-w-7xl mx-auto p-8 gap-6 pt-16'):
            with ui.row().classes('w-full gap-4 items-stretch'):
                with ui.row().classes('flex-[2] justify-between items-center bg-[#161B22]/80 backdrop-blur-md p-5 rounded-3xl border border-white/5 shadow-lg'):
                    with ui.row().classes('items-center gap-4'):
                        ui.icon('account_circle', size='xl').classes(role_color)
                        with ui.column().classes('gap-0'):
                            ui.label(f'Welcome back, {username}').classes('text-xl font-black text-white tracking-wide')
                            with ui.row().classes('items-center gap-2 mt-1'):
                                ui.label(f'{role} MEMBER').classes(f'text-[10px] px-2 py-0.5 rounded border border-[{COLORS.get("primary")}]/30 bg-[{COLORS.get("primary")}]/10 {role_color} font-black tracking-widest')
                                ui.label(status_txt).classes('text-xs text-gray-500 font-bold')
                
                # 🌟 ฟังก์ชันจัดการตอนเปลี่ยนพอร์ต
                def change_portfolio_group(e):
                    app.storage.client['dashboard_group'] = e.value
                    dashboard_content.refresh()
                
                with ui.column().classes('flex-1 justify-center items-start bg-[#161B22]/80 backdrop-blur-md p-5 rounded-3xl border border-white/5 shadow-lg relative'):
                    ui.label('CURRENT PORTFOLIO').classes('text-[10px] text-gray-500 font-black tracking-widest uppercase mb-1')
                    ui.select(['ALL', 'DCA', 'TRADING', 'DIV'], value=current_group, on_change=change_portfolio_group).classes('w-full').props('outlined dark dense rounded')
                
                with ui.column().classes('flex-[1.5] justify-center items-center bg-gradient-to-r from-[#161B22] to-[#1C2128] p-5 rounded-3xl border border-white/5 shadow-lg'):
                    ui.label('MARKET SENTIMENT').classes('text-[10px] text-gray-500 font-black tracking-widest uppercase mb-1')
                    with ui.row().classes('items-baseline gap-2'):
                        ui.label('68').classes('text-4xl font-black text-[#32D74B]')
                        ui.label('GREED').classes('text-sm font-bold text-[#32D74B] tracking-wider')

            with ui.row().classes('w-full justify-between items-end mt-4 mb-2'):
                with ui.column().classes('gap-0'):
                    ui.label('TOTAL PORTFOLIO VALUE').classes('text-gray-400 font-bold tracking-widest text-xs mb-2')
                    with ui.row().classes('items-baseline gap-4'):
                        blink_class = 'blink-green' if is_profit_overall else 'blink-red'
                        color_class = 'text-[#32D74B]' if is_profit_overall else 'text-[#FF453A]'
                        sign = "+" if is_profit_overall else "-"
                        pct = (abs(total_profit) / total_invested * 100) if total_invested > 0 else 0
                        
                        ui.label(f'{curr_sym}{net_worth:,.2f}').classes(f'text-[70px] leading-none font-black {blink_class}')
                        ui.label(f'{"▲" if is_profit_overall else "▼"} {curr_sym}{abs(total_profit):,.2f} ({sign}{pct:.2f}%)').classes(f'text-2xl font-black {color_class}')
                        
                with ui.row().classes('items-center gap-4'):
                    if top_gainer:
                        with ui.column().classes('bg-[#32D74B]/10 border border-[#32D74B]/30 rounded-2xl p-3 items-end'):
                            ui.label('TOP GAINER').classes('text-[9px] text-[#32D74B] font-black tracking-widest')
                            ui.label(f"{top_gainer['ticker']} +{top_gainer['profit_pct']:.1f}%").classes('text-sm font-bold text-white')
                    if top_loser:
                        with ui.column().classes('bg-[#FF453A]/10 border border-[#FF453A]/30 rounded-2xl p-3 items-end'):
                            ui.label('TOP LOSER').classes('text-[9px] text-[#FF453A] font-black tracking-widest')
                            ui.label(f"{top_loser['ticker']} {top_loser['profit_pct']:.1f}%").classes('text-sm font-bold text-white')
                            
                    ui.button('+ ADD HOLDING', on_click=handle_add_asset, color='#D0FD3E').classes('text-black font-black rounded-2xl px-6 py-4 shadow-[0_0_15px_rgba(208,253,62,0.4)] hover:scale-105 transition-all ml-4')

            create_portfolio_table(assets, on_edit=handle_edit, on_news=handle_news, on_chart=handle_chart)

    dashboard_content()
    
    def smart_refresh():
        if app.storage.client.get('modal_open', False): return
        dashboard_content.refresh()

    ui.timer(15.0, smart_refresh)


# ==========================================
# 3. หน้าวิเคราะห์พอร์ต (ดึงกราฟ Growth จริง)
# ==========================================
@ui.page('/analytics')
@standard_page_frame
async def analytics_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker() 

    user_id = app.storage.user.get('user_id')
    raw_portfolio = get_portfolio(user_id) if user_id else []

    def get_filtered_data(group='ALL'):
        filtered = [item for item in raw_portfolio if group == 'ALL' or item.get('asset_group', 'ALL') == group]
        data = []
        total = 0
        for item in filtered:
            val = item['shares'] * get_live_price(item['ticker']) 
            total += val
            data.append({'ticker': item['ticker'], 'value': val, 'avg_cost': item['avg_cost'], 'shares': item['shares']})
        return sorted(data, key=lambda x: x['value'], reverse=True), total

    with ui.column().classes('w-full max-w-7xl mx-auto p-8 gap-6 pt-16 items-center'):
        
        # 🌟 Header & Risk Metrics Score
        with ui.row().classes('w-full justify-between items-center bg-[#161B22]/80 backdrop-blur-md p-6 rounded-3xl border border-white/5 shadow-lg'):
            with ui.column().classes('gap-1'):
                ui.label('PORTFOLIO ANALYTICS').classes('text-3xl font-black text-white tracking-widest uppercase')
                ui.label('Deep dive into your portfolio performance and AI strategy.').classes('text-sm text-gray-400')
            
            # Risk Widget
            with ui.row().classes('items-center gap-4 bg-[#0D1117] p-3 rounded-2xl border border-white/5'):
                with ui.column().classes('items-end gap-0'):
                    ui.label('PORTFOLIO BETA (RISK)').classes('text-[10px] font-black text-gray-500 tracking-widest')
                    ui.label('1.15 (Moderate)').classes('text-lg font-black text-white')
                ui.circular_progress(value=0.6, show_value=False, size='40px', color='warning').classes('text-orange-400')

        mode_toggle = ui.toggle(['Allocation', 'Real Growth', 'AI Rebalance', 'Sector Flow'], value='Allocation') \
            .classes('bg-[#161B22] text-gray-400 rounded-xl p-1 border border-gray-800 shadow-inner') \
            .props('unelevated dark color=positive text-color=white')

        with ui.row().classes('w-full gap-6 mt-2 items-stretch'):
            chart_card = ui.card().classes('flex-[2] bg-[#161B22]/80 backdrop-blur-md border border-white/5 p-0 rounded-3xl h-[550px] relative overflow-hidden shadow-xl')
            list_card = ui.column().classes('flex-[1] bg-[#161B22]/80 backdrop-blur-md border border-white/5 p-0 rounded-3xl h-[550px] overflow-hidden shadow-xl')

        current_group = {'val': 'ALL'}

        async def update_view(e=None):
            mode = mode_toggle.value
            chart_card.clear()
            list_card.clear()
            
            assets_data, total_value = get_filtered_data(current_group['val'])
            
            with chart_card:
                if not assets_data and mode != 'Sector Flow':
                    ui.label(f'No assets found in {current_group["val"]} group').classes('text-gray-500 absolute-center font-bold')
                elif mode == 'Allocation':
                    pie_data = [{'value': round(a['value'], 2), 'name': a['ticker']} for a in assets_data]
                    ui.echart({
                        'tooltip': {'trigger': 'item'},
                        'legend': {'orient': 'vertical', 'left': 'left', 'textStyle': {'color': '#8B949E'}},
                        'series': [{
                            'name': 'Portfolio', 'type': 'pie', 'radius': ['40%', '70%'],
                            'itemStyle': {'borderRadius': 10, 'borderColor': '#161B22', 'borderWidth': 2},
                            'label': {'show': True, 'position': 'outside', 'color': '#fff', 'formatter': '{b}\n{d}%'},
                            'data': pie_data
                        }]
                    }).classes('w-full h-full p-4')
                    with ui.column().classes('absolute-center items-center gap-0 pointer-events-none'):
                        ui.label(f"${total_value:,.0f}").classes('text-4xl font-black text-white drop-shadow-md')
                        ui.label('Total Value').classes('text-xs text-gray-500 font-bold uppercase tracking-widest')

                elif mode == 'Real Growth':
                    growth_dates, growth_values = await run.io_bound(get_portfolio_historical_growth, raw_portfolio)
                    ui.echart({
                        'tooltip': {'trigger': 'axis'},
                        'grid': {'left': '5%', 'right': '5%', 'bottom': '10%', 'top': '10%'},
                        'xAxis': {'type': 'category', 'boundaryGap': False, 'data': growth_dates, 'axisLine': {'lineStyle': {'color': '#8B949E'}}},
                        'yAxis': {'type': 'value', 'scale': True, 'splitLine': {'lineStyle': {'color': '#1C2128'}}},
                        'series': [{'data': growth_values, 'type': 'line', 'smooth': True, 'symbol': 'none', 'lineStyle': {'color': '#32D74B', 'width': 4}, 'areaStyle': {'color': """new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: 'rgba(50,215,75,0.3)'}, {offset: 1, color: 'rgba(50,215,75,0)'}])"""}}]
                    }).classes('w-full h-full p-4')

                elif mode == 'AI Rebalance':
                    # 🌟 AI Rebalance Manager UI
                    with ui.column().classes('w-full h-full p-8 items-center text-center justify-center bg-gradient-to-br from-[#0D1117] to-[#161B22]'):
                        ui.icon('auto_awesome', size='64px').classes('text-[#D0FD3E] drop-shadow-[0_0_15px_rgba(208,253,62,0.5)] mb-4')
                        ui.label('AI REBALANCE MANAGER').classes('text-2xl font-black text-white tracking-widest')
                        ui.label('Gemini AI กำลังวิเคราะห์สัดส่วนพอร์ตของคุณเพื่อแนะนำการปรับสมดุล (Rebalance) ที่ดีที่สุด เพื่อลดความเสี่ยงและเพิ่มผลตอบแทน').classes('text-gray-400 mt-2 max-w-lg')
                        
                        ui.button('GENERATE AI STRATEGY', icon='bolt').classes('mt-8 bg-[#32D74B] text-black font-black py-3 px-8 rounded-full shadow-[0_0_20px_rgba(50,215,75,0.4)] hover:scale-105 transition-transform')
                
                elif mode == 'Sector Flow':
                    # 🌟 Sector Rotation Flow UI
                    ui.label('SECTOR ROTATION FLOW (MARKET TREND)').classes('text-lg font-black text-white tracking-widest absolute top-6 left-6 z-10')
                    
                    sectors = ['Technology', 'Healthcare', 'Financials', 'Energy', 'Consumer Discretionary']
                    flows = [('Tech', 4.5), ('Healthcare', 1.2), ('Finance', -0.5), ('Energy', -2.3), ('Consumer', 0.8)]
                    
                    ui.echart({
                        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
                        'grid': {'left': '15%', 'right': '10%', 'bottom': '15%', 'top': '25%'},
                        'xAxis': {'type': 'value', 'splitLine': {'lineStyle': {'color': '#1C2128', 'type': 'dashed'}}, 'axisLabel': {'color': '#8B949E'}},
                        'yAxis': {'type': 'category', 'data': [f[0] for f in flows], 'axisLine': {'show': False}, 'axisLabel': {'color': '#fff', 'fontWeight': 'bold'}},
                        'series': [
                            {
                                'name': 'Net Money Flow (%)',
                                'type': 'bar',
                                'data': [
                                    {'value': f[1], 'itemStyle': {'color': '#32D74B' if f[1] > 0 else '#FF453A', 'borderRadius': [0,5,5,0] if f[1] > 0 else [5,0,0,5]}}
                                    for f in flows
                                ],
                                'label': {'show': True, 'position': 'right', 'formatter': '{c}%', 'color': '#fff'}
                            }
                        ]
                    }).classes('w-full h-full p-4 mt-6')

            with list_card:
                with ui.row().classes('w-full bg-[#11141C] p-5 border-b border-gray-800 text-xs text-gray-500 font-bold tracking-widest justify-between'):
                    ui.label('ASSET')
                    ui.label('ACTION' if mode == 'AI Rebalance' else 'VALUE')

                with ui.column().classes('w-full p-3 overflow-y-auto custom-scrollbar gap-2'):
                    if mode == 'Sector Flow':
                        # โชว์รายชื่อ Sector ที่เงินไหลเข้า
                        for name, flow in [('Tech', 4.5), ('Healthcare', 1.2), ('Consumer', 0.8)]:
                            with ui.row().classes('w-full justify-between items-center p-4 bg-[#32D74B]/10 rounded-2xl border border-[#32D74B]/20'):
                                with ui.row().classes('items-center gap-3'):
                                    ui.icon('trending_up', size='sm').classes('text-[#32D74B]')
                                    ui.label(name).classes('font-black text-white tracking-wide text-lg')
                                ui.label(f"INFLOW").classes('text-[#32D74B] font-bold text-xs bg-[#32D74B]/20 px-2 py-1 rounded')
                        for name, flow in [('Energy', -2.3), ('Finance', -0.5)]:
                            with ui.row().classes('w-full justify-between items-center p-4 bg-[#FF453A]/10 rounded-2xl border border-[#FF453A]/20 mt-2'):
                                with ui.row().classes('items-center gap-3'):
                                    ui.icon('trending_down', size='sm').classes('text-[#FF453A]')
                                    ui.label(name).classes('font-black text-white tracking-wide text-lg')
                                ui.label(f"OUTFLOW").classes('text-[#FF453A] font-bold text-xs bg-[#FF453A]/20 px-2 py-1 rounded')
                    else:
                        for a in assets_data:
                            with ui.row().classes('w-full justify-between items-center p-4 hover:bg-[#1C2128] rounded-2xl transition-colors border border-transparent hover:border-white/5'):
                                with ui.row().classes('items-center gap-3'):
                                    ui.element('div').classes('w-1.5 h-6 rounded-full bg-[#D0FD3E]')
                                    ui.label(a['ticker']).classes('font-black text-white tracking-wide text-lg')
                                
                                if mode == 'AI Rebalance':
                                    action = random.choice(['BUY MORE', 'TAKE PROFIT', 'HOLD'])
                                    color = '#32D74B' if action == 'BUY MORE' else ('#FF453A' if action == 'TAKE PROFIT' else '#8B949E')
                                    ui.label(action).style(f'color: {color}; font-size: 11px; font-weight: 900; letter-spacing: 1px; padding: 4px 8px; border-radius: 6px; background-color: {color}15;')
                                else:
                                    pct = (a['value'] / total_value) * 100 if total_value > 0 else 0
                                    with ui.row().classes('gap-4 text-sm items-center'):
                                        ui.label(f"${a['value']:,.0f}").classes('text-gray-300 font-bold')
                                        ui.label(f"{pct:.1f}%").classes('text-white font-black w-14 text-right bg-white/10 py-1 rounded')

        mode_toggle.on('update:model-value', lambda e: ui.timer(0.1, update_view, once=True))
        
        def set_group(g):
            current_group['val'] = g
            ui.timer(0.1, update_view, once=True)

        with ui.row().classes('bg-[#161B22] rounded-xl p-1.5 border border-white/5 mt-2 gap-1 shadow-lg'):
            for g in ['ALL', 'DCA', 'DIV', 'TRADING']:
                btn = ui.button(g, on_click=lambda g=g: set_group(g)).props('flat size=sm').classes('font-bold tracking-widest')
                if current_group['val'] == g:
                    btn.classes('bg-[#D0FD3E] text-black')
                else:
                    btn.classes('text-gray-500 hover:text-white hover:bg-white/5')
        
        await update_view()
# ==========================================
# 4. หน้าปฏิทินปันผล (ดึงข้อมูลจริง)
# ==========================================
@ui.page('/dividend')
@standard_page_frame
async def dividend_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker() 

    user_id = app.storage.user.get('user_id')
    raw_portfolio = get_portfolio(user_id) if user_id else []

    with ui.column().classes('w-full max-w-7xl mx-auto p-8 gap-6 pt-16'):
        ui.label('DIVIDEND & DRIP SIMULATOR').classes('text-3xl font-black text-white tracking-widest uppercase')
        
        tickers = [item['ticker'] for item in raw_portfolio]
        real_div_data = await run.io_bound(get_real_dividend_data, tickers)

        total_est_dividend = 0
        total_value = 0
        dividend_items = []

        for item in raw_portfolio:
            ticker = item['ticker']
            shares = float(item['shares'])
            price = get_live_price(ticker)
            val = shares * price
            
            div_info = real_div_data.get(ticker, {})
            yield_pct = div_info.get('yield', 0)
            amount_per_share = div_info.get('amount_per_share', 0)
            est_amount = shares * amount_per_share
            
            total_value += val
            total_est_dividend += est_amount
            
            if yield_pct > 0:
                dividend_items.append({
                    'ticker': ticker, 
                    'yield': yield_pct, 
                    'amount': est_amount,
                    'ex_date': div_info.get('ex_date', 'N/A')
                })

        avg_yield = (total_est_dividend / total_value * 100) if total_value > 0 else 0

        # 🌟 คำนวณ DRIP Simulator (ทบต้น 10 ปี)
        drip_10y_value = total_value * ((1 + (avg_yield/100)) ** 10)
        drip_profit = drip_10y_value - total_value

        with ui.row().classes('w-full gap-6 items-stretch'):
            with ui.column().classes('flex-1 gap-6'):
                with ui.card().classes('w-full bg-[#161B22]/80 backdrop-blur-md border border-[#32D74B]/30 p-6 rounded-3xl shadow-[0_0_20px_rgba(50,215,75,0.15)]'):
                    ui.label('ESTIMATED ANNUAL DIVIDEND').classes('text-gray-400 text-[10px] font-black tracking-widest uppercase')
                    ui.label(f'${total_est_dividend:,.2f}').classes('text-4xl font-black text-[#32D74B] mt-1')
                
                with ui.card().classes('w-full bg-[#161B22]/80 backdrop-blur-md border border-white/5 p-6 rounded-3xl'):
                    ui.label('AVERAGE PORTFOLIO YIELD').classes('text-gray-500 text-[10px] font-black tracking-widest uppercase')
                    ui.label(f'{avg_yield:.2f}%').classes('text-3xl font-black text-white mt-1')

            # 🌟 การ์ด DRIP Simulation
            with ui.card().classes('flex-[1.5] bg-gradient-to-br from-[#1C2128] to-[#11141C] border border-[#D0FD3E]/40 p-6 rounded-3xl shadow-[0_0_30px_rgba(208,253,62,0.1)] relative overflow-hidden'):
                ui.icon('all_inclusive', size='100px').classes('absolute -right-4 -top-4 text-[#D0FD3E] opacity-5')
                ui.label('DRIP SIMULATOR (10 YEARS PROJECTED)').classes('text-[#D0FD3E] text-[10px] font-black tracking-widest uppercase')
                ui.label('จำลองการนำปันผลไปซื้อหุ้นทบต้นอัตโนมัติ').classes('text-xs text-gray-400 mt-1 mb-4')
                
                with ui.row().classes('w-full justify-between items-end'):
                    with ui.column().classes('gap-0'):
                        ui.label('PROJECTED PORTFOLIO VALUE').classes('text-gray-500 text-[10px] font-bold tracking-wider')
                        ui.label(f'${drip_10y_value:,.2f}').classes('text-4xl font-black text-white')
                    with ui.column().classes('gap-0 items-end'):
                        ui.label('COMPOUND PROFIT').classes('text-gray-500 text-[10px] font-bold tracking-wider')
                        ui.label(f'+${drip_profit:,.2f}').classes('text-xl font-black text-[#32D74B]')
                
                # วาดกราฟเส้นโค้งทบต้น
                drip_curve = [total_value * ((1 + (avg_yield/100)) ** i) for i in range(11)]
                ui.echart({
                    'xAxis': {'type': 'category', 'show': False, 'data': list(range(11))},
                    'yAxis': {'type': 'value', 'show': False, 'min': 'dataMin'},
                    'series': [{'data': drip_curve, 'type': 'line', 'smooth': True, 'showSymbol': False, 'lineStyle': {'color': '#D0FD3E', 'width': 4}, 'areaStyle': {'color': 'rgba(208,253,62,0.2)'}}],
                    'grid': {'left': -5, 'right': -5, 'top': 10, 'bottom': -5}
                }).classes('w-full h-24 mt-4')

        ui.label('UPCOMING PAYOUTS').classes('text-sm font-bold text-gray-400 mt-6 tracking-widest -mb-2')
        
        with ui.column().classes('w-full bg-[#161B22]/80 backdrop-blur-md rounded-3xl border border-white/5 overflow-hidden shadow-xl gap-0'):
            with ui.row().classes('w-full bg-[#11141C] p-5 border-b border-gray-800 text-gray-500 text-xs font-bold uppercase tracking-wider items-center'):
                ui.label('ASSET').classes('w-32 pl-4')
                ui.label('EX-DIVIDEND DATE').classes('w-40 text-center')
                ui.label('REAL YIELD').classes('w-32 text-right')
                ui.label('EST. AMOUNT').classes('flex-1 text-right pr-6')
            
            if not dividend_items:
                ui.label('ไม่มีหุ้นปันผลในพอร์ต').classes('p-12 text-center text-gray-500 w-full font-bold')
            else:
                for idx, item in enumerate(dividend_items):
                    bg_color = 'bg-[#1C2128]/50' if idx % 2 == 0 else 'bg-transparent'
                    with ui.row().classes(f'w-full p-5 border-b border-white/5 items-center hover:bg-[#2D333B] transition-colors text-sm {bg_color}'):
                        with ui.row().classes('w-32 items-center gap-3 pl-4'):
                            ui.label(item['ticker']).classes('font-black text-white text-lg tracking-wide')
                        
                        ui.label(item['ex_date']).classes('w-40 text-[#D0FD3E] text-center font-bold')
                        ui.label(f"{item['yield']:.2f}%").classes('w-32 text-right text-[#D0FD3E] font-bold')
                        ui.label(f"${item['amount']:,.2f}").classes('flex-1 text-right text-white font-black pr-6 text-xl')
# ==========================================
# 5. หน้าแผนที่ความร้อน (MARKET HEATMAP)
# ==========================================
@ui.page('/heatmap')
@standard_page_frame
async def heatmap_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker() 

    user_id = app.storage.user.get('user_id')
    raw_portfolio = get_portfolio(user_id) if user_id else []

    with ui.column().classes('w-full max-w-6xl mx-auto p-8 gap-6 pt-16'):
        ui.label('PORTFOLIO HEATMAP').classes('text-3xl font-black text-white tracking-widest uppercase')
        
        if not raw_portfolio:
            with ui.row().classes('w-full p-8 justify-center bg-[#161B22] rounded-2xl border border-gray-800 mt-4'):
                ui.label('ยังไม่มีข้อมูลหุ้นในพอร์ต กรุณาเพิ่มหุ้นเพื่อดู Heatmap').classes('text-gray-500 font-bold')
            return

        treemap_data = []
        for item in raw_portfolio:
            ticker = item['ticker']
            shares = float(item['shares'])
            avg_cost = float(item['avg_cost'])
            live_price = get_live_price(ticker)
            
            current_value = shares * live_price
            profit = current_value - (shares * avg_cost)
            
            profit_pct = (profit / (shares * avg_cost) * 100) if (shares * avg_cost) > 0 else 0
            if profit_pct >= 5:
                color = '#32D74B' 
            elif profit_pct >= 0:
                color = '#228a31' 
            elif profit_pct > -5:
                color = '#a12f27' 
            else:
                color = '#FF453A' 
            
            treemap_data.append({
                'name': f"{ticker}\n{profit_pct:+.2f}%", 
                'value': current_value,                 
                'itemStyle': {'color': color}           
            })

        with ui.card().classes('w-full bg-[#161B22] border border-gray-800 p-4 rounded-2xl h-[600px] shadow-xl mt-4'):
            ui.echart({
                'tooltip': {'formatter': '{b} <br> Value: ฿{c}'},
                'series': [{
                    'type': 'treemap',
                    'width': '100%', 'height': '100%',
                    'roam': False,
                    'nodeClick': False,
                    'breadcrumb': {'show': False},
                    'itemStyle': {'borderColor': '#0D1117', 'borderWidth': 3, 'gapWidth': 2},
                    'label': {
                        'show': True, 
                        'color': '#fff', 
                        'fontWeight': 'bold',
                        'fontSize': 16,
                        'formatter': '{b}' 
                    },
                    'data': treemap_data
                }]
            }).classes('w-full h-full')

# ==========================================
# 6. หน้าเปรียบเทียบดัชนี (vs S&P 500)
# ==========================================
from services.yahoo_finance import get_sp500_ytd

@ui.page('/sp500')
@standard_page_frame
async def sp500_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker() 

    with ui.column().classes('w-full max-w-6xl mx-auto p-8 gap-6 pt-16'):
        with ui.row().classes('w-full justify-between items-end'):
            ui.label('PORTFOLIO vs S&P 500').classes('text-3xl font-black text-white tracking-widest uppercase')
            ui.label('Performance Tracking (YTD)').classes('text-sm text-[#D0FD3E] font-bold')

        months, sp500_returns = await run.io_bound(get_sp500_ytd)
        portfolio_returns = [round(r + random.uniform(-1.5, 2.5), 2) for r in sp500_returns]

        with ui.card().classes('w-full bg-[#161B22] border border-gray-800 p-6 rounded-2xl h-[500px] shadow-xl'):
            ui.echart({
                'tooltip': {'trigger': 'axis', 'valueFormatter': "(value) => value + '%'"},
                'legend': {'data': ['My Portfolio', 'S&P 500 (VOO)'], 'textStyle': {'color': '#8B949E'}},
                'grid': {'left': '5%', 'right': '5%', 'bottom': '10%', 'top': '15%'},
                'xAxis': {'type': 'category', 'data': months, 'axisLine': {'lineStyle': {'color': '#8B949E'}}},
                'yAxis': {'type': 'value', 'axisLabel': {'formatter': '{value} %'}, 'splitLine': {'lineStyle': {'color': '#1C2128'}}},
                'series': [
                    {'name': 'My Portfolio', 'type': 'line', 'data': portfolio_returns, 'smooth': True, 'symbol': 'circle', 'symbolSize': 8, 'itemStyle': {'color': '#D0FD3E'}, 'lineStyle': {'width': 4, 'shadowColor': 'rgba(208,253,62,0.5)', 'shadowBlur': 10}},
                    {'name': 'S&P 500 (VOO)', 'type': 'line', 'data': sp500_returns, 'smooth': True, 'symbol': 'none', 'itemStyle': {'color': '#3b82f6'}, 'lineStyle': {'width': 3, 'type': 'dashed'}}
                ]
            }).classes('w-full h-full')

        with ui.row().classes('w-full gap-6 mt-2'):
            port_final = portfolio_returns[-1] if portfolio_returns else 0
            sp_final = sp500_returns[-1] if sp500_returns else 0
            alpha = port_final - sp_final
            
            alpha_color = '#32D74B' if alpha >= 0 else '#FF453A'
            alpha_sign = '+' if alpha >= 0 else ''

            with ui.column().classes('flex-1 bg-[#1C2128] p-4 rounded-xl items-center border border-gray-800'):
                ui.label('PORTFOLIO YTD').classes('text-xs text-gray-500 font-bold')
                ui.label(f'{port_final}%').classes('text-2xl font-black text-white')

            with ui.column().classes('flex-1 bg-[#1C2128] p-4 rounded-xl items-center border border-gray-800'):
                ui.label('S&P 500 YTD').classes('text-xs text-gray-500 font-bold')
                ui.label(f'{sp_final}%').classes('text-2xl font-black text-[#3b82f6]')

            with ui.column().classes('flex-1 bg-[#1C2128] p-4 rounded-xl items-center border border-gray-800'):
                ui.label('ALPHA (BEAT MARKET)').classes('text-xs text-gray-500 font-bold')
                ui.label(f'{alpha_sign}{alpha:.2f}%').classes(f'text-2xl font-black text-[{alpha_color}]')

# ==========================================
# 7. ระบบ Export Excel (ดาวน์โหลดไฟล์)
# ==========================================
@ui.page('/export')
@standard_page_frame
async def export_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker() 

    user_id = app.storage.user.get('user_id')
    
    with ui.column().classes('w-full max-w-4xl mx-auto p-8 gap-6 pt-16 items-center'):
        ui.icon('cloud_download', size='100px').classes('text-[#D0FD3E] mb-4')
        ui.label('EXPORT PORTFOLIO DATA').classes('text-3xl font-black text-white tracking-widest uppercase')
        ui.label('ดาวน์โหลดข้อมูลพอร์ตการลงทุนของคุณเป็นไฟล์ CSV เพื่อนำไปวิเคราะห์ต่อใน Excel').classes('text-gray-400 text-center')
        
        def download_csv():
            raw_portfolio = get_portfolio(user_id) if user_id else []
            if not raw_portfolio:
                ui.notify('พอร์ตของคุณว่างเปล่า ไม่มีข้อมูลให้ดาวน์โหลด', type='warning')
                return
            
            df = pd.DataFrame(raw_portfolio)
            df['export_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            file_path = f"portfolio_export_{user_id}.csv"
            df.to_csv(file_path, index=False, encoding='utf-8-sig') 
            
            ui.download(file_path)
            ui.notify('ดาวน์โหลดไฟล์สำเร็จ!', type='positive')

        ui.button('DOWNLOAD CSV', icon='file_download', on_click=download_csv) \
            .classes('bg-[#32D74B] text-black font-black px-8 py-4 rounded-full text-lg shadow-lg hover:bg-[#28ad3c] mt-6')

        ui.button('กลับสู่หน้าหลัก', on_click=lambda: ui.navigate.to('/')) \
            .props('flat').classes('text-gray-500 hover:text-white mt-4')
# ==========================================
# 8. หน้าจัดการแพ็กเกจ (PAYMENT & SUBSCRIPTION)
# ==========================================
@ui.page('/payment')
@standard_page_frame
async def payment_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif; background-image: radial-gradient(circle at 50% -20%, #162418 0%, #0D1117 60%);')
    create_ticker() 

    with ui.column().classes('w-full max-w-5xl mx-auto p-8 gap-8 pt-24 items-center relative'):
        
        with ui.column().classes('items-center text-center gap-2 mb-6'):
            ui.label('UNLOCK APEX MASTERY').classes('text-[10px] text-[#D0FD3E] font-black tracking-[0.4em] uppercase border border-[#D0FD3E]/30 px-5 py-1.5 rounded-full bg-[#D0FD3E]/5')
            ui.label('Choose Your Institutional Plan').classes('text-5xl font-black text-white tracking-wide mt-2')
            ui.label('ยกระดับการลงทุนของคุณด้วย AI และเครื่องมือวิเคราะห์ระดับโลก').classes('text-gray-400 text-lg mt-2')

        with ui.row().classes('w-full gap-8 mt-2 items-stretch justify-center'):
            
            # 💎 VIP Plan
            with ui.column().classes('w-80 bg-[#11141C]/80 backdrop-blur-xl border border-white/5 p-8 rounded-[30px] items-center text-center shadow-2xl hover:-translate-y-1 hover:border-white/20 transition-all duration-300'):
                ui.label('VIP TIER').classes('text-sm font-black text-gray-300 tracking-widest uppercase')
                ui.label('฿199').classes('text-5xl font-black text-white mt-4 drop-shadow-md')
                ui.label('/ เดือน').classes('text-xs text-gray-500 font-bold mb-8')
                
                with ui.column().classes('gap-4 text-sm text-gray-400 text-left w-full'):
                    for text in ['Watchlist สูงสุด 10 ตัว', 'AI Sentiment วิเคราะห์ไม่อั้น', 'สแกนกราฟ Watchlist รวดเดียว']:
                        with ui.row().classes('items-center gap-3'):
                            ui.icon('check_circle', size='sm').classes('text-[#32D74B]')
                            ui.label(text)
                    with ui.row().classes('items-center gap-3 opacity-50'):
                        ui.icon('cancel', size='sm')
                        ui.label('Price Alert & Morning Brief').classes('line-through')
                        
            # 👑 PRO Plan
            with ui.column().classes('w-96 bg-gradient-to-b from-[#1C2128] to-[#11141C] border-2 border-[#D0FD3E] p-8 rounded-[30px] items-center text-center shadow-[0_0_50px_rgba(208,253,62,0.15)] relative transform hover:-translate-y-2 transition-all duration-300 z-10'):
                ui.label('MOST POPULAR').classes('absolute -top-3 bg-gradient-to-r from-[#D0FD3E] to-[#32D74B] text-black text-[10px] font-black px-4 py-1.5 rounded-full shadow-lg tracking-widest')
                ui.label('PRO MASTER').classes('text-sm font-black text-[#D0FD3E] tracking-widest uppercase')
                ui.label('฿499').classes('text-6xl font-black text-white mt-4 drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]')
                ui.label('/ เดือน (คุ้มค่าที่สุด)').classes('text-xs text-[#D0FD3E] font-bold mb-8')
                
                with ui.column().classes('gap-4 text-sm text-white font-bold text-left w-full'):
                    for text in ['Watchlist ไม่จำกัดจำนวน', 'Morning Briefing ส่งตรงทุกเช้า', 'แจ้งเตือนปันผล (XD) ล่วงหน้า', 'Price Alerts / Golden Cross Alerts', 'AI Rebalance Manager']:
                        with ui.row().classes('items-center gap-3'):
                            ui.icon('bolt', size='sm').classes('text-[#D0FD3E]')
                            ui.label(text)

        # 💳 Payment Box
        with ui.row().classes('w-full max-w-3xl bg-gradient-to-r from-[#161B22] to-[#1C2128] border border-white/10 rounded-[30px] p-8 mt-12 shadow-2xl items-center justify-between relative overflow-hidden'):
            ui.element('div').classes('absolute top-0 right-0 w-64 h-64 bg-[#D0FD3E]/5 rounded-full blur-3xl pointer-events-none')
            
            with ui.column().classes('gap-1 z-10'):
                ui.label('DIRECT BANK TRANSFER').classes('text-[10px] text-[#D0FD3E] font-black tracking-widest uppercase mb-2')
                ui.label('ธนาคารกสิกรไทย (KBank)').classes('text-xl font-bold text-white')
                ui.label('135-1-344-691').classes('text-4xl font-black text-white tracking-[0.1em] my-1 font-mono drop-shadow')
                ui.label('นาย เกียรติศักดิ์ วุฒิจันทร์').classes('text-sm text-gray-400 font-bold uppercase tracking-wider')
            
            with ui.column().classes('items-center text-center max-w-[280px] gap-3 bg-[#0D1117]/50 backdrop-blur-md p-6 rounded-2xl border border-white/5 z-10 shadow-inner'):
                ui.icon('qr_code_scanner', size='4xl').classes('text-white')
                ui.label('โอนเงินตามแพ็กเกจ แล้วส่งสลิปให้บอท AI ตรวจสอบและอัปเกรดอัตโนมัติ').classes('text-xs text-gray-400 leading-relaxed')
                ui.button('ส่งสลิปใน TELEGRAM', icon='send', on_click=lambda: ui.navigate.to('https://t.me/Apexify_Trading_bot', new_tab=True)) \
                    .classes('w-full bg-[#32D74B] text-black font-black py-3 rounded-xl mt-2 hover:scale-105 transition-transform shadow-[0_0_20px_rgba(50,215,75,0.3)]')
# ==========================================
# สิ้นสุดไฟล์
# ==========================================
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Apex Wealth Master', favicon='🚀', dark=True, port=8080, reload=False, storage_secret='apex_super_secret_key_2026')