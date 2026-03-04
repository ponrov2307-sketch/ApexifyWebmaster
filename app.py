from nicegui import ui, app, run
import logging
from core.config import (
    APP_HOST,
    APP_PORT,
    APP_RELOAD,
    APP_TITLE,
    COLORS,
    NICEGUI_STORAGE_SECRET,
    FEATURE_PHASE_B_SIGNALS,
    FEATURE_UPSELL_TRACKING,
)
import random
import pandas as pd
from datetime import datetime, UTC
import asyncio
from datetime import timedelta
from urllib.parse import quote_plus
# Components & Services
from web.components import charts
from web.components.ticker import create_ticker
from web.components.stats import create_stats_cards
from web.components.table import create_portfolio_table, get_logo_url_for_ticker
from web.components.charts import show_candlestick_chart
from services.yahoo_finance import (
    get_sparkline_data,
    get_live_price,
    update_global_cache_batch,
    get_real_dividend_data,
    get_portfolio_historical_growth,
    get_stock_duel_data,
    get_drip_projection,
    get_real_drip_backtest,
    get_real_sector_rotation,
)
from services.news_fetcher import fetch_stock_news_summary
from services.gemini_ai import generate_apexify_report

# DB & Auth
from core.models import get_portfolio, add_portfolio_stock, update_portfolio_stock, delete_portfolio_stock, get_user_by_telegram, get_all_unique_tickers, get_user_price_alerts, delete_price_alert, set_user_price_alert
from web.auth import login_page, require_login, logout
from web.router import standard_page_frame

# ==========================================
# ?? APEXIFY X BINANCE OVERHAUL ENGINE
# ==========================================
ui.add_head_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700;800&family=Sora:wght@600;700;800&display=swap');
        :root {
            --q-primary: #3FD0FF;
            --q-dark: #060B12;
            --q-dark-page: #060B12;
            --ax-bg: #060B12;
            --ax-surface: #0D1620;
            --ax-surface-2: #111E2A;
            --ax-accent: #56D3FF;
            --ax-accent-2: #5CF2C8;
            --ax-positive: #4CE2BC;
            --ax-negative: #FF5E6C;
            --ax-text-muted: #8DA4B5;
        }
        body, .q-layout, .q-page-container, .q-page { 
            background-color: var(--ax-bg) !important;
            background-image: radial-gradient(circle at 80% -10%, rgba(86, 211, 255, 0.11), transparent 44%), radial-gradient(circle at 10% 10%, rgba(92, 242, 200, 0.09), transparent 38%) !important;
            color: #EAECEF !important;
            font-family: "Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: #0B0E11; }
        ::-webkit-scrollbar-thumb { background: #2B3139; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #848E9C; }

        .q-dialog__inner > div {
            background: #0D1620 !important;
            border: 1px solid rgba(86,211,255,0.18) !important;
            border-radius: 18px !important;
            box-shadow: 0 20px 50px rgba(0,0,0,0.72) !important;
        }

        .q-field--outlined .q-field__control {
            border-radius: 12px !important;
            background: #0A131B !important;
            border: 1px solid rgba(141,164,181,0.25) !important;
        }
        .q-field--outlined.q-field--focused .q-field__control {
            border-color: var(--ax-accent) !important;
            box-shadow: none !important;
        }
        ::selection { background: var(--ax-accent); color: #00140f; }
        .q-page-container { padding-top: 0 !important; }
    </style>
''', shared=True)

def apply_global_style():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')


ui.add_head_html('''
    <style>
        @keyframes aurora-drift {
            0% { transform: translate3d(0, 0, 0) scale(1); }
            50% { transform: translate3d(30px, -20px, 0) scale(1.08); }
            100% { transform: translate3d(0, 0, 0) scale(1); }
        }
        @keyframes pulse-green {
            0%, 100% { text-shadow: 0 0 0px transparent; color: #32D74B; }
            50% { text-shadow: 0 0 15px rgba(50,215,75,0.6); color: #D0FD3E; }
        }
        @keyframes pulse-red {
            0%, 100% { text-shadow: 0 0 0px transparent; color: #FF453A; }
            50% { text-shadow: 0 0 15px rgba(255,69,58,0.6); color: #ff857f; }
        }
        
        /* ?? 1. อนิเมชั่นเด้งแบบนุ่มนวล (ใช้ cubic-bezier ให้ดูมีสปริง) */
        @keyframes smooth-pop {
            0% { transform: scale(1); }
            40% { transform: scale(1.05); } /* ลดความใหญ่ลงให้ดูแพง ไม่กระแทกตา */
            100% { transform: scale(1); }
        }
        .animate-pop { 
            animation: smooth-pop 0.5s cubic-bezier(0.22, 1, 0.36, 1); 
            display: inline-block; /* บังคับให้อนิเมชั่นไม่กระทบโครงสร้างกล่อง */
            will-change: transform; /* ให้การ์ดจอช่วยเรนเดอร์ จะสมูท 100% */
        }
        
        /* ?? 2. ล็อกความกว้างตัวเลข (ไม้ตายแอปเทรด) ป้องกันข้อความยืดหดเวลาเลขเปลี่ยน */
        .tabular-nums {
            font-variant-numeric: tabular-nums;
        }

        .blink-green { animation: pulse-green 2s infinite ease-in-out; }
        .blink-red { animation: pulse-red 2s infinite ease-in-out; }

        .ax-card {
            background: linear-gradient(180deg, rgba(14, 25, 35, 0.9), rgba(9, 16, 24, 0.92));
            border: 1px solid rgba(120, 153, 176, 0.2);
            border-radius: 22px;
            backdrop-filter: blur(14px);
            box-shadow: 0 14px 34px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.06);
        }
        .ax-card-hover {
            transition: all 0.25s ease;
        }
        .ax-card-hover:hover {
            border-color: rgba(86, 211, 255, 0.4);
            box-shadow: 0 18px 42px rgba(4, 12, 18, 0.68), 0 0 24px rgba(86, 211, 255, 0.12);
            transform: translateY(-3px);
        }
        .ax-pill {
            border-radius: 9999px;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.04);
        }
        .ax-accent-btn {
            background: linear-gradient(90deg, var(--ax-accent), var(--ax-accent-2));
            color: #06201d;
            font-weight: 900;
        }
        .ax-ghost-btn {
            border: 1px solid rgba(57, 200, 255, 0.35);
            color: #8bdfff;
            background: rgba(57, 200, 255, 0.08);
        }
        .ax-gradient-bg {
            position: relative;
            overflow: hidden;
        }
        .ax-gradient-bg::before {
            content: "";
            position: absolute;
            inset: -30% auto auto -20%;
            width: 320px;
            height: 320px;
            border-radius: 9999px;
            pointer-events: none;
            background: radial-gradient(circle, rgba(32,214,161,0.14), rgba(32,214,161,0));
            filter: blur(35px);
        }
        .q-btn {
            letter-spacing: 0.02em;
        }
        .q-btn:hover {
            filter: brightness(1.04);
        }
        .q-card, .q-menu, .q-dialog__inner > div {
            border-color: rgba(57, 200, 255, 0.14) !important;
        }
        .ax-page-shell {
            width: 100%;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
            padding-left: 10px;
            padding-right: 10px;
        }
        .ax-section-title {
            font-size: 0.78rem;
            color: #8ea7b6;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            font-weight: 900;
        }
        .ax-subtle {
            color: var(--ax-text-muted);
        }
        .ax-soft-border {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
        }
        .ax-btn-primary {
            background: linear-gradient(90deg, #65D8FF, #7EF7CF);
            color: #042029;
            font-weight: 900;
            border-radius: 12px;
        }
        .ax-btn-secondary {
            background: rgba(57,200,255,0.12);
            color: #9fe7ff;
            border: 1px solid rgba(57,200,255,0.35);
            border-radius: 12px;
            font-weight: 800;
        }
        .ax-grid-3 {
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
            width: 100%;
        }
        @media (min-width: 1024px) {
            .ax-grid-3 {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
        }
        .ax-action-strip {
            width: 100%;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            background: rgba(8, 20, 27, 0.68);
            backdrop-filter: blur(12px);
            padding: 12px;
        }
        .ax-equal-card {
            min-height: 220px;
        }
        .ax-neon-ring {
            border: 1px solid rgba(86,211,255,0.28) !important;
            box-shadow: 0 0 0 1px rgba(86,211,255,0.1) inset, 0 10px 30px rgba(0,0,0,0.35), 0 0 35px rgba(86,211,255,0.1);
        }
        .ax-hero-glow {
            position: relative;
        }
        .ax-hero-glow::before,
        .ax-hero-glow::after {
            content: "";
            position: absolute;
            border-radius: 9999px;
            filter: blur(70px);
            pointer-events: none;
            z-index: 0;
            animation: aurora-drift 10s ease-in-out infinite;
        }
        .ax-hero-glow::before {
            width: 260px;
            height: 260px;
            left: -40px;
            top: -70px;
            background: rgba(32, 214, 161, 0.2);
        }
        .ax-hero-glow::after {
            width: 300px;
            height: 300px;
            right: -50px;
            bottom: -110px;
            background: rgba(57, 200, 255, 0.16);
            animation-delay: 1.8s;
        }
    </style>
''', shared=True)

# ==========================================
# ??? ฟังก์ชันช่วยเหลือ (MODALS & POPUPS)
# ==========================================
# ==========================================
# ?? หน้าต่างจัดการสินทรัพย์ (ADD & EDIT)
# ==========================================
async def handle_add_asset():
    app.storage.client['modal_open'] = True
    user_id = app.storage.user.get('user_id')
    if not user_id: return

    # ?? [แบ่งสิทธิ์ 3 Tiers] ??
    tid = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(tid) if tid else {}
    role = str(user_info.get('role', 'free')).lower()
    
    current_portfolio = get_portfolio(user_id)
    curr_len = len(current_portfolio)
    
    if role == 'free' and curr_len >= 3:
        ui.notify('?? FREE ใส่หุ้นได้สูงสุด 3 ตัว (อัปเกรด VIP หรือ PRO เพื่อปลดล็อค!)', type='warning')
        app.storage.client['modal_open'] = False
        return
    if role == 'vip' and curr_len >= 10:
        ui.notify('?? VIP ใส่หุ้นได้สูงสุด 10 ตัว (อัปเกรดเป็น PRO เพื่อใส่ได้ไม่จำกัด!)', type='warning')
        app.storage.client['modal_open'] = False
        return
    # ?? [สิ้นสุดโค้ดที่เพิ่ม] ??
    with ui.dialog().props('no-refocus maximized sm:maximized=false') as dialog:
        with ui.card().classes('w-full sm:max-w-[450px] h-full sm:h-auto bg-[#181A20] p-0 flex flex-col'):
            with ui.row().classes('w-full p-4 md:p-5 border-b border-[#2B3139] justify-between items-center shrink-0'):
                ui.label('Add New Asset').classes('text-lg md:text-xl font-bold text-white')
                ui.button(icon='close', on_click=dialog.close).props('flat dense').classes('text-gray-500 hover:text-[#F6465D]')

            with ui.column().classes('p-5 md:p-6 w-full gap-5 flex-1 overflow-y-auto'):
                with ui.column().classes('w-full gap-1'):
                    ui.label('Symbol / Ticker').classes('text-[10px] text-gray-400 font-bold uppercase')
                    ticker_input = ui.input(placeholder='AAPL, BTC-USD').classes('w-full text-lg').props('outlined dark autofocus')
                
                with ui.row().classes('w-full gap-4 flex flex-col sm:flex-row'):
                    with ui.column().classes('flex-1 gap-1 w-full'):
                        ui.label('Shares').classes('text-[10px] text-gray-400 font-bold uppercase')
                        shares_input = ui.number(value=0, format='%.6f').classes('w-full').props('outlined dark step=0.01')
                    with ui.column().classes('flex-1 gap-1 w-full'):
                        ui.label('Avg Cost').classes('text-[10px] text-gray-400 font-bold uppercase')
                        cost_input = ui.number(value=0, format='%.4f').classes('w-full').props('outlined dark step=0.01')

                with ui.row().classes('w-full gap-4 flex flex-col sm:flex-row'):
                    with ui.column().classes('flex-[1.5] gap-1 w-full'):
                        ui.label('Target Alert (Bot Sync)').classes('text-[10px] text-[#FCD535] font-bold uppercase')
                        alert_input = ui.number(value=0, format='%.2f').classes('w-full').props('outlined dark')
                    with ui.column().classes('flex-1 gap-1 w-full'):
                        ui.label('Group').classes('text-[10px] text-gray-400 font-bold uppercase')
                        group_select = ui.select(['ALL', 'DCA', 'DIV', 'TRADING'], value='ALL').classes('w-full').props('outlined dark')

            with ui.row().classes('w-full p-5 pt-0 gap-3 shrink-0 flex flex-col sm:flex-row'):
                ui.button('Cancel', on_click=dialog.close).classes('w-full sm:flex-1 bg-[#2B3139] text-white font-bold py-3 rounded-lg hover:bg-gray-700 transition-colors order-last sm:order-first')
                def save_new():
                    t = ticker_input.value.strip().upper() if ticker_input.value else ''
                    if not t: ui.notify('?? กรุณาใส่ชื่อหุ้น', type='warning'); return
                    a = float(alert_input.value or 0)
                    if add_portfolio_stock(user_id, t, float(shares_input.value or 0), float(cost_input.value or 0), group_select.value):
                        if a > 0: set_user_price_alert(user_id, t, a, '>' if a > get_live_price(t) else '<')
                        ui.notify(f'? เพิ่ม {t} สำเร็จ', type='positive')
                        ui.run_javascript('window.location.reload()')
                ui.button('Confirm', on_click=save_new).classes('w-full sm:flex-[2] bg-[#FCD535] text-black font-bold py-3 rounded-lg hover:bg-[#E5C02A] transition-colors')
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
    from services.yahoo_finance import get_support_resistance
    support, resistance = get_support_resistance(ticker)
    active_alerts = get_user_price_alerts(str(user_id))
    current_alert_target = next((a['target_price'] for a in active_alerts if a['symbol'].upper() == ticker.upper() and a['is_active'] == 1), 0)
    saved_alert = float(asset.get('alert_price', 0))
    default_alert = current_alert_target if current_alert_target > 0 else (saved_alert if saved_alert > 0 else current_price * 0.95)

    with ui.dialog().props('no-refocus maximized sm:maximized=false') as dialog:
        with ui.card().classes('w-full sm:max-w-[450px] h-full sm:h-auto bg-[#181A20] p-0 flex flex-col'):
            with ui.row().classes('w-full p-4 md:p-5 border-b border-[#2B3139] justify-between items-center shrink-0'):
                ui.label(f'Edit {ticker}').classes('text-lg md:text-xl font-bold text-white')
                ui.button(icon='close', on_click=dialog.close).props('flat dense').classes('text-gray-500 hover:text-[#F6465D]')
        
            with ui.column().classes('p-5 md:p-6 w-full gap-5 flex-1 overflow-y-auto'):
                with ui.row().classes('w-full justify-between items-center bg-[#0B0E11] p-3 rounded-lg border border-[#2B3139]'):
                    ui.label('Market Price').classes('text-xs text-gray-500 font-bold')
                    with ui.row().classes('items-center gap-2'):
                        ui.label(f'R: ${resistance}').classes('text-[9px] text-[#F6465D] bg-[#F6465D]/10 px-1 rounded')
                        ui.label(f'S: ${support}').classes('text-[9px] text-[#0ECB81] bg-[#0ECB81]/10 px-1 rounded')
                        ui.label(f"${current_price:,.2f}").classes('text-xl font-bold text-white ml-2')

                with ui.row().classes('w-full gap-4 flex flex-col sm:flex-row'):
                    with ui.column().classes('flex-1 gap-1 w-full'):
                        ui.label('Shares').classes('text-[10px] text-gray-400 font-bold uppercase')
                        shares_input = ui.number(value=float(asset['shares']), format='%.6f').classes('w-full').props('outlined dark step=0.01')
                    with ui.column().classes('flex-1 gap-1 w-full'):
                        ui.label('Avg Cost').classes('text-[10px] text-gray-400 font-bold uppercase')
                        cost_input = ui.number(value=float(asset['avg_cost']), format='%.4f').classes('w-full').props('outlined dark step=0.01')

                with ui.row().classes('w-full gap-4 flex flex-col sm:flex-row'):
                    with ui.column().classes('flex-[1.5] gap-1 w-full'):
                        with ui.row().classes('w-full justify-between'):
                            ui.label('Price Alert').classes('text-[10px] text-[#FCD535] font-bold uppercase')
                            if support > 0: ui.button('Auto S/R', on_click=lambda: alert_input.set_value(support)).props('flat dense size=xs').classes('text-[#0ECB81]')
                        alert_input = ui.number(value=default_alert, format='%.2f').classes('w-full').props('outlined dark')
                    with ui.column().classes('flex-1 gap-1 w-full'):
                        ui.label('Group').classes('text-[10px] text-gray-400 font-bold uppercase')
                        group_select = ui.select(['ALL', 'DCA', 'DIV', 'TRADING'], value=asset.get('asset_group', 'ALL')).classes('w-full').props('outlined dark')

            with ui.row().classes('w-full p-5 pt-0 gap-3 shrink-0 flex flex-col sm:flex-row'):
                def do_del():
                    if delete_portfolio_stock(user_id, ticker): ui.run_javascript('window.location.reload()')
                ui.button('Delete', on_click=do_del).classes('w-full sm:flex-1 bg-transparent text-[#F6465D] border border-[#F6465D]/50 font-bold py-3 rounded-lg hover:bg-[#F6465D]/10 order-last sm:order-first')
                def do_save():
                    new_alert = float(alert_input.value)
                    if update_portfolio_stock(user_id, ticker, shares_input.value, cost_input.value, group_select.value, new_alert):
                        if new_alert > 0: set_user_price_alert(user_id, ticker, new_alert, '>' if new_alert > current_price else '<')
                        ui.run_javascript('window.location.reload()')
                ui.button('Save & Sync', on_click=do_save).classes('w-full sm:flex-[2] bg-[#FCD535] text-black font-bold py-3 rounded-lg hover:bg-[#E5C02A]')
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
    from services.yahoo_finance import get_support_resistance
    support, resistance = get_support_resistance(ticker)
    
    # ?? ดึงข้อมูลจากตาราง Telegram (user_price_alerts) มาแสดงเป็นค่าเริ่มต้น
    active_alerts = get_user_price_alerts(str(user_id))
    current_alert_target = next((a['target_price'] for a in active_alerts if a['symbol'].upper() == ticker.upper() and a['is_active'] == 1), 0)
    
    saved_alert = float(asset.get('alert_price', 0))
    # เลือกว่าจะเอาตัวเลขจากไหน (เรียงความสำคัญ: Telegram -> ค่าเดิม -> 95% ของราคาปัจจุบัน)
    default_alert = current_alert_target if current_alert_target > 0 else (saved_alert if saved_alert > 0 else current_price * 0.95)

    with ui.dialog().props('no-refocus') as dialog, ui.card().classes('w-full max-w-[450px] bg-[#0D1117]/90 backdrop-blur-2xl border border-white/10 p-0 rounded-3xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.8)]'):
        with ui.row().classes('w-full bg-gradient-to-r from-[#161B22] to-[#1C2128] p-5 border-b border-white/5 justify-between items-center'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('tune', size='sm').classes('text-[#D0FD3E]')
                ui.label('EDIT ASSET').classes('text-xl font-black text-white tracking-[0.2em]')
            ui.button(icon='close', on_click=dialog.close).props('flat dense round').classes('text-gray-500 hover:text-[#FF453A] transition-colors')
        
        with ui.column().classes('p-5 md:p-6 w-full gap-5'):
            with ui.row().classes('w-full justify-between items-center bg-[#11141C]/50 p-4 rounded-2xl border border-white/5 shadow-inner flex-nowrap'):
                with ui.column().classes('gap-0 shrink-0'):
                    ui.label(ticker).classes('text-xl md:text-2xl font-black text-white tracking-wider')
                    ui.label('Market Price').classes('text-[10px] text-gray-500 uppercase tracking-widest font-bold')
                
                with ui.column().classes('items-end gap-1'):
                    ui.label(f"${current_price:,.2f}").classes('text-2xl md:text-3xl font-black text-[#D0FD3E] drop-shadow-[0_0_10px_rgba(208,253,62,0.3)] leading-none')
                    with ui.row().classes('gap-1 md:gap-2'):
                        ui.label(f'Res: ${resistance}').classes('text-[9px] font-bold text-[#FF453A] bg-[#FF453A]/10 px-1.5 py-0.5 rounded')
                        ui.label(f'Sup: ${support}').classes('text-[9px] font-bold text-[#32D74B] bg-[#32D74B]/10 px-1.5 py-0.5 rounded')
            
            ui.element('div').classes('w-full h-[1px] bg-gradient-to-r from-transparent via-gray-700 to-transparent my-1')

            with ui.row().classes('w-full gap-4 flex flex-col sm:flex-row'):
                with ui.column().classes('flex-1 gap-1 w-full'):
                    ui.label('Shares (จำนวน)').classes('text-xs text-gray-400 font-bold tracking-wider')
                    shares_input = ui.number(value=float(asset['shares']), format='%.6f').classes('w-full').props('outlined dark step=0.01 rounded')
                with ui.column().classes('flex-1 gap-1 w-full'):
                    ui.label('Avg Cost (ต้นทุน)').classes('text-xs text-gray-400 font-bold tracking-wider')
                    cost_input = ui.number(value=float(asset['avg_cost']), format='%.4f').classes('w-full').props('outlined dark step=0.01 rounded')

            with ui.row().classes('w-full gap-4 items-end flex flex-col sm:flex-row'):
                with ui.column().classes('flex-[1.5] gap-1 w-full'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label('Price Alert (Bot Sync)').classes('text-xs text-[#D0FD3E] font-bold tracking-wider drop-shadow-md')
                        if support > 0:
                            ui.button('AUTO S/R', on_click=lambda: alert_input.set_value(support)).props('flat dense size=xs').classes('text-[#32D74B] text-[9px] font-black tracking-widest hover:bg-white/5 px-2 rounded')
                    
                    alert_input = ui.number(value=default_alert, format='%.2f').classes('w-full').props('outlined dark rounded')
                
                with ui.column().classes('flex-1 gap-1 w-full'):
                    ui.label('Group').classes('text-xs text-gray-400 font-bold tracking-wider')
                    
                    # ?? [แก้บั๊ก] ทำความสะอาดค่าจากฐานข้อมูลก่อน ป้องกัน Error ถาวร
                    raw_group = str(asset.get('asset_group') or 'ALL').strip().upper()
                    valid_groups = ['ALL', 'DCA', 'DIV', 'TRADING']
                    safe_group = raw_group if raw_group in valid_groups else 'ALL'
                    
                    asset_group_select = ui.select(valid_groups, value=safe_group).classes('w-full').props('outlined dark rounded')

            def save_edit():
                new_alert = float(alert_input.value)
                # เซฟข้อมูลต้นทุนและจำนวนหุ้นปกติ
                if update_portfolio_stock(user_id, ticker, shares_input.value, cost_input.value, asset_group_select.value, new_alert):
                    
                    # ?? [ไฮไลท์สำคัญ] บันทึกการตั้งเตือนลงตารางของ Telegram อัตโนมัติ
                    if new_alert > 0:
                        # ถ้าราคาที่ตั้งเตือน สูงกว่า ราคาปัจจุบัน แสดงว่าเตือนตอนราคาเบรกขึ้น (>)
                        cond = '>' if new_alert > current_price else '<'
                        set_user_price_alert(user_id, ticker, new_alert, cond)

                    ui.notify(f'? บันทึกข้อมูลและซิงค์การแจ้งเตือนสำเร็จ!', type='positive')
                    ui.run_javascript('window.scrollTo(0, 0); setTimeout(() => { window.location.href = "/"; }, 200);')

            def confirm_delete():
                if delete_portfolio_stock(user_id, ticker):
                    ui.notify(f'??? ลบ {ticker} ออกจากพอร์ตแล้ว', type='warning')
                    ui.run_javascript('window.scrollTo(0, 0); setTimeout(() => { window.location.href = "/"; }, 200);')

            with ui.row().classes('w-full gap-3 mt-2 flex flex-col sm:flex-row'):
                ui.button('DELETE', on_click=confirm_delete).classes('w-full sm:flex-1 bg-transparent text-[#FF453A] border border-[#FF453A]/30 font-black py-3 rounded-xl hover:bg-[#FF453A] hover:text-white transition-all order-last sm:order-first')
                ui.button('SAVE & SYNC', on_click=save_edit).classes('w-full sm:flex-[2] bg-gradient-to-r from-[#D0FD3E] to-[#32D74B] text-black font-black py-3 rounded-xl shadow-[0_0_15px_rgba(50,215,75,0.4)] hover:scale-[1.02] transition-all')

    dialog.on('hide', lambda: app.storage.client.update({'modal_open': False}))
    dialog.open()
async def handle_news(ticker):
    app.storage.client['modal_open'] = True
    current_price = await run.io_bound(get_live_price, ticker)
    logo_url = get_logo_url_for_ticker(ticker)

    # ?? ดึงข้อมูลสิทธิ์การใช้งาน
    user_id = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(user_id) if user_id else {}
    role = str(user_info.get('role', 'free')).lower()
    
    # ?? ตัวแปรเช็คสิทธิ์ PRO สำหรับใช้งาน AI ทั้งหมด
    is_pro_ai = role in ['pro', 'admin']

    # ดึงข้อมูลจริงจาก Yahoo Finance
    from services.yahoo_finance import get_analyst_target, get_real_rsi
    target_price, upside = await run.io_bound(get_analyst_target, ticker)
    real_rsi = await run.io_bound(get_real_rsi, ticker)

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl h-[750px] bg-[#0D1117] border border-gray-800 p-0 rounded-3xl shadow-2xl flex flex-col'):
        with ui.row().classes('w-full bg-[#161B22] p-6 border-b border-gray-800 items-center justify-between shrink-0'):
            with ui.row().classes('items-center gap-4'):
                ui.image(logo_url).classes('w-16 h-16 rounded-xl bg-white p-1 shadow-inner')
                with ui.column().classes('gap-0'):
                    ui.label(f"{ticker} Insights").classes('text-3xl font-black text-white tracking-widest')
                    ui.label(f"Current: ${current_price:,.2f}").classes('text-xl font-bold text-[#D0FD3E]')
            ui.button(icon='close', on_click=dialog.close).props('flat dense').classes('text-gray-400 hover:text-[#FF453A]')

        with ui.column().classes('p-6 w-full gap-6 overflow-y-auto custom-scrollbar flex-1'):
            
            # ?? 1. สถิติ & Analyst Target (ทุกคนดูได้ เป็นเหยื่อล่อ)
            with ui.row().classes('w-full gap-4 items-stretch'):
                with ui.grid(columns=3).classes('flex-[2] gap-4 bg-[#161B22] p-5 rounded-2xl border border-white/5'):
                    stats = [('Market Cap', '$3.01T'), ('P/E Ratio', '32.14'), ('EPS', '6.42'), ('Beta (Vol)', '1.25'), ('52W High', f"${current_price*1.3:.2f}"), ('52W Low', f"${current_price*0.7:.2f}")]
                    for label, val in stats:
                        with ui.column().classes('gap-0'):
                            ui.label(label).classes('text-xs text-gray-500 font-bold')
                            ui.label(val).classes('text-sm font-black text-white')
                
                with ui.column().classes('flex-1 bg-gradient-to-br from-[#1C2128] to-[#11141C] p-5 rounded-2xl border border-[#D0FD3E]/30 items-center justify-center text-center shadow-[0_0_20px_rgba(208,253,62,0.1)]'):
                    ui.label('ANALYST TARGET (12M)').classes('text-[10px] font-black text-[#D0FD3E] tracking-widest')
                    ui.label(f"${target_price:,.2f}").classes('text-3xl font-black text-white my-1')
                    ui.label(f"Upside: +{upside:.1f}%").classes('text-sm font-bold text-[#32D74B]')

            # ?? 2. AI Sentiment (ล็อคสิทธิ์ PRO)
            with ui.column().classes('w-full bg-[#161B22]/50 border border-gray-800 rounded-2xl p-6 items-center text-center relative'):
                ui.icon('smart_toy', size='sm').classes('text-[#D0FD3E] mb-1')
                ui.label('AI SENTIMENT ANALYSIS').classes('text-xs font-black text-[#D0FD3E] tracking-widest mb-2')
                
                if not is_pro_ai:
                    ui.label('?? ฟีเจอร์ AI วิเคราะห์แนวโน้มหุ้น สงวนสิทธิ์สำหรับแพ็กเกจ PRO').classes('text-sm text-gray-500 mb-4')
                    ui.button('UPGRADE TO PRO', on_click=lambda: ui.navigate.to('/payment')).classes('bg-[#FCD535] text-black font-black px-6 py-2 rounded-full text-xs shadow-lg hover:scale-105')
                else:
                    loading_ai = ui.spinner('dots', size='lg', color='#D0FD3E')
                    ai_content = ui.column().classes('items-center gap-2 hidden w-full')
                    with ai_content:
                        ai_text = ui.label('').classes('text-sm text-gray-300 leading-relaxed text-center')

            # ?? 3. News & AI Summary (ล็อคสิทธิ์ PRO)
            ui.label('RECENT NEWS & AI IMPACT').classes('text-xs font-black text-gray-500 tracking-widest mt-2 -mb-2')
            
            if not is_pro_ai:
                with ui.column().classes('w-full bg-[#161B22]/50 border border-gray-800 rounded-2xl p-6 items-center text-center'):
                    ui.label('?? ข่าวสาร Real-time และ AI สรุปข่าว สงวนสิทธิ์สำหรับแพ็กเกจ PRO').classes('text-sm text-gray-500')
            else:
                loading_news = ui.spinner('dots', size='md', color='white').classes('mx-auto mt-4')
                news_container = ui.column().classes('w-full gap-3 hidden')
                with news_container:
                    news_summary_text = ui.label('').classes('text-sm text-gray-300 bg-[#161B22] p-5 rounded-2xl border border-gray-800 w-full')

    dialog.on('hide', lambda: app.storage.client.update({'modal_open': False}))
    dialog.open()

    # ?? ถ้าเป็น PRO ถึงจะสั่งให้ AI ทำงาน (ลดค่าใช้จ่าย API)
    if is_pro_ai:
        tech_data = {'symbol': ticker, 'price': current_price, 'rsi': real_rsi, 'ema20': current_price*0.98, 'ema50': current_price*0.95, 'ema200': current_price*0.9}
        
        from services.gemini_ai import generate_apexify_report
        from services.news_fetcher import fetch_stock_news_summary
        
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


def normalize_series(series):
    values = [float(v) for v in (series or []) if v is not None]
    if not values:
        return []
    min_v, max_v = min(values), max(values)
    if max_v <= min_v:
        return [50.0 for _ in values]
    return [((v - min_v) / (max_v - min_v)) * 100 for v in values]


def parse_expiry_to_days_left(expiry_value):
    if not expiry_value:
        return None
    raw = str(expiry_value).strip()
    if not raw:
        return None
    candidates = ['%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S']
    dt = None
    for fmt in candidates:
        try:
            dt = datetime.strptime(raw, fmt)
            break
        except Exception:
            continue
    if dt is None:
        return None
    now = datetime.now()
    return (dt.date() - now.date()).days


def build_payment_qr_url():
    payload = (
        "ธนาคารกสิกรไทย (KBank)\n"
        "เลขที่บัญชี: 135-1-344-691\n"
        "ชื่อบัญชี: นาย เกียรติศักดิ์ วุฒิจันทร์\n"
        "Apexify PRO/VIP Payment"
    )
    return f"https://quickchart.io/qr?size=280&text={quote_plus(payload)}"


def redeem_code_from_backend(telegram_id: str, code: str):
    """Bridge web redeem UI to backend redeem implementation if available."""
    try:
        from core.database import redeem_code
    except Exception:
        return (False, 'not_available', None, None)
    try:
        result = redeem_code(str(telegram_id), str(code).upper())
        if isinstance(result, tuple):
            return result
        return (False, 'invalid_response', None, None)
    except Exception as e:
        return (False, f'error:{e}', None, None)


def get_matchmaker_universe():
    return [
        'NVDA', 'MSFT', 'AAPL', 'GOOGL', 'AMZN', 'META', 'TSLA', 'AVGO', 'AMD', 'PLTR',
        'NFLX', 'ADBE', 'CRM', 'ORCL', 'INTC', 'QCOM', 'ASML', 'MU', 'TSM', 'SMCI',
        'JPM', 'V', 'MA', 'GS', 'BAC', 'C', 'BRK-B', 'BLK', 'AXP', 'MS',
        'COST', 'WMT', 'PG', 'KO', 'PEP', 'MCD', 'NKE', 'SBUX', 'HD', 'LOW',
        'XOM', 'CVX', 'SLB', 'CAT', 'DE', 'GE', 'LMT', 'BA', 'UNH', 'LLY',
        'SPY', 'QQQ', 'DIA', 'IWM', 'VOO', 'VTI', 'XLF', 'XLK', 'XLE', 'XLV',
    ]


def build_trade_plan(asset: dict) -> dict:
    ticker = str(asset.get('ticker', 'N/A'))
    current_price = float(asset.get('last_price', 0) or 0)
    avg_cost = float(asset.get('avg_cost', 0) or 0)
    profit_pct = float(asset.get('profit_pct', 0) or 0)
    sparkline = asset.get('sparkline') or []
    trend_up = bool(sparkline and len(sparkline) > 1 and sparkline[-1] >= sparkline[0])

    if profit_pct >= 15:
        suggested_action = 'TAKE PROFIT'
        signal = 'SELL-TRIM'
        reason = 'กำไรเริ่มสูง ควรทยอยล็อกกำไร / Profit is extended; scale out gradually.'
    elif profit_pct <= -8:
        suggested_action = 'CUT LOSS'
        signal = 'SELL-REDUCE'
        reason = 'ขาดทุนเกิน threshold ควรควบคุมความเสี่ยง / Loss exceeded threshold; control downside risk.'
    elif profit_pct < 5:
        suggested_action = 'WATCH'
        signal = 'WAIT'
        reason = 'ยังไม่ชัดเจน รอดูทิศทาง / Range-bound; watch confirmation.'
    else:
        suggested_action = 'HOLD'
        signal = 'BUY-ON-DIP' if trend_up else 'HOLD'
        reason = 'โมเมนตัมยังพอถือได้ / Momentum is constructive; continue holding.'

    if current_price <= 0:
        current_price = avg_cost if avg_cost > 0 else 1.0

    entry_low = current_price * (0.98 if trend_up else 0.965)
    entry_high = current_price * (1.01 if trend_up else 0.99)
    stop_loss_price = current_price * (0.94 if trend_up else 0.92)
    target_price = current_price * (1.08 if trend_up else 1.06)
    target_price_2 = current_price * (1.14 if trend_up else 1.1)

    risk_per_share = max(entry_high - stop_loss_price, 0.01)
    reward_per_share = max(target_price - entry_high, 0.01)
    rr_ratio = reward_per_share / risk_per_share

    # Risk sizing heuristic (Phase B): tighter with weaker confidence.
    base_risk_pct = 2.0 if trend_up else 1.2
    if suggested_action in ['CUT LOSS', 'WATCH']:
        base_risk_pct = 0.8
    if rr_ratio < 1.2:
        base_risk_pct *= 0.6
    elif rr_ratio > 2.0:
        base_risk_pct *= 1.15
    position_risk_pct = max(0.5, min(3.0, base_risk_pct))

    confidence = 55
    if trend_up:
        confidence += 12
    if suggested_action == 'HOLD':
        confidence += 8
    if suggested_action == 'TAKE PROFIT':
        confidence += 5
    if suggested_action in ['CUT LOSS', 'WATCH']:
        confidence -= 10
    if rr_ratio >= 2:
        confidence += 8
    elif rr_ratio < 1:
        confidence -= 12
    confidence = max(20, min(92, int(round(confidence))))

    plan = {
        'ticker': ticker,
        'current_price': current_price,
        'avg_cost': avg_cost,
        'profit_pct': profit_pct,
        'suggested_action': suggested_action,
        'signal': signal,
        'entry_low': entry_low,
        'entry_high': entry_high,
        'target_price': target_price,
        'target_price_2': target_price_2,
        'stop_loss_price': stop_loss_price,
        'rr_ratio': rr_ratio,
        'position_risk_pct': position_risk_pct,
        'confidence': confidence,
        'reason': reason,
    }
    if not FEATURE_PHASE_B_SIGNALS:
        plan['entry_low'] = current_price
        plan['entry_high'] = current_price
        plan['target_price_2'] = plan['target_price']
        plan['rr_ratio'] = 1.0
        plan['position_risk_pct'] = 1.0
        plan['confidence'] = 50
    return plan


def track_upsell_event(source: str) -> None:
    if not FEATURE_UPSELL_TRACKING:
        return
    key = str(source or 'unknown').strip().lower()
    try:
        counters = app.storage.client.get('upsell_events', {})
        counters[key] = int(counters.get(key, 0)) + 1
        app.storage.client['upsell_events'] = counters
    except Exception:
        pass
    try:
        print(f"?? Upsell click: {key}")
    except Exception:
        pass


def go_payment_with_tracking(source: str) -> None:
    track_upsell_event(source)
    ui.navigate.to('/payment')


def compute_portfolio_health(assets: list) -> dict:
    if not assets:
        return {
            'score': 0,
            'subscores': {
                'Concentration': 0,
                'Drawdown': 0,
                'Volatility': 0,
                'Correlation': 0,
            },
            'issues': ['No holdings available.'],
            'actions': ['Add holdings to generate a health diagnosis.'],
            'what_if_score': 0,
        }

    values = [max(float(a.get('shares', 0)) * float(a.get('last_price', 0)), 0.0) for a in assets]
    total_value = sum(values)
    if total_value <= 0:
        return {
            'score': 0,
            'subscores': {
                'Concentration': 0,
                'Drawdown': 0,
                'Volatility': 0,
                'Correlation': 0,
            },
            'issues': ['Portfolio value is zero.'],
            'actions': ['Update prices/holdings before diagnosis.'],
            'what_if_score': 0,
        }

    weights = [v / total_value for v in values]
    max_weight = max(weights)
    top3_weight = sum(sorted(weights, reverse=True)[:3])

    pnl_pcts = [float(a.get('profit_pct', 0) or 0) for a in assets]
    neg_pcts = [p for p in pnl_pcts if p < 0]
    loss_exposure = sum(weights[i] for i, p in enumerate(pnl_pcts) if p < 0)
    avg_loss_mag = abs(sum(neg_pcts) / len(neg_pcts)) if neg_pcts else 0.0

    weighted_abs_pnl = sum(abs(pnl_pcts[i]) * weights[i] for i in range(len(assets)))

    concentration_penalty = min(max((max_weight - 0.35) * 100 * 0.9, 0.0), 35.0)
    drawdown_penalty = min((loss_exposure * 100 * 0.35) + (avg_loss_mag * 0.5), 25.0)
    volatility_penalty = min(weighted_abs_pnl * 0.75, 20.0)
    correlation_penalty = min(max((top3_weight - 0.65) * 100 * 0.6, 0.0), 20.0)

    total_penalty = concentration_penalty + drawdown_penalty + volatility_penalty + correlation_penalty
    score = max(5, round(100 - total_penalty))

    def subscore(penalty, cap):
        return max(0, min(100, round(100 - (penalty / cap) * 100)))

    subscores = {
        'Concentration': subscore(concentration_penalty, 35),
        'Drawdown': subscore(drawdown_penalty, 25),
        'Volatility': subscore(volatility_penalty, 20),
        'Correlation': subscore(correlation_penalty, 20),
    }

    issues = []
    actions = []
    if max_weight > 0.35:
        issues.append(f'Concentration risk: top position is {max_weight*100:.1f}% of portfolio.')
        actions.append('Trim top position to below 30-35% and spread into 2-3 uncorrelated names.')
    if loss_exposure > 0.45:
        issues.append(f'Drawdown pressure: {loss_exposure*100:.1f}% of portfolio is in losing positions.')
        actions.append('Set stop-loss rules and scale out of weak trends.')
    if weighted_abs_pnl > 12:
        issues.append('Volatility elevated: portfolio swings are currently high.')
        actions.append('Reduce leverage/high-beta exposure and rebalance into lower-volatility assets.')
    if top3_weight > 0.65:
        issues.append(f'Correlation proxy risk: top 3 holdings = {top3_weight*100:.1f}%.')
        actions.append('Diversify themes/sectors to reduce same-direction shocks.')

    if not issues:
        issues = ['Portfolio structure is balanced with manageable risk.']
        actions = ['Keep allocation discipline and review risk weekly.']

    # Phase B starter: simple "what-if" projected improvement if top actions are applied.
    potential_gain = 0
    if max_weight > 0.35:
        potential_gain += 8
    if loss_exposure > 0.45:
        potential_gain += 7
    if weighted_abs_pnl > 12:
        potential_gain += 5
    if top3_weight > 0.65:
        potential_gain += 6
    what_if_score = min(100, score + potential_gain)

    return {
        'score': score,
        'subscores': subscores,
        'issues': issues[:3],
        'actions': actions[:3],
        'what_if_score': what_if_score,
    }


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
async def main_page(client): 
    create_ticker()
    
    # ?? [แก้บั๊กที่ 1] รอให้ Browser เชื่อมต่อเสร็จสมบูรณ์ 100% ก่อน!
    await client.connected()
    
    # ?? [แก้บั๊กที่ 1] ค่อยดึงข้อมูล User (ตอนนี้รับรองว่าไม่เป็น 0 แล้ว)
    user_id = app.storage.user.get('user_id')
    telegram_id = app.storage.user.get('telegram_id')
    lang = app.storage.user.get('lang', 'TH')
    currency = app.storage.user.get('currency', 'USD')

    async def load_dashboard_data():
        # ?? ย้ายการเรียก Storage มาไว้บนสุดเพื่อแก้บั๊ก AssertionError
        current_group = app.storage.client.get('dashboard_group', 'ALL')
        
        user_info = await run.io_bound(get_user_by_telegram, telegram_id) if telegram_id else {}
        
        curr_sym = '฿' if currency == 'THB' else '$'
        curr_rate = 34.5 if currency == 'THB' else 1.0 
        
        t_welcome = 'ยินดีต้อนรับ' if lang == 'TH' else 'Welcome back,'
        t_status = 'พร้อมเทรด' if lang == 'TH' else 'Ready to trade'
        t_port_val = 'มูลค่าพอร์ตรวม' if lang == 'TH' else 'TOTAL PORTFOLIO VALUE'
        t_add_btn = '+ เพิ่มสินทรัพย์' if lang == 'TH' else '+ ADD HOLDING'
        t_curr_port = 'พอร์ตปัจจุบัน' if lang == 'TH' else 'CURRENT PORTFOLIO'
        
        username = user_info.get('username', f"User_{str(telegram_id)[-4:]}" if telegram_id else 'Guest')
        role = str(user_info.get('role', 'free')).upper()
        role_color = 'text-[#D0FD3E]' if role in ['PRO', 'VIP', 'ADMIN'] else 'text-gray-400'
        
        expiry = user_info.get('vip_expiry')
        status_txt = f'Valid till: {expiry}' if expiry and role in ['PRO', 'VIP', 'ADMIN'] else t_status
        days_left = parse_expiry_to_days_left(expiry)

        raw_portfolio = await run.io_bound(get_portfolio, user_id) if user_id else []
        
        raw_portfolio = await run.io_bound(get_portfolio, user_id) if user_id else []
        
        assets = []
        total_invested, net_worth = 0, 0
        
        # ==========================================
        # ?? 1. ลูปดึงราคาและคำนวณหุ้น (อัปเดตเพิ่ม Sparkline)
        # ==========================================
        for item in raw_portfolio:
            # กรองตามกลุ่มที่เลือก (ALL, DCA, DIV, TRADING)
            if current_group != 'ALL' and item.get('asset_group', 'ALL') != current_group: 
                continue
                
            ticker = item['ticker']
            shares = float(item['shares'])
            avg_cost = float(item['avg_cost'])
            
            # ?? ดึงราคาแบบ Real-time และ กราฟ Sparkline
            last_price = await run.io_bound(get_live_price, ticker)
            sparkline_data, is_up = await run.io_bound(get_sparkline_data, ticker)
            
            # ?? [เพิ่มโค้ดนี้] บังคับกราฟเส้นให้หยักสุดขีด (Normalize 0-100)
            if sparkline_data and len(sparkline_data) > 0:
                sparkline_data = normalize_series(sparkline_data)
            current_value = shares * last_price
            invested = shares * avg_cost
            profit = current_value - invested
            profit_pct = (profit / invested * 100) if invested > 0 else 0
            
            net_worth += current_value
            total_invested += invested
            
            assets.append({
                'ticker': ticker,
                'shares': shares,
                'avg_cost': avg_cost,
                'last_price': last_price,
                'total_value': current_value,
                'profit': profit,
                'profit_pct': profit_pct,
                'asset_group': item.get('asset_group', 'ALL'),
                'alert_price': item.get('alert_price', 0),
                'sparkline': sparkline_data, # ?? ส่งกราฟไปให้ตารางวาด
                'is_up': is_up               # ?? ส่งสีเขียว/แดงไปให้ตาราง
            })

       # ==========================================
        # ?? 2. คำนวณกำไรรวม และหา Top Gainer / Top Loser
        # ==========================================
        # ?? แปลงยอดเงินทั้งหมดตามสกุลเงินที่เลือก (USD หรือ THB)
        net_worth = net_worth * curr_rate
        total_invested = total_invested * curr_rate
        
        total_profit = net_worth - total_invested
        is_profit_overall = total_profit >= 0
        
        sorted_assets = sorted(assets, key=lambda x: x['ticker'])
        profit_sorted = sorted(assets, key=lambda x: x['profit_pct'], reverse=True)
        
        top_gainer = profit_sorted[0] if profit_sorted and profit_sorted[0]['profit_pct'] > 0 else None
        top_loser = profit_sorted[-1] if profit_sorted and profit_sorted[-1]['profit_pct'] < 0 else None

        # ==========================================
        # ?? 3. Sidebar pulse data (Fear & Greed + VIX)
        # ==========================================
        from services.yahoo_finance import get_real_fear_and_greed
        real_fg_value, real_fg_label = await run.io_bound(get_real_fear_and_greed)
        vix = await run.io_bound(get_live_price, '^VIX') or 0.0
        
        fg_value = real_fg_value
        
        if fg_value <= 25:
            fg_color = '#FF453A' 
            fg_label = 'EXTREME FEAR'
            fg_advice = '?? ทยอยเก็บของถูก'
        elif fg_value <= 45:
            fg_color = '#F97316' 
            fg_label = 'FEAR'
            fg_advice = '?? ตลาดกังวล ทยอยสะสม'
        elif fg_value <= 55:
            fg_color = '#8B949E' 
            fg_label = 'NEUTRAL'
            fg_advice = '?? ทรงตัว รอดูทิศทาง'
        elif fg_value <= 75:
            fg_color = '#FCD535' 
            fg_label = 'GREED'
            fg_advice = '?? คึกคัก รันเทรนด์'
        else:
            fg_color = '#32D74B' 
            fg_label = 'EXTREME GREED'
            fg_advice = '?? ระวังการปรับฐาน'

        sidebar_pulse = {
            'fg_value': float(fg_value),
            'fg_label': fg_label,
            'vix': float(vix),
            'mood_color': fg_color,
            'updated_at': datetime.now(UTC).isoformat(),
        }
        try:
            app.storage.client['sidebar_pulse'] = sidebar_pulse
        except RuntimeError:
            # Client can disconnect while background refresh is still running.
            pass

        # ส่งข้อมูลทั้งหมดไปแสดงผล
        return {
            't_welcome': t_welcome, 't_status': t_status, 't_port_val': t_port_val, 't_add_btn': t_add_btn, 't_curr_port': t_curr_port,
            'username': username, 'role': role, 'role_color': role_color, 'status_txt': status_txt,
            'vip_expiry': expiry, 'days_left': days_left,
            'curr_sym': curr_sym, 'curr_rate': curr_rate, 'current_group': current_group,
            'net_worth': net_worth, 'total_profit': total_profit, 'total_invested': total_invested, 'is_profit_overall': is_profit_overall,
            'top_gainer': top_gainer, 'top_loser': top_loser,
            'fg_value': fg_value, 'fg_label': fg_label, 'fg_color': fg_color, 'fg_advice': fg_advice,
            'sidebar_pulse': sidebar_pulse,
            'sorted_assets': sorted_assets
        }

    d = await load_dashboard_data()
    ui_refs = {}

    # ?? จุดที่ 1: ปรับระยะขอบบนเป็น pt-[110px] เพื่อหลบแถบวิ่งให้สวยงาม
    with ui.column().classes('ax-page-shell w-full max-w-7xl mx-auto p-2 sm:p-4 md:p-8 gap-4 md:gap-6 pt-[110px] md:pt-[120px]'):

        async def change_portfolio_group(e):
            app.storage.client['dashboard_group'] = e.value
            await smart_update() # รันทันที ปลอดภัย 100%

        # ?? แถวบน: 2-column fixed (desktop) + compact stack (mobile)
        with ui.grid(columns='grid-cols-1 lg:grid-cols-2').classes('w-full gap-3 md:gap-4 items-stretch'):
            with ui.column().classes('min-w-0 bg-[#12161E]/80 backdrop-blur-xl p-3 md:p-5 rounded-[18px] md:rounded-[20px] border border-white/5 shadow-lg gap-2 transition-all hover:border-white/10 ax-card-hover'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('account_circle', size='md').classes(d['role_color'])
                    with ui.column().classes('gap-0'):
                        ui.label(d['t_welcome']).classes('text-[9px] md:text-[10px] text-gray-500 font-bold uppercase tracking-wider')
                        ui.label(d['username']).classes('text-sm md:text-lg font-black text-white tracking-wide leading-tight')
                        ui.label(f"{d['role']} MEMBER").classes(f'text-[9px] px-2 py-0.5 mt-1 rounded-full border border-[#D0FD3E]/30 bg-[#D0FD3E]/10 {d["role_color"]} font-black tracking-widest uppercase inline-block')

                with ui.row().classes('w-full gap-1.5 md:gap-2 flex-wrap'):
                    chip_cls = 'text-[9px] md:text-[10px] font-bold px-2 py-1 rounded-full bg-white/5 text-gray-300 border border-white/10'
                    ui.label(f"TG: {str(telegram_id)[-6:] if telegram_id else 'N/A'}").classes(chip_cls)
                    ui.label(f"CUR: {'THB' if d['curr_sym'] == '฿' else 'USD'}").classes(chip_cls)
                    ui.label(f"HOLDINGS: {len(d.get('sorted_assets', []))}").classes(chip_cls)
                    ui.label(f"STATUS: {d.get('status_txt', '-')[:18]}").classes('text-[9px] md:text-[10px] font-bold px-2 py-1 rounded-full bg-[#20D6A1]/10 text-[#20D6A1] border border-[#20D6A1]/25')
                    ui.label(f"EXPOSURE: {d.get('curr_sym', '$')}{d.get('total_invested', 0):,.0f}").classes(chip_cls)
                    auth_at = str(app.storage.user.get('auth_at', '')).replace('T', ' ')[:16] if app.storage.user.get('auth_at') else 'N/A'
                    ui.label(f"LOGIN: {auth_at}").classes(chip_cls)

            with ui.column().classes('min-w-0 justify-center bg-gradient-to-br from-[#161B22] to-[#0B0E14] p-3 md:p-5 rounded-[18px] md:rounded-[20px] border border-[#20D6A1]/20 shadow-lg relative overflow-hidden transition-all hover:border-[#39C8FF]/40 ax-neon-ring ax-card-hover'):
                ui.label('VIP COMMAND CENTER').classes('text-[9px] md:text-[10px] text-[#39C8FF] font-black tracking-widest uppercase mb-1 z-10')
                membership_role = d.get('role', 'FREE')
                days_left = d.get('days_left')
                days_text = f'{days_left} DAYS LEFT' if isinstance(days_left, int) and days_left >= 0 else 'NO ACTIVE PACKAGE'
                days_color = 'text-[#2FE8A8]' if isinstance(days_left, int) and days_left >= 0 else 'text-[#FFFF33]'
                ui_refs['vip_days'] = ui.label(days_text).classes(f'text-base md:text-xl font-black {days_color}')
                ui_refs['vip_status'] = ui.label(f'{membership_role} MEMBER').classes('text-[9px] md:text-[10px] text-gray-400 font-black tracking-wider')

                redeem_input = ui.input(placeholder='REDEEM CODE').props('dense outlined dark').classes('w-full mt-1 md:mt-2')

                async def redeem_from_web():
                    code = (redeem_input.value or '').strip().upper()
                    if not code:
                        ui.notify('กรุณากรอกโค้ดก่อน', type='warning')
                        return
                    tid = app.storage.user.get('telegram_id')
                    if not tid:
                        ui.notify('ไม่พบ Telegram ID สำหรับบัญชีนี้', type='negative')
                        return
                    result = await run.io_bound(redeem_code_from_backend, str(tid), code)
                    try:
                        success, _, expiry, role_type = result
                    except Exception:
                        success = False
                        expiry = None
                        role_type = None
                    if success:
                        ui.notify(f'Redeem สำเร็จ: {str(role_type).upper()} ถึง {expiry}', type='positive')
                        ui.navigate.reload()
                    else:
                        if isinstance(result, tuple) and len(result) > 1 and result[1] == 'not_available':
                            ui.notify('ระบบ Redeem backend ยังไม่พร้อมในรอบนี้', type='warning')
                        else:
                            ui.notify('โค้ดไม่ถูกต้อง หรือถูกใช้งานแล้ว', type='negative')

                with ui.row().classes('w-full gap-2 mt-2 flex-col sm:flex-row'):
                    ui.button('Redeem', on_click=redeem_from_web).props('dense').classes('w-full sm:flex-1 bg-[#20D6A1] text-black font-black rounded-lg text-xs')

                    def show_qr_dialog():
                        with ui.dialog() as renew_dialog, ui.card().classes('w-full max-w-md bg-[#0E1C24] border border-[#39C8FF]/30 rounded-3xl p-6'):
                            ui.label('RENEW PRO / VIP').classes('text-lg font-black text-[#39C8FF] tracking-wider')
                            ui.image(build_payment_qr_url()).classes('w-56 h-56 mx-auto mt-2 rounded-xl bg-white p-2')
                            ui.label('KBank 135-1-344-691').classes('text-sm text-white font-black text-center')
                            ui.label('นาย เกียรติศักดิ์ วุฒิจันทร์').classes('text-xs text-gray-400 text-center')
                            ui.label('Scan QR to pay and renew package instantly').classes('text-xs text-gray-400 text-center')
                            ui.button('Go Payment Page', on_click=lambda: ui.navigate.to('/payment')).classes('w-full mt-3 bg-[#20D6A1] text-black font-black rounded-xl py-2')
                            ui.button('Close', on_click=renew_dialog.close).props('flat').classes('w-full text-gray-400')
                        renew_dialog.open()

                    ui.button('Renew', on_click=show_qr_dialog).props('dense').classes('w-full sm:flex-1 bg-[#39C8FF]/20 text-[#39C8FF] font-black rounded-lg text-xs border border-[#39C8FF]/40')

        # ?? จุดที่ 2: โซนเพิ่มสินทรัพย์ ย้ายมาอยู่ใต้ VIP Command Center
        with ui.row().classes('ax-action-strip justify-between items-center md:items-end mt-1 mb-2 gap-4 flex-col md:flex-row'):
            with ui.row().classes('gap-3 items-center w-full md:w-auto'):
                with ui.row().classes('bg-[#32D74B]/10 border border-[#32D74B]/30 rounded-full px-4 py-1.5 items-center gap-2 shadow-inner') as ui_refs['box_gainer']:
                    ui.icon('trending_up', size='sm').classes('text-[#32D74B]')
                    ui.label('TOP GAINER').classes('text-[9px] text-[#32D74B] font-black tracking-widest hidden sm:block')
                    ui_refs['lbl_gainer'] = ui.label('').classes('tabular-nums text-xs md:text-sm font-bold text-white')
                
                with ui.row().classes('bg-[#FF453A]/10 border border-[#FF453A]/30 rounded-full px-4 py-1.5 items-center gap-2 shadow-inner') as ui_refs['box_loser']:
                    ui.icon('trending_down', size='sm').classes('text-[#FF453A]')
                    ui.label('TOP LOSER').classes('text-[9px] text-[#FF453A] font-black tracking-widest hidden sm:block')
                    ui_refs['lbl_loser'] = ui.label('').classes('tabular-nums text-xs md:text-sm font-bold text-white')
            
            with ui.row().classes('gap-2 items-center w-full md:w-auto mt-1 md:mt-0'):
                # 1. ปุ่ม Add Asset (ของเดิม)
                ui.button(d['t_add_btn'], on_click=handle_add_asset, icon='add').classes('w-full md:w-auto bg-[#D0FD3E] text-black font-black rounded-full px-8 py-3 shadow-[0_0_20px_rgba(208,253,62,0.4)] hover:scale-105 transition-transform text-sm')
                
                
                # 2. ?? ปุุ่ม AI REBALANCE (เพิ่มใหม่)
                def run_ai_rebalance():
                    # ?? 1. ดึง Role จากฐานข้อมูลของจริง
                    tid = app.storage.user.get('telegram_id')
                    user_info = get_user_by_telegram(tid) if tid else {}
                    role = str(user_info.get('role', 'free')).lower()
                    
                    # ?? เช็คสิทธิ์ PRO และ Admin เท่านั้น
                    if role not in ['pro', 'admin']:
                        ui.notify('?? ฟีเจอร์ AI Rebalance สงวนสิทธิ์สำหรับแพ็กเกจ PRO เท่านั้น!', type='warning')
                        return
                    
                    # ?? 2. เตรียมข้อมูลพอร์ต (โค้ดดึงข้อมูลพอร์ตของคุณตามปกติ)
                    port_data = ""
                    for a in d['sorted_assets']:
                        pct = (a['shares'] * a['last_price'] / d['total_invested']) * 100 if d['total_invested'] > 0 else 0
                        port_data += f"- หุ้น {a['ticker']}: สัดส่วน {pct:.2f}%, กำไร {a['profit_pct']:+.2f}%\n"
                    
                    # ?? 3. สร้างหน้าต่าง AI (โค้ดหน้าต่าง dialog ตามปกติ) ...
                    
                    # ?? 3. สร้างหน้าต่าง AI โหลด
                    with ui.dialog() as ai_dialog, ui.card().classes('w-full max-w-2xl bg-[#0B0E14] border border-[#FCD535]/50 p-6 rounded-3xl shadow-[0_0_50px_rgba(252,213,53,0.2)]'):
                        ui.label('?? AI REBALANCING STRATEGY').classes('text-xl md:text-2xl font-black text-[#FCD535] mb-2 tracking-widest')
                        loading_spinner = ui.spinner(size='xl', color='#FCD535').classes('mx-auto my-8')
                        ai_result = ui.markdown('').classes('text-white text-sm md:text-base leading-relaxed')
                        ui.button('รับทราบ', on_click=ai_dialog.close).classes('mt-6 w-full bg-white/10 text-white font-black rounded-xl py-3 hover:bg-white/20')
                    
                    ai_dialog.open()
                    
                    # ?? 4. ดึงข้อมูลจาก Gemini API
                    async def fetch_ai():
                        from services.gemini_ai import generate_rebalance_strategy
                        result = await run.io_bound(generate_rebalance_strategy, port_data)
                        loading_spinner.delete()
                        ai_result.set_content(result) 
                    
                    ui.timer(0.1, fetch_ai, once=True)

                # ปุ่มกด AI
                ui.button('?? AI REBALANCE', on_click=run_ai_rebalance).classes('w-full md:w-auto bg-gradient-to-r from-purple-600 to-indigo-500 text-white font-black rounded-full px-6 py-3 shadow-[0_0_20px_rgba(147,51,234,0.4)] hover:scale-105 transition-transform text-sm')

        # ?? กล่องมูลค่าพอร์ต (ย้ายลงล่างตามคำขอ)
        with ui.row().classes('w-full justify-between items-center bg-gradient-to-br from-[#12161E] to-[#0B0E14] border border-white/5 p-5 md:p-8 rounded-[28px] shadow-[0_10px_40px_rgba(0,0,0,0.5)] relative overflow-hidden ax-hero-glow ax-neon-ring'):
            ui.element('div').classes('absolute -top-32 -left-32 w-96 h-96 bg-[#D0FD3E]/10 rounded-full blur-[100px] pointer-events-none')

            with ui.column().classes('gap-1 z-10 flex-1'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label(d['t_port_val']).classes('text-[10px] md:text-xs text-gray-500 font-black tracking-[0.2em] uppercase')

                    def toggle_currency():
                        current_curr = app.storage.user.get('currency', 'USD')
                        app.storage.user['currency'] = 'THB' if current_curr == 'USD' else 'USD'
                        ui.navigate.reload()

                    btn_text = 'THB' if d['curr_sym'] == '$' else 'USD'
                    ui.button(f'Currency: {btn_text}', on_click=toggle_currency).props('flat dense').classes('text-[#D0FD3E] text-[10px] font-black tracking-widest bg-[#D0FD3E]/10 px-3 py-1 rounded-full hover:bg-[#D0FD3E]/20 transition-colors cursor-pointer')

                with ui.row().classes('items-baseline gap-3 md:gap-4'):
                    blink_class = 'blink-green' if d['is_profit_overall'] else 'blink-red'
                    ui_refs['net_worth'] = ui.label(f"{d['curr_sym']}{d['net_worth']:,.2f}").classes(f'tabular-nums text-4xl md:text-[62px] leading-none font-black text-white tracking-tight drop-shadow-lg {blink_class}')

                color_class = 'text-[#32D74B]' if d['is_profit_overall'] else 'text-[#FF453A]'
                sign = "+" if d['is_profit_overall'] else "-"
                pct = (abs(d['total_profit']) / d['total_invested'] * 100) if d['total_invested'] > 0 else 0
                ui_refs['total_profit'] = ui.label(f'{"" if d["is_profit_overall"] else ""} {d["curr_sym"]}{abs(d["total_profit"]):,.2f} ({sign}{pct:.2f}%)').classes(f'tabular-nums text-base md:text-xl font-black mt-2 {color_class} drop-shadow-md')

        def render_trade_plan_panel(panel_assets, role, curr_sym, curr_rate):
            is_pro_plan = str(role).upper() in ['PRO', 'VIP', 'ADMIN']
            holdings_count = len(panel_assets or [])

            with ui.column().classes('w-full ax-card ax-card-hover ax-gradient-bg p-5 md:p-6 gap-4'):
                with ui.row().classes('w-full justify-between items-center flex-wrap gap-3'):
                    with ui.column().classes('gap-0'):
                        ui.label('PRO TRADE PLAN BUILDER').classes('text-xs md:text-sm font-black text-[#20D6A1] tracking-widest uppercase')
                        ui.label('Heuristic decision guide for each holding').classes('text-[10px] text-gray-500 font-bold tracking-wide')
                    lock_text = 'UNLOCKED' if is_pro_plan else 'PRO FEATURE'
                    lock_class = 'text-[#32D74B] border-[#32D74B]/30 bg-[#32D74B]/10' if is_pro_plan else 'text-[#FCD535] border-[#FCD535]/30 bg-[#FCD535]/10'
                    ui.label(lock_text).classes(f'text-[10px] font-black tracking-widest px-3 py-1 rounded-full border {lock_class}')

                if not is_pro_plan:
                    teaser_assets = sorted(panel_assets, key=lambda x: abs(float(x.get('profit_pct', 0) or 0)), reverse=True)[:3]
                    with ui.column().classes('w-full gap-3 bg-[#0B0E14]/70 border border-white/5 rounded-2xl p-4'):
                        with ui.row().classes('w-full items-center justify-between flex-wrap gap-2'):
                            ui.label('?? PRO PREVIEW').classes('text-sm font-black text-[#FCD535] tracking-widest')
                            ui.button('UNLOCK FULL TRADE PLAN', on_click=lambda: go_payment_with_tracking('trade_plan_unlock')).classes('bg-[#FCD535] text-black font-black px-4 py-2 rounded-full text-[10px] shadow-lg hover:scale-105')

                        if teaser_assets:
                            for asset in teaser_assets:
                                plan = build_trade_plan(asset)
                                bias = 'Bullish' if plan['suggested_action'] in ['HOLD', 'TAKE PROFIT'] else 'Defensive'
                                with ui.row().classes('w-full justify-between items-center rounded-xl bg-white/5 border border-white/10 px-3 py-2'):
                                    ui.label(plan['ticker']).classes('text-sm font-black text-white')
                                    teaser_text = f"{plan['signal']} • C{plan['confidence']}" if FEATURE_PHASE_B_SIGNALS else f"Bias: {bias}"
                                    ui.label(teaser_text).classes('text-[10px] font-bold text-gray-300')
                        else:
                            ui.label('ยังไม่มี holdings สำหรับ preview').classes('text-xs text-gray-400')
                    return

                if not panel_assets:
                    with ui.column().classes('w-full items-center justify-center p-6 rounded-2xl bg-[#0B0E14]/50 border border-white/5'):
                        ui.label('ยังไม่มีสินทรัพย์ในพอร์ตสำหรับสร้างแผน / No holdings available.').classes('text-sm text-gray-400 font-bold')
                    return

                action_theme = {
                    'TAKE PROFIT': ('text-[#32D74B]', 'bg-[#32D74B]/10 border-[#32D74B]/30'),
                    'CUT LOSS': ('text-[#FF453A]', 'bg-[#FF453A]/10 border-[#FF453A]/30'),
                    'WATCH': ('text-[#FCD535]', 'bg-[#FCD535]/10 border-[#FCD535]/30'),
                    'HOLD': ('text-[#8AB4FF]', 'bg-[#8AB4FF]/10 border-[#8AB4FF]/30'),
                }

                with ui.grid(columns='grid-cols-1 xl:grid-cols-2').classes('w-full gap-4'):
                    for asset in panel_assets:
                        plan = build_trade_plan(asset)
                        ticker = plan['ticker']
                        current_price = plan['current_price'] * curr_rate
                        avg_cost = plan['avg_cost'] * curr_rate
                        entry_low = plan['entry_low'] * curr_rate
                        entry_high = plan['entry_high'] * curr_rate
                        target_price = plan['target_price'] * curr_rate
                        target_price_2 = plan['target_price_2'] * curr_rate
                        stop_loss_price = plan['stop_loss_price'] * curr_rate
                        profit_pct = plan['profit_pct']
                        suggested_action = plan['suggested_action']
                        signal = plan['signal']
                        rr_ratio = plan['rr_ratio']
                        pos_risk = plan['position_risk_pct']
                        confidence = plan['confidence']
                        reason = plan['reason']
                        txt_class, badge_class = action_theme.get(suggested_action, ('text-gray-300', 'bg-white/5 border-white/10'))

                        with ui.column().classes('w-full bg-[#0B0E14]/70 border border-white/5 rounded-2xl p-4 gap-3 shadow-inner'):
                            with ui.row().classes('w-full justify-between items-start'):
                                with ui.column().classes('gap-0'):
                                    ui.label(ticker).classes('text-xl font-black text-white tracking-wider')
                                    ui.label(f'Current {curr_sym}{current_price:,.2f} • Avg {curr_sym}{avg_cost:,.2f}').classes('text-[11px] text-gray-500 font-bold')
                                with ui.column().classes('items-end gap-1'):
                                    ui.label(suggested_action).classes(f'text-[10px] font-black tracking-widest px-3 py-1 rounded-full border {txt_class} {badge_class}')
                                    if FEATURE_PHASE_B_SIGNALS:
                                        ui.label(f'{signal} • C{confidence}').classes('text-[9px] text-gray-400 font-black')

                            with ui.row().classes('w-full justify-between items-center gap-3 flex-wrap'):
                                pnl_class = 'text-[#32D74B]' if profit_pct >= 0 else 'text-[#FF453A]'
                                ui.label(f'Profit {profit_pct:+.2f}%').classes(f'text-sm font-black {pnl_class}')
                                if FEATURE_PHASE_B_SIGNALS:
                                    ui.label(f'Entry {curr_sym}{entry_low:,.2f}-{curr_sym}{entry_high:,.2f}').classes('text-xs text-[#39C8FF] font-bold')
                                    ui.label(f'TP1 {curr_sym}{target_price:,.2f}').classes('text-xs text-[#32D74B] font-bold')
                                    ui.label(f'TP2 {curr_sym}{target_price_2:,.2f}').classes('text-xs text-[#20D6A1] font-bold')
                                    ui.label(f'SL {curr_sym}{stop_loss_price:,.2f}').classes('text-xs text-[#FF453A] font-bold')
                                    ui.label(f'R:R {rr_ratio:.2f}').classes('text-xs text-[#FCD535] font-black')
                                    ui.label(f'PosRisk {pos_risk:.1f}%').classes('text-xs text-gray-300 font-black')
                                else:
                                    ui.label(f'Target {curr_sym}{target_price:,.2f}').classes('text-xs text-[#32D74B] font-bold')
                                    ui.label(f'Stop {curr_sym}{stop_loss_price:,.2f}').classes('text-xs text-[#FF453A] font-bold')

                            ui.label(reason).classes('text-xs text-gray-400 leading-relaxed')

                            with ui.row().classes('w-full gap-2 mt-1'):
                                async def create_alert_from_plan(sym=ticker, target=plan['target_price']):
                                    user_id = app.storage.user.get('user_id')
                                    if not user_id:
                                        ui.notify('ไม่พบ user session สำหรับสร้าง alert', type='warning')
                                        return
                                    try:
                                        await run.io_bound(set_user_price_alert, str(user_id), sym, float(target), '>')
                                        ui.notify(f'สร้าง Alert ให้ {sym} แล้ว (Target {target:,.2f}) ดูได้ที่หน้า /alerts', type='positive')
                                    except Exception as e:
                                        ui.notify(f'สร้าง Alert ไม่สำเร็จ: {e}', type='negative')

                                ui.button('Create Alert', icon='notifications_active', on_click=create_alert_from_plan).props('outline dense').classes('flex-1 border-[#FCD535]/40 text-[#FCD535] font-black rounded-lg text-xs')
                                ui.button('View Chart', icon='candlestick_chart', on_click=lambda t=ticker: ui.timer(0.1, lambda: handle_chart(t), once=True)).props('dense').classes('flex-1 bg-[#D0FD3E] text-black font-black rounded-lg text-xs')

        trade_plan_container = ui.column().classes('w-full mt-2')
        with trade_plan_container:
            render_trade_plan_panel(
                d.get('sorted_assets', []),
                d.get('role', 'FREE'),
                d.get('curr_sym', '$'),
                d.get('curr_rate', 1.0),
            )

        def render_health_score_panel(panel_assets, role):
            report = compute_portfolio_health(panel_assets or [])
            is_pro = str(role).upper() in ['PRO', 'VIP', 'ADMIN']

            with ui.column().classes('w-full ax-card p-5 md:p-6 gap-4 border border-white/5'):
                with ui.row().classes('w-full justify-between items-center flex-wrap gap-2'):
                    ui.label('PORTFOLIO HEALTH SCORE').classes('text-xs md:text-sm font-black text-[#39C8FF] tracking-widest uppercase')
                    ui.label(f"Score {report['score']}/100").classes('text-sm font-black text-white px-3 py-1 rounded-full bg-[#39C8FF]/15 border border-[#39C8FF]/30')

                if not is_pro:
                    teaser_issue = report['issues'][0] if report['issues'] else 'Risk diagnosis available in PRO'
                    teaser_action = report['actions'][0] if report['actions'] else 'Unlock PRO for full action plan'
                with ui.column().classes('w-full gap-2 rounded-2xl bg-[#0B0E14]/70 border border-white/10 p-4'):
                    ui.label(f'Issue: {teaser_issue}').classes('text-sm text-gray-300 font-bold')
                    ui.label(f'Action: {teaser_action}').classes('text-xs text-gray-400')
                    if FEATURE_PHASE_B_SIGNALS:
                        ui.label('Phase B unlock: Entry/Exit signals + Position sizing + Confidence scoring').classes('text-[10px] text-[#39C8FF] font-bold')
                        ui.button('UNLOCK FULL HEALTH DIAGNOSIS', on_click=lambda: go_payment_with_tracking('health_score_unlock')).classes('bg-[#FCD535] text-black font-black rounded-full px-5 py-2 text-xs w-full md:w-auto')
                return

                with ui.row().classes('w-full gap-2 flex-wrap'):
                    for k, v in report['subscores'].items():
                        badge = '#32D74B' if v >= 70 else '#FCD535' if v >= 45 else '#FF453A'
                        with ui.column().classes('flex-1 min-w-[140px] bg-white/5 rounded-xl border border-white/10 p-3'):
                            ui.label(k).classes('text-[10px] text-gray-500 font-black tracking-widest uppercase')
                            ui.label(f'{v}/100').classes('text-lg font-black').style(f'color:{badge};')

                with ui.column().classes('w-full gap-2 mt-1'):
                    ui.label('TOP ISSUES').classes('text-[10px] text-gray-500 font-black tracking-widest uppercase')
                    for issue in report['issues']:
                        ui.label(f'• {issue}').classes('text-xs text-gray-300')
                    ui.label('ACTION PLAN').classes('text-[10px] text-gray-500 font-black tracking-widest uppercase mt-1')
                    for action in report['actions']:
                        ui.label(f'• {action}').classes('text-xs text-[#20D6A1]')
                    ui.label(f"What-if score after fixes: {report['what_if_score']}/100").classes('text-xs font-black text-[#39C8FF] mt-2')

        health_score_container = ui.column().classes('w-full mt-2')
        with health_score_container:
            render_health_score_panel(
                d.get('sorted_assets', []),
                d.get('role', 'FREE'),
            )

        def refresh_trade_plan_panel(next_data):
            trade_plan_container.clear()
            with trade_plan_container:
                render_trade_plan_panel(
                    next_data.get('sorted_assets', []),
                    next_data.get('role', 'FREE'),
                    next_data.get('curr_sym', '$'),
                    next_data.get('curr_rate', 1.0),
                )

        def refresh_health_score_panel(next_data):
            health_score_container.clear()
            with health_score_container:
                render_health_score_panel(
                    next_data.get('sorted_assets', []),
                    next_data.get('role', 'FREE'),
                )

        with ui.row().classes('w-full justify-between items-center mt-6 mb-2 border-b border-white/5 pb-2 flex-wrap gap-2'):
            with ui.row().classes('items-center gap-2'):
                ui.label('YOUR HOLDINGS').classes('ax-section-title')
                ui.label('Portfolio Filter').classes('text-[10px] text-gray-400 font-bold tracking-widest uppercase')
                ui.select(['ALL', 'DCA', 'TRADING', 'DIV'], value=d['current_group'], on_change=change_portfolio_group).classes('w-28 text-xs').props('outlined dark dense behavior="menu"')

            with ui.row().classes('gap-2 bg-white/5 p-1 rounded-lg border border-white/10 shadow-inner'):
                def set_sort(key):
                    if app.storage.client.get('sort_key') == key:
                        app.storage.client['sort_desc'] = not app.storage.client.get('sort_desc', False)
                    else:
                        app.storage.client['sort_key'] = key
                        app.storage.client['sort_desc'] = True 
                    trigger_sort_refresh()

                btn_class = 'text-[10px] font-bold tracking-wider px-3 py-1 text-gray-400 hover:text-white transition-colors'
                ui.button('A-Z', icon='sort_by_alpha', on_click=lambda: set_sort('ticker')).props('flat dense size=sm').classes(btn_class)
                ui.button('PROFIT', icon='percent', on_click=lambda: set_sort('profit_pct')).props('flat dense size=sm').classes(btn_class)
                ui.button('VALUE', icon='attach_money', on_click=lambda: set_sort('total_value')).props('flat dense size=sm').classes(btn_class)

        # กล่องสำหรับใส่ตาราง
        table_container = ui.column().classes('w-full')
        
        # ฟังก์ชันสร้างตารางที่มีการ Sort
        # ฟังก์ชันสร้างตาราง (ลบ @ui.refreshable ทิ้งแล้ว)
        def draw_table():
            assets_to_show = d.get('sorted_assets', [])
            # (โค้ด Sort เหมือนเดิม)
            sort_key = app.storage.client.get('sort_key', 'ticker')
            sort_desc = app.storage.client.get('sort_desc', False)
            if assets_to_show:
                if sort_key == 'ticker': assets_to_show = sorted(assets_to_show, key=lambda x: x['ticker'], reverse=sort_desc)
                elif sort_key == 'profit_pct': assets_to_show = sorted(assets_to_show, key=lambda x: x['profit_pct'], reverse=sort_desc)
                elif sort_key == 'total_value': assets_to_show = sorted(assets_to_show, key=lambda x: x['shares'] * x['last_price'], reverse=sort_desc)

            # ?? ส่ง ui_refs เข้าไปด้วย เพื่อผูกหน้าจอ
            create_portfolio_table(
                assets_to_show,
                on_edit=handle_edit,
                on_news=handle_news,
                on_chart=handle_chart,
                ui_refs=ui_refs,
            )
            
        # สร้างกล่อง (เคลียร์ของเก่าทิ้งก่อนวาดใหม่เมื่อกดปุ่ม Sort)
        table_container = ui.column().classes('w-full')
        with table_container:
            draw_table()
            
        def trigger_sort_refresh():
            table_container.clear()
            with table_container:
                draw_table()
# ==========================================
        # ?? ระบบ Popup สรุปพอร์ต (V4 - Executive Briefing UI)
        # ==========================================
        def _today_local_str() -> str:
            return datetime.now().strftime('%Y-%m-%d')

        def _popup_seen_today() -> bool:
            today_str = _today_local_str()
            user_seen = app.storage.user.get('last_summary_date', '')
            browser_seen = ''
            try:
                browser_seen = app.storage.browser.get('last_summary_date', '')
            except Exception:
                browser_seen = ''
            return user_seen == today_str or browser_seen == today_str

        def _mark_popup_seen_today() -> None:
            today_str = _today_local_str()
            app.storage.user['last_summary_date'] = today_str
            try:
                app.storage.browser['last_summary_date'] = today_str
            except Exception:
                pass

        def show_daily_summary_popup(net_worth, total_invested, total_profit, assets, curr_sym='$', meta=None):
            today_str = _today_local_str()
            last_seen = app.storage.user.get('last_summary_date', '')

            assets = assets or []
            meta = meta or {}

            top_gainer = meta.get('top_gainer')
            top_loser = meta.get('top_loser')

            member_role = str(meta.get('role', 'FREE')).upper()
            days_left = meta.get('days_left')
            membership_line = (
                f'{days_left} days left'
                if isinstance(days_left, int) and days_left >= 0
                else 'No active package'
            )

            # ใช้ curr_sym ที่ส่งเข้ามา เพื่อให้ popup ตรงกับ dashboard
            curr_rate = 34.5 if curr_sym == '฿' else 1.0

            # เช็คซ้ำอีกรอบแบบของเดิม (ปลอดภัย)
            if last_seen != today_str:
                profit_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
                is_profit = total_profit >= 0
                p_color = '#32D74B' if is_profit else '#FF453A'
                p_sign = '+' if is_profit else '-'

                # ปุ่มลัด: ปิด popup แล้วค่อยเปิด dialog ของเดิม
                def open_add_from_popup():
                    dialog.close()
                    ui.timer(0.1, handle_add_asset, once=True)

                def open_ai_from_popup():
                    dialog.close()
                    ui.timer(0.1, run_ai_rebalance, once=True)

                with ui.dialog().props('backdrop-filter="blur(10px)"') as dialog:
                    with ui.card().classes(
                        'w-full max-w-[440px] bg-[#05070A]/95 backdrop-blur-3xl '
                        'border border-white/10 p-0 rounded-[36px] overflow-hidden '
                        'shadow-[0_30px_60px_rgba(0,0,0,0.8)] flex flex-col'
                    ):

                        # =========================
                        # 1) HERO SUMMARY
                        # =========================
                        with ui.column().classes(
                            'w-full p-8 pb-8 bg-gradient-to-b from-[#12161E] to-transparent '
                            'relative items-center text-center border-b border-white/5'
                        ):
                            ui.element('div').classes(
                                'absolute top-10 left-1/2 -translate-x-1/2 '
                                'w-48 h-48 rounded-full blur-[70px] pointer-events-none'
                            ).style(f'background-color: {p_color}15;')

                            ui.label('LOGIN BRIEFING 2.0').classes(
                                'text-[9px] text-gray-500 font-black tracking-[0.3em] '
                                'uppercase mb-4 z-10'
                            )

                            ui.label(f"{curr_sym}{net_worth:,.2f}").classes(
                                'text-5xl font-black text-white tracking-tight '
                                'leading-none drop-shadow-lg z-10'
                            )

                            with ui.row().classes(
                                'mt-5 px-5 py-2 rounded-full border items-center '
                                'gap-2 z-10 shadow-inner'
                            ).style(f'background-color: {p_color}10; border-color: {p_color}30;'):
                                ui.icon(
                                    'trending_up' if is_profit else 'trending_down',
                                    size='sm'
                                ).style(f'color: {p_color};')
                                ui.label(
                                    f"{p_sign}{curr_sym}{abs(total_profit):,.2f} "
                                    f"({p_sign}{abs(profit_pct):.2f}%)"
                                ).classes('text-sm font-black tracking-wide').style(f'color: {p_color};')

                        # =========================
                        # 2) PORTFOLIO SNAPSHOT
                        # =========================
                        with ui.column().classes('w-full px-6 pt-4 gap-3'):
                            ui.label('PORTFOLIO SNAPSHOT').classes(
                                'text-[10px] text-gray-500 font-bold tracking-widest uppercase'
                            )

                            with ui.row().classes('w-full gap-3 flex-col sm:flex-row'):
                                # Top Gainer
                                with ui.column().classes(
                                    'flex-1 bg-[#32D74B]/10 border border-[#32D74B]/20 '
                                    'rounded-2xl p-3'
                                ):
                                    ui.label('TOP GAINER').classes(
                                        'text-[9px] text-[#32D74B] font-black tracking-widest'
                                    )
                                    if top_gainer:
                                        ui.label(
                                            f"{top_gainer.get('ticker', '-')} "
                                            f"{top_gainer.get('profit_pct', 0):+.2f}%"
                                        ).classes('text-sm font-black text-white')
                                    else:
                                        ui.label('ไม่มีตัวบวกเด่นวันนี้').classes(
                                            'text-sm text-gray-400'
                                        )

                                # Top Loser
                                with ui.column().classes(
                                    'flex-1 bg-[#FF453A]/10 border border-[#FF453A]/20 '
                                    'rounded-2xl p-3'
                                ):
                                    ui.label('TOP LOSER').classes(
                                        'text-[9px] text-[#FF453A] font-black tracking-widest'
                                    )
                                    if top_loser:
                                        ui.label(
                                            f"{top_loser.get('ticker', '-')} "
                                            f"{top_loser.get('profit_pct', 0):+.2f}%"
                                        ).classes('text-sm font-black text-white')
                                    else:
                                        ui.label('ไม่มีตัวลบเด่นวันนี้').classes(
                                            'text-sm text-gray-400'
                                        )

                            with ui.row().classes(
                                'w-full justify-between items-center rounded-2xl '
                                'px-4 py-3 border border-white/5 bg-white/5'
                            ):
                                ui.label(f'{member_role} MEMBER').classes(
                                    'text-[11px] font-black tracking-widest text-[#39C8FF]'
                                )
                                ui.label(membership_line).classes(
                                    'text-[10px] text-gray-400 font-bold text-right'
                                )

                        # =========================
                        # 3) ASSET LIST
                        # =========================
                        with ui.column().classes('w-full p-6 pt-4 gap-4'):
                            with ui.row().classes('w-full justify-between items-end mb-1 px-1'):
                                ui.label('ASSET PERFORMANCE').classes(
                                    'text-[10px] text-gray-500 font-bold tracking-widest uppercase'
                                )
                                ui.label(f'{len(assets)} Holdings').classes(
                                    'text-[10px] text-gray-600 font-bold'
                                )

                            with ui.column().classes(
                                'w-full gap-3 overflow-y-auto custom-scrollbar '
                                'max-h-[250px] pr-2'
                            ):
                                if not assets:
                                    ui.label('ยังไม่มีสินทรัพย์ในพอร์ต').classes(
                                        'text-gray-500 text-sm text-center w-full my-4'
                                    )
                                else:
                                    for a in assets:
                                        ticker = a.get('ticker', 'N/A')
                                        shares = float(a.get('shares', 0))
                                        base_cost = float(a.get('avg_cost', 0))
                                        base_price = float(a.get('last_price', 0))

                                        # แปลงค่าเงินให้ตรงกับ popup
                                        cost = base_cost * curr_rate
                                        price = base_price * curr_rate
                                        val = shares * price
                                        prof = (price - cost) * shares
                                        p_pct = float(a.get('profit_pct', 0))

                                        a_color = '#32D74B' if prof >= 0 else '#FF453A'
                                        logo_text = ticker[0] if ticker else '?'

                                        with ui.row().classes(
                                            'w-full justify-between items-center p-3 rounded-2xl '
                                            'bg-white/5 hover:bg-white/10 transition-colors '
                                            'border border-white/5 cursor-default'
                                        ):
                                            with ui.row().classes('items-center gap-3'):
                                                with ui.element('div').classes(
                                                    'w-10 h-10 rounded-full bg-[#0B0E14] '
                                                    'border border-white/10 flex items-center '
                                                    'justify-center shadow-inner'
                                                ):
                                                    ui.label(logo_text).classes(
                                                        'text-gray-300 font-black text-lg'
                                                    )

                                                with ui.column().classes('gap-0'):
                                                    ui.label(ticker).classes(
                                                        'font-black text-white text-base leading-tight'
                                                    )
                                                    ui.label(
                                                        f"{shares:,.4f} @ {curr_sym}{cost:,.2f}"
                                                    ).classes(
                                                        'text-[10px] text-gray-500 font-bold mt-0.5'
                                                    )

                                            with ui.column().classes('items-end gap-0'):
                                                ui.label(f"{curr_sym}{val:,.2f}").classes(
                                                    'font-black text-white text-sm'
                                                )
                                                ui.label(f"{p_pct:+.2f}%").classes(
                                                    'text-[11px] font-black tracking-wide'
                                                ).style(f'color: {a_color};')

                            # =========================
                            # 4) QUICK ACTIONS
                            # =========================
                            with ui.column().classes('w-full mt-4 gap-2'):
                                ui.button(
                                    'ENTER DASHBOARD',
                                    on_click=dialog.close
                                ).classes(
                                    'w-full bg-white text-black font-black rounded-2xl py-4 '
                                    'shadow-[0_0_20px_rgba(255,255,255,0.15)] '
                                    'hover:bg-gray-200 hover:scale-[1.02] transition-all '
                                    'tracking-[0.2em] text-xs'
                                )

                                with ui.row().classes('w-full gap-2'):
                                    ui.button(
                                        '+ ADD HOLDING',
                                        on_click=open_add_from_popup
                                    ).classes(
                                        'flex-1 bg-[#D0FD3E] text-black font-black rounded-2xl py-3 '
                                        'hover:scale-[1.02] transition-all text-[11px]'
                                    )

                                    ui.button(
                                        '?? AI REBALANCE',
                                        on_click=open_ai_from_popup
                                    ).classes(
                                        'flex-1 bg-gradient-to-r from-purple-600 to-indigo-500 '
                                        'text-white font-black rounded-2xl py-3 '
                                        'hover:scale-[1.02] transition-all text-[11px]'
                                    )

                dialog.open()
                _mark_popup_seen_today()

        # ?? [แก้บั๊กที่ 2] ฟังก์ชันตัวกลางสำหรับรอให้ข้อมูลโหลด 100% ก่อนเด้ง Popup
        async def trigger_popup():
            if not client.has_socket_connection:
                return
            nd = await load_dashboard_data()
            
            # เช็คว่ายังไม่เคยดูวันนี้ และพอร์ตต้องโหลดข้อมูลเสร็จแล้ว (เงิน > 0)
            if (not _popup_seen_today()) and nd['total_invested'] > 0:
                show_daily_summary_popup(
                    nd['net_worth'],
                    nd['total_invested'],
                    nd['total_profit'],
                    nd['sorted_assets'],
                    curr_sym=nd.get('curr_sym', '$'),
                    meta=nd,
                )

        # หน่วงเวลา 1.5 วินาที ให้หน้าเว็บหลักโหลดโครงสร้างเสร็จก่อน ค่อยประมวลผล Popup
        ui.timer(1.5, trigger_popup, once=True)

    # (โค้ดเดิม) ฟังก์ชันอัปเดตข้อมูลแบบ Real-time
    async def smart_update():
        # ?? เพิ่มบรรทัดนี้: เช็คว่า Browser ยังเชื่อมต่ออยู่ไหม ถ้าปิดไปแล้วให้หยุดทำงานทันที!
        if not client.has_socket_connection: return 
        
        if app.storage.client.get('modal_open', False): return
        nd = await load_dashboard_data()

        def safe_remove_pop(el):
            try:
                el.classes(remove='animate-pop')
            except RuntimeError:
                pass

        # 1. อัปเดต VIP Command Center
        days_left = nd.get('days_left')
        days_text = f'{days_left} DAYS LEFT' if isinstance(days_left, int) and days_left >= 0 else 'NO ACTIVE PACKAGE'
        days_color = 'text-[#2FE8A8]' if isinstance(days_left, int) and days_left >= 0 else 'text-[#FF5E6C]'
        if 'vip_days' in ui_refs:
            ui_refs['vip_days'].set_text(days_text)
            ui_refs['vip_days'].classes(remove='text-[#2FE8A8] text-[#FF5E6C]', add=days_color)
        if 'vip_status' in ui_refs:
            ui_refs['vip_status'].set_text(f"{nd.get('role', 'FREE')} MEMBER")

        # 2. ?? อัปเดตยอดเงิน (พร้อมเช็คการเปลี่ยนแปลงเพื่อเล่นอนิเมชั่น)
        old_nw = app.storage.client.get('last_nw', 0)
        new_nw = nd['net_worth']
        app.storage.client['last_nw'] = new_nw
        
        new_blink = 'blink-green' if nd['is_profit_overall'] else 'blink-red'
        new_color = 'text-[#32D74B]' if nd['is_profit_overall'] else 'text-[#FF453A]'
        sign = "+" if nd['is_profit_overall'] else "-"
        pct = (abs(nd['total_profit']) / nd['total_invested'] * 100) if nd['total_invested'] > 0 else 0
        
        ui_refs['net_worth'].set_text(f"{nd['curr_sym']}{nd['net_worth']:,.2f}")
        ui_refs['net_worth'].classes(remove='blink-green blink-red', add=new_blink)
        
        # ?? เล่นอนิเมชั่นเด้ง (Pop) ถ้ายอดเงินมีการเปลี่ยนแปลง!
        if old_nw != new_nw and old_nw != 0:
            ui_refs['net_worth'].classes(add='animate-pop')
            ui.timer(0.4, lambda: safe_remove_pop(ui_refs['net_worth']), once=True)

        ui_refs['total_profit'].set_text(f'{"" if nd["is_profit_overall"] else ""} {nd["curr_sym"]}{abs(nd["total_profit"]):,.2f} ({sign}{pct:.2f}%)')
        ui_refs['total_profit'].classes(remove='text-[#32D74B] text-[#FF453A]', add=new_color)
        
        # 3. ?? อัปเดตหุ้นเด่น (เปลี่ยนเป็นทศนิยม 2 ตำแหน่ง + ใส่อนิเมชั่นเด้ง)
        if nd['top_gainer']:
            new_gainer = f"{nd['top_gainer']['ticker']} +{nd['top_gainer']['profit_pct']:.2f}%"
            if ui_refs['lbl_gainer'].text != new_gainer:
                ui_refs['lbl_gainer'].set_text(new_gainer)
                ui_refs['lbl_gainer'].classes(add='animate-pop')
                ui.timer(0.4, lambda: safe_remove_pop(ui_refs['lbl_gainer']), once=True)
            ui_refs['box_gainer'].set_visibility(True)
        else: ui_refs['box_gainer'].set_visibility(False)
            
        if nd['top_loser']:
            new_loser = f"{nd['top_loser']['ticker']} {nd['top_loser']['profit_pct']:.2f}%"
            if ui_refs['lbl_loser'].text != new_loser:
                ui_refs['lbl_loser'].set_text(new_loser)
                ui_refs['lbl_loser'].classes(add='animate-pop')
                ui.timer(0.4, lambda: safe_remove_pop(ui_refs['lbl_loser']), once=True)
            ui_refs['box_loser'].set_visibility(True)
        else: ui_refs['box_loser'].set_visibility(False)
        # ?? 4. ยิงข้อมูลอัปเดตเข้าการ์ดหุ้น "ทีละใบแบบเนียนๆ" (ไม่กระพริบ!)
        # เช็คว่าจำนวนหุ้นเพิ่ม/ลด หรือไม่ ถ้าใช่ ค่อยลบวาดใหม่
        current_tickers = [a['ticker'] for a in d['sorted_assets']]
        new_tickers = [a['ticker'] for a in nd['sorted_assets']]
        
        d['sorted_assets'] = nd['sorted_assets']
        d['sidebar_pulse'] = nd.get('sidebar_pulse', {})
        refresh_trade_plan_panel(nd)
        refresh_health_score_panel(nd)
        
        if current_tickers != new_tickers:
            trigger_sort_refresh() # ถ้ามีการเพิ่ม/ลบหุ้น ให้วาดใหม่
        else:
            # ถ้าหุ้นเท่าเดิม ให้ยิงตัวเลขและกราฟทะลุการ์ดเข้าไปเลย
            for a in nd['sorted_assets']:
                t = a['ticker']
                if f'val_{t}' in ui_refs:
                    curr_sym = nd['curr_sym']
                    curr_rate = 34.5 if app.storage.user.get('currency', 'USD') == 'THB' else 1.0
                    
                    # แปลงค่าให้ตรงสกุลเงิน
                    cost = float(a['avg_cost']) * curr_rate
                    last_price = float(a['last_price']) * curr_rate
                    total_value = float(a['shares']) * last_price
                    profit = (last_price - cost) * float(a['shares'])
                    profit_pct = a['profit_pct']
                    
                    p_color = '#32D74B' if profit >= 0 else '#FF453A'
                    p_sign = '+' if profit >= 0 else ''

                    # ?? เด้ง Pop ทันทีถ้าราคาเปลี่ยน
                    new_val_str = f"{curr_sym}{total_value:,.2f}"
                    if ui_refs[f'val_{t}'].text != new_val_str:
                        ui_refs[f'val_{t}'].set_text(new_val_str)
                        ui_refs[f'val_{t}'].style(f'color: {p_color};')
                        ui_refs[f'val_{t}'].classes(add='animate-pop')
                        ui.timer(0.4, lambda t=t: safe_remove_pop(ui_refs[f'val_{t}']), once=True)
                    
                    # อัปเดต ราคาล่าสุด ป้าย PnL 
                    ui_refs[f'lbl_price_{t}'].set_text(f"Price: {curr_sym}{last_price:,.2f}")
                    ui_refs[f'prof_{t}'].set_text(f"{p_sign}{curr_sym}{abs(profit):,.2f} ({p_sign}{profit_pct:.2f}%)")
                    ui_refs[f'prof_{t}'].style(f'color: {p_color}; background-color: {p_color}10;')
                    
                    # อัปเดต Sparkline
                    if a.get('sparkline') and f'spark_{t}' in ui_refs:
                        spark_data = a['sparkline']
                        
                        # ?? บังคับสีให้ตรงกับทิศทางกราฟ 100% (ปลาย >= ต้น = สีเขียว)
                        is_chart_up = spark_data[-1] >= spark_data[0] if len(spark_data) > 1 else True
                        s_color = '#32D74B' if is_chart_up else '#FF453A'
                        
                        ui_refs[f'spark_{t}'].options['series'][0]['data'] = spark_data
                        ui_refs[f'spark_{t}'].options['series'][0]['lineStyle']['color'] = s_color
                        ui_refs[f'spark_{t}'].options['series'][0]['lineStyle']['shadowColor'] = s_color
                        ui_refs[f'spark_{t}'].options['series'][0]['areaStyle']['color'] = s_color
                        ui_refs[f'spark_{t}'].update()

    await smart_update()
    ui.timer(8.0, smart_update)    
       # อัปเดตข้อมูลให้ตารางและสั่ง refresh
    
# ==========================================
# 3. หน้าวิเคราะห์พอร์ต (PORTFOLIO ANALYTICS) - Premium UI
# ==========================================
@ui.page('/analytics')
@standard_page_frame
async def analytics_page(client):
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker() 
    # ?? [แก้บั๊ก] ดึง Storage ขึ้นมาก่อน
    lang = app.storage.user.get('lang', 'TH')
    user_id = app.storage.user.get('user_id')
    await client.connected()
    t_title = 'วิเคราะห์พอร์ตเชิงลึก' if lang == 'TH' else 'PORTFOLIO ANALYTICS'
    t_sub = 'เจาะลึกประสิทธิภาพพอร์ตและกลยุทธ์ AI' if lang == 'TH' else 'Deep dive into your portfolio performance and AI strategy.'
    
    user_id = app.storage.user.get('user_id')
    raw_portfolio = await run.io_bound(get_portfolio, user_id) if user_id else []
    
    tickers_list = [item['ticker'] for item in raw_portfolio]
    from services.yahoo_finance import get_advanced_stock_info
    advanced_info = await run.io_bound(get_advanced_stock_info, tickers_list)

    def get_filtered_data(group='ALL'):
        filtered = [item for item in raw_portfolio if group == 'ALL' or item.get('asset_group', 'ALL') == group]
        data = []
        total = 0
        for item in filtered:
            val = item['shares'] * get_live_price(item['ticker']) 
            total += val
            sector = advanced_info.get(item['ticker'], {}).get('sector', 'Unknown')
            data.append({'ticker': item['ticker'], 'value': val, 'shares': item['shares'], 'sector': sector})
        return sorted(data, key=lambda x: x['value'], reverse=True), total

    with ui.column().classes('w-full max-w-7xl mx-auto p-4 md:p-8 gap-6 pt-[110px] md:pt-[120px] items-center'):
        
        # ?? HEADER SECTION
        with ui.row().classes('w-full justify-between items-center bg-gradient-to-br from-[#12161E] to-[#0B0E14] border border-white/5 p-6 md:p-8 rounded-[32px] shadow-[0_10px_40px_rgba(0,0,0,0.5)] relative overflow-hidden'):
            ui.element('div').classes('absolute -top-20 -right-20 w-64 h-64 bg-[#32D74B]/10 rounded-full blur-[80px] pointer-events-none')
            
            with ui.column().classes('gap-1 z-10'):
                ui.label(t_title).classes('text-2xl md:text-3xl font-black text-white tracking-widest uppercase')
                ui.label(t_sub).classes('text-xs md:text-sm text-gray-400')
            
            with ui.row().classes('items-center gap-4 bg-[#0B0E14]/80 backdrop-blur-md p-4 rounded-2xl border border-white/5 z-10 shadow-inner mt-4 md:mt-0'):
                with ui.column().classes('items-end gap-0'):
                    ui.label('PORTFOLIO BETA (RISK)').classes('text-[10px] font-black text-gray-500 tracking-widest uppercase')
                    avg_beta = sum([advanced_info.get(t, {}).get('beta', 1.0) for t in tickers_list]) / max(len(tickers_list), 1)
                    risk_label = "High" if avg_beta > 1.2 else "Moderate" if avg_beta > 0.8 else "Low"
                    ui.label(f'{avg_beta:.2f} ({risk_label})').classes('text-lg md:text-xl font-black text-white')
                ui.circular_progress(value=min(avg_beta/2, 1.0), show_value=False, size='45px', color='warning').classes('text-orange-400')

        # ?? MODE TOGGLE
        with ui.row().classes('w-full justify-center z-10 -mt-2'):
            mode_toggle = ui.toggle(['Allocation', 'Real Growth', 'Port Doctor', 'Sector Flow'], value='Allocation') \
                .classes('bg-[#12161E]/80 backdrop-blur-xl text-gray-400 rounded-full p-1 border border-white/5 shadow-lg font-bold') \
                .props('unelevated dark color=positive text-color=black')

        with ui.row().classes('w-full justify-center gap-3 flex-wrap'):
            growth_period = ui.select(options=['1M', '3M', '6M', '1Y', '3Y', '5Y'], value='1Y', label='Growth Range').props('outlined dense').classes('w-32')
            growth_benchmark = ui.select(options=['SPY', 'QQQ'], value='SPY', label='Benchmark').props('outlined dense').classes('w-28')
            sector_window = ui.select(options=['5D', '1M', '3M', '6M'], value='1M', label='Sector Window').props('outlined dense').classes('w-32')
        # ?? CHART & LIST AREA (แก้กราฟเบี้ยวด้วย w-full min-w-0)
        with ui.row().classes('w-full gap-6 mt-2 flex-col lg:flex-row items-stretch'):
            chart_card = ui.column().classes('flex- w-full min-w-0 bg-[#12161E]/60 backdrop-blur-xl border border-white/5 p-0 rounded-[32px] h-[500px] lg:h-[600px] relative overflow-hidden shadow-2xl')
            list_card = ui.column().classes('flex- w-full min-w-0 bg-[#12161E]/60 backdrop-blur-xl border border-white/5 p-0 rounded-[32px] h-[500px] lg:h-[600px] overflow-hidden shadow-2xl')

        current_group = {'val': 'ALL'}

        async def update_view(e=None):
            mode = mode_toggle.value
            growth_period.set_visibility(mode == 'Real Growth')
            growth_benchmark.set_visibility(mode == 'Real Growth')
            sector_window.set_visibility(mode == 'Sector Flow')
            chart_card.clear()
            list_card.clear()
            
            assets_data, total_value = get_filtered_data(current_group['val'])
            
            with chart_card:
                if not assets_data and mode != 'Sector Flow':
                    with ui.column().classes('absolute-center items-center gap-4'):
                        ui.icon('pie_chart', size='4xl').classes('text-gray-600')
                        ui.label('No data available').classes('text-gray-500 font-bold text-lg')
                
                elif mode == 'Allocation':
                    pie_data = [{'value': round(a['value'], 2), 'name': a['ticker']} for a in assets_data]
                    ui.echart({
                        'tooltip': {'trigger': 'item', 'backgroundColor': '#12161E', 'borderColor': '#32D74B', 'textStyle': {'color': '#fff'}},
                        'legend': {'orient': 'vertical', 'left': '5%', 'top': 'center', 'textStyle': {'color': '#8B949E', 'fontSize': 12}},
                        'series': [{'name': 'Portfolio', 'type': 'pie', 'radius': ['45%', '75%'], 'center': ['55%', '50%'], 'itemStyle': {'borderRadius': 12, 'borderColor': '#0B0E14', 'borderWidth': 4}, 'label': {'show': True, 'color': '#fff', 'formatter': '{b}\n{d}%', 'fontWeight': 'bold'}, 'data': pie_data}]
                    }).classes('w-full h-full p-4')
                    with ui.column().classes('absolute top-1/2 left-[55%] -translate-x-1/2 -translate-y-1/2 items-center gap-0 pointer-events-none'):
                        ui.label(f"${total_value:,.0f}").classes('text-3xl md:text-4xl font-black text-white drop-shadow-lg')
                        ui.label('TOTAL VALUE').classes('text-[10px] text-gray-500 font-bold uppercase tracking-widest')

                elif mode == 'Real Growth':
                    period_map = {'1M': '1mo', '3M': '3mo', '6M': '6mo', '1Y': '1y', '3Y': '3y', '5Y': '5y'}
                    growth = await run.io_bound(
                        get_portfolio_historical_growth,
                        raw_portfolio,
                        period_map.get(growth_period.value, '1y'),
                        '1d',
                        growth_benchmark.value or 'SPY',
                    )
                    labels = growth.get('labels', [])
                    p_values = growth.get('portfolio_values', [])
                    b_values = growth.get('benchmark_values', [])
                    p_metrics = growth.get('portfolio_metrics', {})
                    b_metrics = growth.get('benchmark_metrics', {})
                    updated_at = str(growth.get('updated_at', '')).replace('T', ' ')[:19]
                    bench_name = growth.get('benchmark_ticker', growth_benchmark.value or 'SPY')

                    if not labels or not p_values:
                        with ui.column().classes('absolute-center items-center gap-3'):
                            ui.icon('query_stats', size='4xl').classes('text-gray-600')
                            ui.label('Insufficient data for growth analysis').classes('text-gray-400 font-bold')
                    else:
                        with ui.row().classes('w-full gap-2 absolute top-3 left-3 z-20 flex-wrap'):
                            ui.label(f"Return {p_metrics.get('return_pct', 0):+.2f}%").classes('text-[10px] font-black px-2 py-1 rounded-full bg-[#20D6A1]/15 text-[#20D6A1] border border-[#20D6A1]/30')
                            ui.label(f"MDD {p_metrics.get('max_drawdown_pct', 0):.2f}%").classes('text-[10px] font-black px-2 py-1 rounded-full bg-white/10 text-white border border-white/20')
                            ui.label(f"Vol {p_metrics.get('volatility_annual_pct', 0):.2f}%").classes('text-[10px] font-black px-2 py-1 rounded-full bg-[#39C8FF]/15 text-[#39C8FF] border border-[#39C8FF]/30')
                            ui.label(f"Source: Yahoo • {updated_at}").classes('text-[10px] font-bold px-2 py-1 rounded-full bg-white/5 text-gray-300 border border-white/10')

                        ui.echart({
                            'tooltip': {'trigger': 'axis', 'backgroundColor': '#12161E', 'textStyle': {'color': '#fff'}},
                            'legend': {'data': ['Portfolio', bench_name], 'top': 8, 'textStyle': {'color': '#8B949E'}},
                            'grid': {'left': '8%', 'right': '5%', 'bottom': '12%', 'top': '18%'},
                            'xAxis': {'type': 'category', 'boundaryGap': False, 'data': labels, 'axisLine': {'lineStyle': {'color': '#8B949E'}}},
                            'yAxis': {'type': 'value', 'scale': True, 'splitLine': {'lineStyle': {'color': '#1C2128', 'type': 'dashed'}}},
                            'series': [
                                {'name': 'Portfolio', 'data': p_values, 'type': 'line', 'smooth': True, 'symbol': 'none', 'lineStyle': {'color': '#32D74B', 'width': 3}},
                                {'name': bench_name, 'data': b_values, 'type': 'line', 'smooth': True, 'symbol': 'none', 'lineStyle': {'color': '#39C8FF', 'width': 2, 'type': 'dashed'}},
                            ]
                        }).classes('w-full h-full p-4')

                elif mode == 'Port Doctor':
                    with ui.column().classes('w-full h-full p-6 md:p-8 items-center justify-center relative'):
                        ui.element('div').classes('absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[#32D74B]/10 via-transparent to-transparent opacity-50 pointer-events-none')
                        ui.icon('health_and_safety', size='64px').classes('text-[#32D74B] mb-4 drop-shadow-[0_0_20px_rgba(50,215,75,0.8)] animate-pulse')
                        ui.label('PORT DOCTOR DIAGNOSIS').classes('text-2xl md:text-3xl font-black text-white tracking-widest text-center')
                        ui.label('ให้ AI สวมบทคุณหมอ สแกนสุขภาพพอร์ตแบบเจาะลึก พร้อมจัดยา (คำแนะนำ) เพื่อแก้พอร์ตติดดอย').classes('text-gray-400 text-sm mt-2 text-center max-w-md')
                        
                        ai_loading = ui.spinner('dots', size='xl', color='#32D74B').classes('mt-8 hidden')
                        ai_result = ui.markdown('').classes('text-sm md:text-base text-gray-300 leading-relaxed text-left mt-6 max-w-2xl hidden bg-[#0B0E14]/80 backdrop-blur-md p-6 md:p-8 rounded-[24px] border border-[#32D74B]/30 shadow-[0_0_30px_rgba(50,215,75,0.1)] custom-scrollbar overflow-y-auto max-h-[300px] w-full')
                        
                        async def generate_doctor():
                            # ?? เช็คสิทธิ์ PRO และ Admin
                            tid = app.storage.user.get('telegram_id')
                            user_info = get_user_by_telegram(tid) if tid else {}
                            role = str(user_info.get('role', 'free')).lower()
                            
                            if role not in ['pro', 'admin']:
                                ui.notify('?? ฟีเจอร์ Port Doctor สงวนสิทธิ์สำหรับแพ็กเกจ PRO เท่านั้น!', type='warning')
                                return
                                
                            btn_ai.set_visibility(False)
                            ai_loading.classes(remove='hidden')
                            
                            # เตรียมข้อมูลพอร์ตส่งให้คุณหมอ
                            port_str = ", ".join([f"{a['ticker']}: ${a['value']:,.0f}" for a in assets_data])
                            from services.gemini_ai import generate_port_doctor_diagnosis
                            res = await run.io_bound(generate_port_doctor_diagnosis, port_str)
                            
                            ai_loading.classes(add='hidden')
                            ai_result.classes(remove='hidden')
                            ai_result.set_content(res)
                            
                        btn_ai = ui.button('เริ่มสแกนสุขภาพพอร์ต', icon='vaccines', on_click=generate_doctor).classes('mt-8 bg-[#1C2128] border border-[#32D74B]/50 text-[#32D74B] font-black py-4 px-10 rounded-full shadow-[0_0_30px_rgba(50,215,75,0.2)] hover:bg-[#32D74B] hover:text-black transition-all text-lg')
                
                elif mode == 'Sector Flow':
                    window_map = {'5D': '5d', '1M': '1mo', '3M': '3mo', '6M': '6mo'}
                    rotation_data = await run.io_bound(get_real_sector_rotation, window_map.get(sector_window.value, '1mo'))
                    ui.label(f'REAL SECTOR FLOW ({sector_window.value})').classes('text-lg font-black text-white tracking-widest absolute top-6 left-6 md:left-8 z-10')

                    if not rotation_data:
                        with ui.column().classes('absolute-center items-center gap-3'):
                            ui.icon('stacked_bar_chart', size='4xl').classes('text-gray-600')
                            ui.label('Insufficient data for sector flow').classes('text-gray-400 font-bold')
                    else:
                        s_names = [f"{item.get('rank', 0)}. {item['sector']}" for item in rotation_data]
                        s_values = [item['flow_pct'] for item in rotation_data]
                        updated_at = str(rotation_data[0].get('updated_at', '')).replace('T', ' ')[:19]
                        ui.label(f'Data Source: Yahoo Finance • Updated: {updated_at}').classes('absolute top-14 left-6 text-[10px] text-gray-400 z-10')

                        ui.echart({
                            'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}, 'backgroundColor': '#12161E', 'valueFormatter': "(value) => value + '%'"},
                            'grid': {'left': '34%', 'right': '8%', 'bottom': '8%', 'top': '20%'},
                            'xAxis': {'type': 'value', 'splitLine': {'lineStyle': {'color': '#1C2128', 'type': 'dashed'}}},
                            'yAxis': {'type': 'category', 'data': s_names, 'axisLine': {'show': False}, 'axisLabel': {'color': '#fff', 'fontWeight': 'bold'}},
                            'series': [{'name': 'Return (%)', 'type': 'bar', 'data': [{'value': v, 'itemStyle': {'color': '#32D74B' if v >= 0 else '#FF453A', 'borderRadius': 5}} for v in s_values]}]
                        }).classes('w-full h-full p-4 mt-6')

            with list_card:
                with ui.row().classes('w-full bg-[#0B0E14] p-5 md:p-6 border-b border-white/5 text-xs text-gray-500 font-bold tracking-widest justify-between shrink-0'):
                    ui.label('ASSET')
                    ui.label('VALUE')

                with ui.column().classes('w-full p-3 md:p-4 overflow-y-auto custom-scrollbar gap-2 flex-1'):
                    if mode == 'Sector Flow':
                        window_map = {'5D': '5d', '1M': '1mo', '3M': '3mo', '6M': '6mo'}
                        rotation_data = await run.io_bound(get_real_sector_rotation, window_map.get(sector_window.value, '1mo'))
                        for item in rotation_data:
                            flow = float(item.get('flow_pct', 0))
                            with ui.row().classes('w-full justify-between items-center p-4 bg-white/5 rounded-2xl border border-white/10'):
                                with ui.column().classes('gap-0'):
                                    ui.label(f"{item.get('rank', 0)}. {item.get('sector', 'N/A')}").classes('font-black text-white tracking-wide text-base md:text-lg')
                                    ui.label(item.get('symbol', '')).classes('text-[10px] text-gray-400 font-bold')
                                    spark = item.get('sparkline', [])
                                    if spark:
                                        ui.echart({
                                            'xAxis': {'type': 'category', 'show': False},
                                            'yAxis': {'type': 'value', 'show': False},
                                            'grid': {'left': 0, 'right': 0, 'top': 6, 'bottom': 6},
                                            'series': [{
                                                'type': 'line',
                                                'data': spark,
                                                'smooth': True,
                                                'showSymbol': False,
                                                'lineStyle': {'width': 2, 'color': '#32D74B' if flow >= 0 else '#FF453A'},
                                                'areaStyle': {'opacity': 0.12, 'color': '#32D74B' if flow >= 0 else '#FF453A'},
                                            }]
                                        }).classes('w-28 h-12 mt-1')
                                ui.label(f"{flow:+.2f}%").classes('font-black text-sm px-3 py-1 rounded-md').style(f"background:{'#32D74B22' if flow >= 0 else '#FF453A22'}; color:{'#32D74B' if flow >= 0 else '#FF453A'};")
                    else:
                        for a in assets_data:
                            with ui.row().classes('w-full justify-between items-center p-4 bg-white/5 hover:bg-[#1C2128] rounded-2xl transition-colors border border-transparent hover:border-white/10 group cursor-pointer'):
                                with ui.column().classes('gap-0'):
                                    ui.label(a['ticker']).classes('font-black text-white tracking-wide text-lg md:text-xl')
                                
                                pct = (a['value'] / total_value) * 100 if total_value > 0 else 0
                                with ui.row().classes('gap-3 md:gap-4 text-sm items-center'):
                                    ui.label(f"${a['value']:,.0f}").classes('text-gray-300 font-bold')
                                    ui.label(f"{pct:.1f}%").classes('text-[#32D74B] font-black w-14 text-right bg-[#32D74B]/10 py-1 rounded-md')

        # ให้มันเรียกฟังก์ชันตรงๆ ไปเลย
        mode_toggle.on('update:model-value', update_view)
        growth_period.on('update:model-value', update_view)
        growth_benchmark.on('update:model-value', update_view)
        sector_window.on('update:model-value', update_view)
        
        async def set_group(g):
            current_group['val'] = g
            await update_view()

        # เมนูเลือกกลุ่ม (ALL / DCA / DIV / TRADING)
        with ui.row().classes('bg-[#0B0E14]/80 backdrop-blur-md rounded-full p-1.5 border border-white/5 mt-4 md:mt-2 gap-1 shadow-lg mx-auto md:mx-0'):
            for g in ['ALL', 'DCA', 'DIV', 'TRADING']:
                btn = ui.button(g, on_click=lambda g=g: set_group(g)).props('unelevated rounded size=sm').classes('font-bold tracking-widest px-4 py-1.5 transition-all')
                if current_group['val'] == g:
                    btn.classes('bg-[#D0FD3E] text-black shadow-md')
                else:
                    btn.classes('bg-transparent text-gray-500 hover:text-white hover:bg-white/5')
        
        await update_view()
# ==========================================
# 4. หน้าปฏิทินปันผล (DIVIDEND & DRIP) - Premium UI
# ==========================================
@ui.page('/dividend')
@standard_page_frame
async def dividend_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker()

    user_id = app.storage.user.get('user_id')
    raw_portfolio = await run.io_bound(get_portfolio, user_id) if user_id else []

    with ui.column().classes('w-full max-w-7xl mx-auto p-4 md:p-8 gap-6 pt-[110px] md:pt-[120px]'):
        with ui.row().classes('w-full justify-between items-end flex flex-col md:flex-row gap-2'):
            with ui.column().classes('gap-1'):
                ui.label('DIVIDEND & DRIP SIMULATOR').classes('text-2xl md:text-3xl font-black text-white tracking-widest uppercase')
                ui.label('เลือกได้ 2 โหมด: Quick DRIP (ง่าย) และ Real Backtest (ข้อมูลจริง)').classes('text-xs md:text-sm text-gray-400')

        mode_tabs = ui.toggle(['Quick DRIP', 'Real Backtest'], value='Quick DRIP').classes('bg-[#12161E]/80 backdrop-blur-xl text-gray-400 rounded-full p-1 border border-white/5 shadow-lg font-bold').props('unelevated dark color=positive text-color=black')

        # Inputs
        with ui.row().classes('w-full gap-3 flex-wrap'):
            initial_input = ui.number('Initial Capital ($)', value=10000, min=0, step=100).props('outlined dense').classes('w-44')
            monthly_input = ui.number('Monthly Contribution ($)', value=0, min=0, step=50).props('outlined dense').classes('w-48')
            div_yield_input = ui.number('Dividend Yield %', value=3, min=0, step=0.1).props('outlined dense').classes('w-40')
            growth_input = ui.number('Price Growth %', value=5, step=0.1).props('outlined dense').classes('w-40')
            years_input = ui.select(options=[5, 10, 15, 20, 30, 50], value=10, label='Years').props('outlined dense').classes('w-28')
            tax_input = ui.number('Tax %', value=0, min=0, max=100, step=0.1).props('outlined dense').classes('w-28')
            ticker_input = ui.input('Ticker (Real Backtest)').props('outlined dense').classes('w-44').style('text-transform: uppercase;')
            ticker_input.set_value('KO')
            run_btn = ui.button('RUN SIMULATION', icon='play_arrow').classes('bg-[#20D6A1] text-black font-black rounded-xl px-5 py-3')

        summary_row = ui.row().classes('w-full gap-4 flex-col md:flex-row')
        chart_wrap = ui.column().classes('w-full')
        table_wrap = ui.column().classes('w-full')

        def render_summary(initial_capital: float, final_value: float, profit: float):
            summary_row.clear()
            with summary_row:
                for title, val, color in [
                    ('INITIAL CAPITAL', initial_capital, '#ffffff'),
                    ('FUTURE VALUE', final_value, '#20D6A1'),
                    ('COMPOUND PROFIT', profit, '#D0FD3E' if profit >= 0 else '#FF5E6C'),
                ]:
                    with ui.column().classes('flex-1 bg-[#12161E]/80 backdrop-blur-xl p-5 rounded-[20px] border border-white/5'):
                        ui.label(title).classes('text-[10px] text-gray-500 font-black tracking-widest uppercase')
                        ui.label(f'${val:,.2f}').classes('text-2xl md:text-3xl font-black').style(f'color:{color};')

        def render_chart(labels, series_a, series_b=None, name_a='Portfolio', name_b='Benchmark'):
            chart_wrap.clear()
            with chart_wrap:
                with ui.card().classes('w-full bg-[#12161E]/60 backdrop-blur-xl border border-white/5 p-4 md:p-6 rounded-[26px] h-[360px] md:h-[460px] shadow-2xl'):
                    series = [{'name': name_a, 'type': 'line', 'data': series_a, 'smooth': True, 'showSymbol': False, 'lineStyle': {'width': 3, 'color': '#20D6A1'}}]
                    legend = [name_a]
                    if series_b is not None:
                        series.append({'name': name_b, 'type': 'line', 'data': series_b, 'smooth': True, 'showSymbol': False, 'lineStyle': {'width': 2, 'color': '#39C8FF', 'type': 'dashed'}})
                        legend.append(name_b)
                    ui.echart({
                        'tooltip': {'trigger': 'axis', 'backgroundColor': '#12161E', 'textStyle': {'color': '#fff'}},
                        'legend': {'data': legend, 'textStyle': {'color': '#8B949E'}},
                        'grid': {'left': '6%', 'right': '6%', 'bottom': '8%', 'top': '14%', 'containLabel': True},
                        'xAxis': {'type': 'category', 'data': labels, 'axisLine': {'lineStyle': {'color': '#8B949E'}}},
                        'yAxis': {'type': 'value', 'axisLabel': {'formatter': '${value}'}, 'splitLine': {'lineStyle': {'color': '#1C2128', 'type': 'dashed'}}},
                        'series': series,
                    }).classes('w-full h-full')

        def render_table(columns, rows):
            table_wrap.clear()
            with table_wrap:
                ui.table(columns=columns, rows=rows, row_key='year').classes('w-full ax-card').props('dense rows-per-page-options=[10,20,50]')

        async def run_simulation(e=None):
            mode = mode_tabs.value
            is_quick = mode == 'Quick DRIP'
            monthly_input.set_visibility(is_quick)
            div_yield_input.set_visibility(is_quick)
            growth_input.set_visibility(is_quick)
            tax_input.set_visibility(is_quick)
            ticker_input.set_visibility(not is_quick)
            initial = float(initial_input.value or 0)
            years = int(years_input.value or 10)

            if is_quick:
                result = await run.io_bound(
                    get_drip_projection,
                    initial,
                    float(monthly_input.value or 0),
                    float(div_yield_input.value or 0),
                    float(growth_input.value or 0),
                    years,
                    float(tax_input.value or 0),
                )
                summary = result['summary']
                render_summary(summary['initial_capital'], summary['future_value'], summary['compound_profit'])
                render_chart(result['labels'], result['values'], None, 'Quick DRIP')
                render_table(
                    [
                        {'name': 'year', 'label': 'Year', 'field': 'year'},
                        {'name': 'start_capital', 'label': 'Start', 'field': 'start_capital'},
                        {'name': 'contribution', 'label': 'Contribution', 'field': 'contribution'},
                        {'name': 'net_dividend', 'label': 'Net Dividend', 'field': 'net_dividend'},
                        {'name': 'growth_gain', 'label': 'Growth Gain', 'field': 'growth_gain'},
                        {'name': 'end_value', 'label': 'End Value', 'field': 'end_value'},
                    ],
                    result['rows'],
                )
                ui.notify(f"Assumptions: {result.get('assumptions', '-')}", type='info')
                return

            symbol = str(ticker_input.value or '').strip().upper()
            if not symbol:
                ui.notify('กรอก ticker สำหรับ Real Backtest', type='warning')
                return

            backtest = await run.io_bound(get_real_drip_backtest, symbol, years, initial if initial > 0 else 10000.0)
            if not backtest:
                summary_row.clear()
                chart_wrap.clear()
                table_wrap.clear()
                with chart_wrap:
                    with ui.column().classes('w-full ax-card p-8 items-center text-center gap-2'):
                        ui.icon('warning', size='3rem').classes('text-[#FF5E6C]')
                        ui.label('insufficient data').classes('text-lg font-black text-white')
                        ui.label('ไม่สามารถโหลดข้อมูลจริงสำหรับ ticker/ช่วงเวลานี้').classes('text-sm text-gray-400')
                return

            s = backtest['summary']
            render_summary(s['initial_capital'], s['final_drip'], s['final_drip'] - s['initial_capital'])
            render_chart(backtest['labels'], backtest['drip_values'], backtest['price_only_values'], f"{symbol} DRIP", f"{symbol} Price Only")
            render_table(
                [
                    {'name': 'year', 'label': 'Year', 'field': 'year'},
                    {'name': 'price', 'label': 'Price', 'field': 'price'},
                    {'name': 'price_only_value', 'label': 'Price Only', 'field': 'price_only_value'},
                    {'name': 'drip_value', 'label': 'DRIP Value', 'field': 'drip_value'},
                    {'name': 'dividend_ps', 'label': 'Dividend/Share', 'field': 'dividend_ps'},
                    {'name': 'shares', 'label': 'Shares', 'field': 'shares'},
                ],
                backtest['rows'],
            )
            ui.notify(
                f"Total {s['total_return_pct']:+.2f}% | Price {s['price_return_pct']:+.2f}% | Dividend {s['dividend_return_pct']:+.2f}%",
                type='positive'
            )

        run_btn.on_click(run_simulation)
        mode_tabs.on('update:model-value', run_simulation)
        await run_simulation()
# ==========================================
# 5. หน้าแผนที่ความร้อน (PORTFOLIO HEATMAP) - Premium UI
# ==========================================
@ui.page('/heatmap')
@standard_page_frame
async def heatmap_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker() 

    user_id = app.storage.user.get('user_id')
    raw_portfolio = await run.io_bound(get_portfolio, user_id) if user_id else []

    with ui.column().classes('w-full max-w-7xl mx-auto p-4 md:p-8 gap-6 pt-[110px] md:pt-[120px]'):
        # Header
        with ui.row().classes('w-full justify-between items-end flex flex-col md:flex-row gap-2'):
            with ui.column().classes('gap-1'):
                ui.label('PORTFOLIO HEATMAP').classes('text-2xl md:text-3xl font-black text-white tracking-widest uppercase')
                ui.label('แผนภาพความร้อนแสดงสัดส่วนและผลกำไรของสินทรัพย์ในพอร์ต').classes('text-xs md:text-sm text-gray-400')
        
        if not raw_portfolio:
            with ui.column().classes('w-full items-center justify-center p-12 bg-[#12161E]/50 backdrop-blur-md rounded-[32px] border border-white/5 border-dashed mt-4'):
                ui.icon('grid_view', size='4xl').classes('text-gray-600 mb-4')
                ui.label('ยังไม่มีข้อมูลหุ้นในพอร์ต').classes('text-lg text-gray-400 font-bold')
                ui.label('กรุณาเพิ่มหุ้นเพื่อดู Heatmap').classes('text-sm text-gray-500')
            return

        # ==========================================
        # ?? โค้ดชุดใหม่: Heatmap (ไร้ภาษาโค้ด) + ตาราง Breakdown ด้านล่าง
        # ==========================================
        treemap_data = []
        for item in raw_portfolio:
            ticker = item['ticker']
            shares = float(item['shares'])
            avg_cost = float(item['avg_cost'])
            
            # ดึงราคาแบบ Real-time
            live_price = await run.io_bound(get_live_price, ticker)
            
            current_value = shares * live_price
            profit = current_value - (shares * avg_cost)
            profit_pct = (profit / (shares * avg_cost) * 100) if (shares * avg_cost) > 0 else 0
            
            # โทนสีไล่เฉดตามความแรง
            if profit_pct >= 5: color = '#22C55E'    
            elif profit_pct > 0: color = '#166534'   
            elif profit_pct == 0: color = '#475569'  
            elif profit_pct > -5: color = '#991B1B'  
            else: color = '#EF4444'                  
            
            treemap_data.append({
                'name': f"{ticker}\n{profit_pct:+.2f}%", # ใส่ชื่อและ % คู่กันไปเลย
                'value': current_value,                 
                'profit_pct_val': profit_pct, # เก็บค่าตัวเลขไว้ใช้เรียงในตาราง
                'itemStyle': {'color': color}           
            })
            
        # เรียงลำดับจากมูลค่ามากไปน้อยสำหรับโชว์ในตาราง
        treemap_data.sort(key=lambda x: x['value'], reverse=True)

        # ?? สร้างกล่องคลุมทั้งหมด (เพื่อสั่งเบลอทีเดียวถ้าเป็น Free)
        with ui.column().classes('w-full relative'):
            
            # โซนเนื้อหา (กราฟ Heatmap + ตาราง)
            with ui.column().classes('w-full gap-8') as premium_content:
                
                # ?? 1. กราฟ Heatmap
                with ui.card().classes('w-full bg-[#12161E]/80 backdrop-blur-2xl border border-white/10 p-4 md:p-6 rounded-[32px] h-[400px] md:h-[600px] shadow-[0_0_40px_rgba(0,0,0,0.5)] relative overflow-hidden'):
                    ui.element('div').classes('absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-[#D0FD3E]/5 rounded-full blur-[120px] pointer-events-none')
                    
                    chart = ui.echart({
                        'tooltip': {
                            'formatter': '<b>{b}</b><br/>Total Value: ${c}',
                            'backgroundColor': 'rgba(11, 14, 20, 0.95)',
                            'borderColor': '#2B3139',
                            'borderWidth': 1,
                            'textStyle': {'color': '#fff'}
                        },
                        'series': [{
                            'type': 'treemap',
                            'width': '100%', 'height': '100%',
                            'roam': False,
                            'nodeClick': False,
                            'breadcrumb': {'show': False},
                            'itemStyle': {
                                'borderColor': '#0B0E14', 
                                'borderWidth': 3, 
                                'gapWidth': 2, 
                                'borderRadius': 4 
                            },
                            'label': {
                                'show': True,
                                'position': 'inside',
                                'formatter': '{b}',
                                'color': '#ffffff',
                                'fontSize': 18,
                                'fontWeight': 'bold',
                                'textShadowColor': 'rgba(0,0,0,0.8)',
                                'textShadowBlur': 4
                            },
                            'data': treemap_data
                        }]
                    }).classes('w-full h-full z-10')

                # ?? 2. ตาราง Breakdown
                ui.label('ASSET BREAKDOWN').classes('text-xl font-black text-white tracking-widest mt-4 -mb-4')
                with ui.column().classes('w-full bg-[#12161E]/60 backdrop-blur-xl rounded-[32px] border border-white/5 overflow-hidden shadow-2xl gap-0'):
                    with ui.row().classes('w-full bg-[#0B0E14] p-5 md:p-6 border-b border-white/5 text-gray-500 text-[10px] md:text-xs font-bold uppercase tracking-widest items-center'):
                        ui.label('ASSET').classes('w-24 md:w-32 pl-2 md:pl-4')
                        ui.label('TOTAL VALUE').classes('flex-1 text-right')
                        ui.label('PROFIT/LOSS').classes('w-24 md:w-32 text-right pr-2 md:pr-6')
                    
                    for item in treemap_data:
                        # ตัดเอาเฉพาะชื่อหุ้นมาโชว์ (ไม่เอา % ที่ติดมา)
                        ticker_display = item['name'].split('\n')[0]
                        val = item['value']
                        pct = item['profit_pct_val']
                        
                        p_color = '#32D74B' if pct >= 0 else '#FF453A'
                        p_sign = '+' if pct >= 0 else ''
                        
                        with ui.row().classes('w-full p-4 md:p-6 border-b border-white/5 items-center hover:bg-[#1C2128]/80 transition-colors text-sm group cursor-default'):
                            ui.label(ticker_display).classes('w-24 md:w-32 pl-2 md:pl-4 font-black text-white text-lg tracking-wide')
                            ui.label(f"${val:,.2f}").classes('flex-1 text-right text-white font-bold text-lg')
                            ui.label(f"{p_sign}{pct:.2f}%").classes('w-24 md:w-32 text-right font-black pr-2 md:pr-6').style(f'color: {p_color}')

            # ?? ล็อคสิทธิ์ (ดึง Database ตรงๆ)
            tid = app.storage.user.get('telegram_id')
            user_info = get_user_by_telegram(tid) if tid else {}
            role = str(user_info.get('role', 'free')).lower()
            
            if role not in ['vip', 'pro', 'admin']:
                # สั่งเบลอทั้งกราฟและตารางพร้อมกัน
                premium_content.classes('blur-md pointer-events-none opacity-40')
                with ui.column().classes('absolute top-[30%] left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 items-center text-center bg-[#0B0E14]/90 p-8 rounded-[32px] border border-[#FCD535]/30 shadow-2xl backdrop-blur-md w-full max-w-sm'):
                    ui.icon('lock', size='4xl').classes('text-[#FCD535] mb-2')
                    ui.label('PREMIUM FEATURE').classes('text-xl font-black text-[#FCD535] tracking-widest')
                    ui.label('แผนภาพความร้อนและตารางเชิงลึก สงวนสิทธิ์สำหรับแพ็กเกจ VIP และ PRO').classes('text-gray-300 mb-6 text-sm')
                    ui.button('UPGRADE NOW', on_click=lambda: ui.navigate.to('/payment')).classes('w-full bg-[#FCD535] text-black font-black py-3 rounded-xl hover:scale-105 transition-transform shadow-[0_0_20px_rgba(252,213,53,0.3)]')
# 6. 2-Stock Return Simulator (Premium)
# ==========================================
@ui.page('/sp500')
@standard_page_frame
async def sp500_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker()

    with ui.column().classes('w-full max-w-7xl mx-auto p-4 md:p-8 gap-6 pt-[110px] md:pt-[120px]'):
        with ui.row().classes('w-full justify-between items-end flex flex-col md:flex-row gap-2'):
            with ui.column().classes('gap-1'):
                ui.label('2-STOCK RETURN SIMULATOR').classes('text-2xl md:text-3xl font-black text-white tracking-widest uppercase')
                ui.label('เทียบผลตอบแทนหุ้น 2 ตัวแบบเข้าใจง่าย (5/10/15/20/30/50 ปี)').classes('text-xs md:text-sm text-gray-400')
            ui.label('Backtest View').classes('text-[10px] md:text-xs text-[#D0FD3E] font-bold bg-[#D0FD3E]/10 px-3 py-1 rounded-full border border-[#D0FD3E]/30 tracking-widest uppercase')

        with ui.row().classes('w-full gap-3 flex-col md:flex-row'):
            ticker_a_input = ui.input('Stock A').props('outlined dense').classes('flex-1').style('text-transform: uppercase;')
            ticker_a_input.set_value('AAPL')
            ticker_b_input = ui.input('Stock B').props('outlined dense').classes('flex-1').style('text-transform: uppercase;')
            ticker_b_input.set_value('MSFT')
            year_select = ui.select(options=[5, 10, 15, 20, 30, 50], value=10, label='Horizon (Years)').props('outlined dense').classes('w-full md:w-48')
            compare_btn = ui.button('COMPARE', icon='insights').classes('bg-[#20D6A1] text-black font-black rounded-xl px-5 py-3')

        ui.label('สมมติลงทุนเริ่มต้น $10,000 เท่ากันทั้งสองตัว และแสดงกราฟมูลค่าเงินลงทุน').classes('text-xs text-gray-500 -mt-1')

        result_section = ui.column().classes('w-full gap-5')

        def sample_rows(data: dict):
            rows = []
            total = len(data['labels'])
            step = max(1, total // 180)
            for i in range(0, total, step):
                rows.append({
                    'date': data['labels'][i],
                    'a_close': data['a_close'][i],
                    'b_close': data['b_close'][i],
                    'a_return_pct': data['a_return_pct'][i],
                    'b_return_pct': data['b_return_pct'][i],
                    'a_value': data['a_value'][i],
                    'b_value': data['b_value'][i],
                })
            return rows

        def render_results(data: dict):
            result_section.clear()
            summary = data['summary']
            a_ticker = data['ticker_a']
            b_ticker = data['ticker_b']

            winner = a_ticker if summary['a_total_return'] >= summary['b_total_return'] else b_ticker
            spread = round(abs(summary['a_total_return'] - summary['b_total_return']), 2)

            with result_section:
                with ui.row().classes('w-full gap-4 md:gap-6 items-stretch flex-col md:flex-row'):
                    with ui.column().classes('flex-1 bg-[#12161E]/80 backdrop-blur-xl p-5 md:p-6 rounded-[24px] items-center border border-white/5 shadow-lg'):
                        ui.label(f'{a_ticker} RETURN').classes('text-[10px] md:text-xs text-gray-500 font-bold tracking-widest uppercase')
                        ui.label(f"{summary['a_total_return']:+.2f}%").classes('text-3xl md:text-4xl font-black text-white mt-1')
                        ui.label(f"CAGR {summary['a_cagr']:.2f}% • MDD {summary['a_max_drawdown']:.2f}%").classes('text-xs text-gray-400')
                    with ui.column().classes('flex-1 bg-[#12161E]/80 backdrop-blur-xl p-5 md:p-6 rounded-[24px] items-center border border-white/5 shadow-lg'):
                        ui.label(f'{b_ticker} RETURN').classes('text-[10px] md:text-xs text-gray-500 font-bold tracking-widest uppercase')
                        ui.label(f"{summary['b_total_return']:+.2f}%").classes('text-3xl md:text-4xl font-black text-white mt-1')
                        ui.label(f"CAGR {summary['b_cagr']:.2f}% • MDD {summary['b_max_drawdown']:.2f}%").classes('text-xs text-gray-400')
                    with ui.column().classes('flex-1 bg-[#12161E]/80 backdrop-blur-xl p-5 md:p-6 rounded-[24px] items-center border border-white/5 shadow-lg'):
                        ui.label('WINNER').classes('text-[10px] md:text-xs text-gray-500 font-bold tracking-widest uppercase')
                        ui.label(winner).classes('text-3xl md:text-4xl font-black text-[#20D6A1] mt-1')
                        ui.label(f'Outperformed by {spread:.2f}%').classes('text-xs text-gray-400')

                with ui.card().classes('w-full bg-[#12161E]/60 backdrop-blur-xl border border-white/5 p-4 md:p-6 rounded-[32px] h-[420px] md:h-[520px] shadow-2xl'):
                    ui.echart({
                        'tooltip': {'trigger': 'axis', 'backgroundColor': '#12161E', 'borderColor': '#20D6A1', 'textStyle': {'color': '#fff'}},
                        'legend': {'data': [a_ticker, b_ticker], 'textStyle': {'color': '#8B949E', 'fontWeight': 'bold'}, 'top': 0},
                        'grid': {'left': '5%', 'right': '5%', 'bottom': '5%', 'top': '15%', 'containLabel': True},
                        'xAxis': {'type': 'category', 'data': data['labels'], 'axisLine': {'lineStyle': {'color': '#8B949E'}}},
                        'yAxis': {'type': 'value', 'axisLabel': {'formatter': '${value}'}, 'splitLine': {'lineStyle': {'color': '#1C2128', 'type': 'dashed'}}},
                        'series': [
                            {'name': a_ticker, 'type': 'line', 'data': data['a_value'], 'smooth': True, 'showSymbol': False, 'lineStyle': {'width': 3, 'color': '#20D6A1'}},
                            {'name': b_ticker, 'type': 'line', 'data': data['b_value'], 'smooth': True, 'showSymbol': False, 'lineStyle': {'width': 3, 'color': '#39C8FF'}},
                        ]
                    }).classes('w-full h-full')

                ui.label('Comparison Table').classes('text-lg md:text-xl font-black text-white tracking-widest uppercase')
                ui.table(
                    columns=[
                        {'name': 'date', 'label': 'Date', 'field': 'date'},
                        {'name': 'a_close', 'label': f'{a_ticker} Close', 'field': 'a_close'},
                        {'name': 'b_close', 'label': f'{b_ticker} Close', 'field': 'b_close'},
                        {'name': 'a_return_pct', 'label': f'{a_ticker} Return %', 'field': 'a_return_pct'},
                        {'name': 'b_return_pct', 'label': f'{b_ticker} Return %', 'field': 'b_return_pct'},
                        {'name': 'a_value', 'label': f'{a_ticker} Value ($)', 'field': 'a_value'},
                        {'name': 'b_value', 'label': f'{b_ticker} Value ($)', 'field': 'b_value'},
                    ],
                    rows=sample_rows(data),
                    row_key='date'
                ).classes('w-full ax-card').props('dense rows-per-page-options=[15,30,50]')

        async def compare():
            symbol_a = str(ticker_a_input.value or '').strip().upper()
            symbol_b = str(ticker_b_input.value or '').strip().upper()
            years = int(year_select.value or 10)
            if not symbol_a or not symbol_b:
                ui.notify('กรอกหุ้นให้ครบทั้ง 2 ตัว', type='warning')
                return

            compare_btn.disable()
            result_section.clear()
            with result_section:
                with ui.column().classes('w-full ax-card p-8 items-center gap-3'):
                    ui.spinner(size='lg')
                    ui.label('Loading historical data...').classes('text-sm text-gray-300')

            data = await run.io_bound(get_stock_duel_data, symbol_a, symbol_b, years, 10000.0)
            compare_btn.enable()
            if not data:
                result_section.clear()
                with result_section:
                    with ui.column().classes('w-full ax-card p-8 items-center text-center gap-2'):
                        ui.icon('warning', size='3rem').classes('text-[#FF5E6C]')
                        ui.label('โหลดข้อมูลไม่สำเร็จ').classes('text-lg font-black text-white')
                        ui.label('เช็กสัญลักษณ์หุ้นหรือเครือข่าย แล้วลองอีกครั้ง').classes('text-sm text-gray-400')
                return

            render_results(data)

        compare_btn.on_click(compare)
        await compare()

# ==========================================
# 7. AI STOCK MATCHMAKER (TINDER STYLE)
# ==========================================
@ui.page('/matchmaker')
@standard_page_frame
async def matchmaker_page():
    create_ticker()

    tid = app.storage.user.get('telegram_id')
    user_info = await run.io_bound(get_user_by_telegram, tid) if tid else {}
    role = str(user_info.get('role', 'free')).lower()
    is_pro = role in ['pro', 'vip', 'admin']

    with ui.column().classes('ax-page-shell w-full max-w-5xl mx-auto p-4 md:p-8 gap-5 pt-[110px] md:pt-[120px]'):
        with ui.row().classes('w-full items-end justify-between flex-col md:flex-row gap-3'):
            with ui.column().classes('gap-1'):
                ui.label('AI STOCK MATCHMAKER').classes('text-2xl md:text-4xl font-black text-white tracking-widest uppercase')
                ui.label('ปัดซ้ายเพื่อข้าม • ปัดขวาเพื่อเพิ่มเข้า Watchlist/Alerts').classes('text-xs md:text-sm text-gray-400')
            if not is_pro:
                ui.button('UPGRADE TO PRO', on_click=lambda: ui.navigate.to('/payment')).classes('bg-[#FCD535] text-black font-black rounded-full px-6 py-2 text-xs')

        if not is_pro:
            with ui.column().classes('w-full ax-card p-8 items-center text-center gap-3'):
                ui.icon('lock', size='3rem').classes('text-[#FCD535]')
                ui.label('Feature locked for PRO/VIP').classes('text-lg font-black text-white')
                ui.label('ปลดล็อก AI Matchmaker เพื่อรับหุ้นที่ AI คัดมาและปัดเก็บได้ทันที').classes('text-sm text-gray-400')
            return

        universe = get_matchmaker_universe()
        random.shuffle(universe)
        queue = universe[:min(30, len(universe))]
        state = {'index': 0, 'liked': 0, 'skipped': 0, 'card_cache': {}}

        with ui.row().classes('w-full gap-2'):
            ui.label(f'CARDS THIS ROUND: {len(queue)}').classes('text-xs font-black px-3 py-1 rounded-full bg-[#39C8FF]/15 text-[#39C8FF] border border-[#39C8FF]/30')
            liked_badge = ui.label('LIKED: 0').classes('text-xs font-black px-3 py-1 rounded-full bg-[#20D6A1]/15 text-[#20D6A1] border border-[#20D6A1]/30')
            skipped_badge = ui.label('SKIPPED: 0').classes('text-xs font-black px-3 py-1 rounded-full bg-white/5 text-gray-300 border border-white/10')

        card_container = ui.column().classes('w-full')

        async def get_card_data(symbol: str):
            if symbol in state['card_cache']:
                return state['card_cache'][symbol]
            price = await run.io_bound(get_live_price, symbol)
            spark, _ = await run.io_bound(get_sparkline_data, symbol)
            trend_up = bool(spark and len(spark) > 1 and spark[-1] >= spark[0])
            data = {'price': float(price or 0), 'spark': spark or [], 'trend_up': trend_up}
            state['card_cache'][symbol] = data
            return data

        async def render_card():
            card_container.clear()
            with card_container:
                idx = state['index']
                if idx >= len(queue):
                    with ui.column().classes('w-full ax-card p-10 items-center text-center gap-3'):
                        ui.icon('celebration', size='3rem').classes('text-[#20D6A1]')
                        ui.label('ครบทุกการ์ดแล้ว').classes('text-2xl font-black text-white')
                        ui.label('กดรีโหลดเพื่อสุ่มรอบใหม่').classes('text-sm text-gray-400')
                        ui.button('RELOAD CARDS', on_click=lambda: ui.navigate.reload()).classes('bg-[#20D6A1] text-black font-black rounded-full px-6 py-2 text-xs')
                    return

                ticker = queue[idx]
                card = await get_card_data(ticker)
                price = card['price']
                spark = card['spark']
                trend_up = card['trend_up']
                quick_pitch = (
                    f"- โครงสร้างราคา {'แข็งแรง' if trend_up else 'ยังแกว่ง'}\n"
                    f"- Risk: ตั้ง Stop-loss ให้ชัดก่อนตัดสินใจ"
                )

                with ui.column().classes('w-full max-w-2xl mx-auto bg-gradient-to-b from-[#0F1E26] to-[#09131A] border border-[#20D6A1]/25 rounded-[28px] p-6 md:p-8 shadow-[0_15px_40px_rgba(0,0,0,0.45)] gap-4 ax-neon-ring ax-card-hover'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label(ticker).classes('text-4xl md:text-5xl font-black text-white tracking-wider')
                        trend_color = '#20D6A1' if trend_up else '#FF5E6C'
                        ui.label('UPTREND' if trend_up else 'RISKY').classes('text-[10px] font-black tracking-widest px-3 py-1 rounded-full border').style(f'color:{trend_color}; border-color:{trend_color}55; background:{trend_color}18;')
                    ui.label(f'Price: ${price:,.2f}').classes('text-lg font-black text-[#39C8FF]')
                    pitch_md = ui.markdown(quick_pitch).classes('text-sm text-gray-200 leading-relaxed')

                    if spark:
                        norm = normalize_series(spark)
                        ui.echart({
                            'xAxis': {'type': 'category', 'show': False},
                            'yAxis': {'type': 'value', 'show': False},
                            'grid': {'left': 0, 'right': 0, 'top': 8, 'bottom': 8},
                            'series': [{
                                'type': 'line',
                                'data': norm,
                                'smooth': True,
                                'showSymbol': False,
                                'lineStyle': {'width': 3, 'color': '#20D6A1' if trend_up else '#FF5E6C'},
                                'areaStyle': {'opacity': 0.16, 'color': '#20D6A1' if trend_up else '#FF5E6C'},
                            }]
                        }).classes('w-full h-24')

                    with ui.row().classes('w-full gap-3 mt-2'):
                        async def swipe_left():
                            state['skipped'] += 1
                            skipped_badge.set_text(f"SKIPPED: {state['skipped']}")
                            state['index'] += 1
                            await render_card()

                        async def swipe_right():
                            user_id = app.storage.user.get('user_id')
                            target = float(price) * 1.08
                            if user_id and target > 0:
                                await run.io_bound(set_user_price_alert, str(user_id), ticker, target, '>')
                            state['liked'] += 1
                            liked_badge.set_text(f"LIKED: {state['liked']}")
                            ui.notify(f'Added {ticker} to watch alerts at ${target:,.2f}', type='positive')
                            state['index'] += 1
                            await render_card()

                        ui.button('SWIPE LEFT', icon='close', on_click=swipe_left).classes('flex-1 bg-white/10 text-gray-200 border border-white/15 rounded-xl py-3 font-black')
                        ui.button('SWIPE RIGHT', icon='favorite', on_click=swipe_right).classes('flex-1 bg-[#20D6A1] text-black rounded-xl py-3 font-black')

                    async def hydrate_ai_pitch(sym=ticker, px=price, tr=trend_up, render_idx=idx):
                        # Non-blocking AI enhancement: render card instantly, then replace summary.
                        try:
                            from services.gemini_ai import generate_stock_matchmaker_pitch
                            ai_pitch = await run.io_bound(generate_stock_matchmaker_pitch, sym, float(px), tr)
                            if state['index'] == render_idx:
                                pitch_md.set_content(ai_pitch)
                        except Exception:
                            pass

                    async def warm_next_card(next_idx=idx + 1):
                        if next_idx < len(queue):
                            await get_card_data(queue[next_idx])

                    ui.timer(0.05, hydrate_ai_pitch, once=True)
                    ui.timer(0.05, warm_next_card, once=True)

        await render_card()


# ==========================================
# 8. ระบบ Export Excel (ดาวน์โหลดไฟล์) - Premium UI
# ==========================================
@ui.page('/export')
@standard_page_frame
async def export_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker()  # ?? เพิ่ม await ตรงนี้ 

    user_id = app.storage.user.get('user_id')
    
    with ui.column().classes('w-full max-w-4xl mx-auto p-4 md:p-8 gap-6 pt-[110px] md:pt-[120px] items-center'):
        
        with ui.column().classes('w-full bg-[#12161E]/80 backdrop-blur-xl border border-white/5 p-8 md:p-16 rounded-[32px] items-center text-center shadow-2xl relative overflow-hidden transition-all hover:border-white/10'):
            # แสง Glow ตรงกลาง
            ui.element('div').classes('absolute top-0 left-1/2 -translate-x-1/2 w-64 h-64 bg-[#32D74B]/10 rounded-full blur-[80px] pointer-events-none')
            
            ui.icon('cloud_download', size='100px').classes('text-[#D0FD3E] mb-6 drop-shadow-[0_0_20px_rgba(208,253,62,0.4)] z-10')
            ui.label('EXPORT PORTFOLIO DATA').classes('text-2xl md:text-3xl font-black text-white tracking-widest uppercase z-10')
            ui.label('ดาวน์โหลดข้อมูลพอร์ตการลงทุนของคุณเป็นไฟล์ CSV เพื่อนำไปวิเคราะห์ต่อใน Excel หรือแพลตฟอร์มอื่น').classes('text-gray-400 text-sm md:text-base mt-2 max-w-lg z-10')
            
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
                ui.notify('? ดาวน์โหลดไฟล์สำเร็จ!', type='positive')

            ui.button('DOWNLOAD SECURE CSV', icon='file_download', on_click=download_csv) \
                .classes('bg-gradient-to-r from-[#D0FD3E] to-[#32D74B] text-black font-black px-8 py-4 rounded-full text-lg shadow-[0_0_20px_rgba(50,215,75,0.4)] hover:scale-105 transition-transform mt-8 z-10')

            ui.button('กลับสู่หน้าหลัก', on_click=lambda: ui.navigate.to('/')) \
                .props('flat').classes('text-gray-500 hover:text-white mt-4 font-bold tracking-widest z-10')

# ==========================================
# 9. หน้าจัดการแพ็กเกจ (PAYMENT & SUBSCRIPTION)
# ==========================================
@ui.page('/payment')
@standard_page_frame
async def payment_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif; background-image: radial-gradient(circle at 50% -20%, #162418 0%, #0D1117 60%);')
    create_ticker()  # ?? เพิ่ม await ตรงนี้

    state = {'is_annual': False}

    with ui.column().classes('ax-page-shell w-full max-w-7xl mx-auto p-4 md:p-8 gap-6 md:gap-8 pt-20 md:pt-24 items-center relative ax-hero-glow'):
        
        with ui.column().classes('items-center text-center gap-2 mb-2'):
            ui.element('div').classes('w-52 h-52 absolute -top-10 rounded-full blur-[90px] bg-[#20D6A1]/15 pointer-events-none')
            ui.label('UNLOCK APEX MASTERY').classes('text-[10px] text-[#D0FD3E] font-black tracking-[0.4em] uppercase border border-[#D0FD3E]/30 px-5 py-1.5 rounded-full bg-[#D0FD3E]/5 z-10')
            ui.label('Choose Your Institutional Plan').classes('text-3xl md:text-5xl font-black text-white tracking-wide mt-2 z-10')
            ui.label('ยกระดับการลงทุนด้วย AI Signals, Matchmaker และระบบ Alert อัจฉริยะ').classes('text-sm md:text-lg text-gray-300 mt-2 px-4 z-10')
            with ui.row().classes('gap-2 mt-2 z-10'):
                ui.label('FAST ACTIVATION').classes('text-[10px] px-3 py-1 rounded-full bg-[#20D6A1]/15 text-[#20D6A1] border border-[#20D6A1]/25 font-black tracking-widest')
                ui.label('KBank QR READY').classes('text-[10px] px-3 py-1 rounded-full bg-[#39C8FF]/15 text-[#39C8FF] border border-[#39C8FF]/25 font-black tracking-widest')

        @ui.refreshable
        def pricing_section():
            is_annual = state['is_annual']
            
            with ui.row().classes('w-full justify-center mb-4 md:mb-6 z-10'):
                with ui.row().classes('bg-[#161B22] p-1.5 rounded-full border border-gray-800 items-center shadow-inner gap-1'):
                    btn_mo_class = 'bg-[#D0FD3E] text-black shadow-md' if not is_annual else 'bg-transparent text-gray-500 hover:text-white'
                    btn_yr_class = 'bg-[#D0FD3E] text-black shadow-md' if is_annual else 'bg-transparent text-gray-500 hover:text-white'
                    
                    ui.button('รายเดือน', on_click=lambda: set_annual(False)).props('unelevated').classes(f'px-4 md:px-6 py-2 text-xs md:text-sm font-black rounded-full transition-all {btn_mo_class}')
                    ui.button('รายปี (Save 20%)', on_click=lambda: set_annual(True)).props('unelevated').classes(f'px-4 md:px-6 py-2 text-xs md:text-sm font-black rounded-full transition-all {btn_yr_class}')

            with ui.grid(columns='grid-cols-1 lg:grid-cols-3').classes('w-full gap-4 md:gap-6 mt-2 items-stretch'):
                # FREE
                with ui.column().classes('w-full bg-[#0A1318]/85 border border-[#1c3744] p-6 md:p-8 rounded-[30px] shadow-xl justify-between ax-card-hover ax-equal-card'):
                    with ui.column().classes('gap-3'):
                        ui.label('BASIC ??').classes('text-xs font-black text-[#7aa5b8] tracking-[0.25em] uppercase')
                        ui.label('ฟรี ??').classes('text-5xl font-black text-white')
                        ui.label('เริ่มต้นติดตามตลาด ทดลองใช้ AI').classes('text-sm text-gray-400')
                        ui.element('div').classes('w-full h-px bg-white/10 my-2')
                        for text in ['สรุปสภาวะตลาดโลก', 'ข่าวด่วนการลงทุน', 'สร้าง Watchlist สูงสุด 3 ตัว', 'โควต้าวิเคราะห์กราฟ 10 ครั้ง/วัน']:
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('check', size='sm').classes('text-[#9ad0c7]')
                                ui.label(text).classes('text-sm text-gray-200')
                    ui.button('เริ่มต้นใช้งานฟรี ??', on_click=lambda: ui.navigate.to('/')).classes('mt-6 w-full border border-white/20 text-white font-black rounded-xl py-3')

                # VIP
                with ui.column().classes('w-full bg-gradient-to-b from-[#13232D] to-[#0B1720] border border-[#56D3FF]/35 p-6 md:p-8 rounded-[30px] shadow-[0_0_30px_rgba(86,211,255,0.14)] relative justify-between ax-card-hover ax-equal-card'):
                    ui.label('MOST POPULAR').classes('absolute -top-3 left-1/2 -translate-x-1/2 bg-[#1edc8b] text-black text-[10px] font-black px-4 py-1 rounded-full tracking-widest')
                    with ui.column().classes('gap-3'):
                        ui.label('ADVANCED ?').classes('text-xs font-black text-[#6ceac2] tracking-[0.25em] uppercase')
                        ui.label('VIP ??').classes('text-5xl font-black text-white')
                        ui.label(f"฿{'1,990' if is_annual else '299'} {'/ปี' if is_annual else '/เดือน'}").classes('text-4xl font-black text-white')
                        ui.label('ปลดล็อก AI วิเคราะห์กราฟแบบละเอียด').classes('text-sm text-[#9acfbf]')
                        ui.element('div').classes('w-full h-px bg-[#1edc8b]/25 my-2')
                        for text in ['ฟีเจอร์ Basic ทั้งหมด', 'สแกนกราฟ Unlimited (RSI, MACD, Volume)', 'Watchlist สูงสุด 10 ตัว', 'AI คำนวณแนวรับ-แนวต้านอัตโนมัติ', 'แผนเทรดจาก AI พร้อมจุดเข้า/TP/SL']:
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('bolt', size='sm').classes('text-[#1edc8b]')
                                ui.label(text).classes('text-sm text-white')
                    ui.button('อัปเกรด VIP ??', on_click=lambda: ui.notify('เลือกแพ็กเกจ VIP แล้ว สแกน QR ด้านล่าง', type='info')).classes('mt-6 w-full bg-[#1edc8b] text-black font-black rounded-xl py-3')

                # PRO
                with ui.column().classes('w-full bg-gradient-to-b from-[#13242E] to-[#0C1822] border border-[#7EF7CF] p-6 md:p-8 rounded-[30px] shadow-[0_0_34px_rgba(126,247,207,0.18)] relative justify-between ax-card-hover ax-equal-card'):
                    ui.label('BEST VALUE').classes('absolute -top-3 left-1/2 -translate-x-1/2 bg-[#20D6A1] text-black text-[10px] font-black px-4 py-1 rounded-full tracking-widest')
                    with ui.column().classes('gap-3'):
                        ui.label('ULTIMATE ??').classes('text-xs font-black text-[#7df3ca] tracking-[0.25em] uppercase')
                        ui.label('PRO ??').classes('text-5xl font-black text-white')
                        ui.label(f"฿{'4,990' if is_annual else '499'} {'/ปี' if is_annual else '/เดือน'}").classes('text-4xl font-black text-white')
                        ui.label('เครื่องมือระดับสถาบันสำหรับนักลงทุนจริงจัง').classes('text-sm text-[#a4d9c8]')
                        ui.element('div').classes('w-full h-px bg-[#20D6A1]/25 my-2')
                        for text in ['ฟีเจอร์ VIP ทั้งหมด', 'AI Stock Matchmaker', 'Morning Briefing สรุปตลาดทุกเช้า', 'Custom Price Alerts', 'Global News Alerts', 'Watchlist ไม่จำกัดจำนวน']:
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('star', size='sm').classes('text-[#20D6A1]')
                                ui.label(text).classes('text-sm text-white')
                    ui.button('อัปเกรด PRO ??', on_click=lambda: ui.notify('เลือกแพ็กเกจ PRO แล้ว สแกน QR ด้านล่าง', type='positive')).classes('mt-6 w-full bg-[#20D6A1] text-black font-black rounded-xl py-3')

        def set_annual(val):
            state['is_annual'] = val
            pricing_section.refresh()
            
        pricing_section()

        # ?? Payment Box
        with ui.row().classes('w-full max-w-4xl bg-gradient-to-r from-[#161B22] to-[#1C2128] border border-white/10 rounded-[30px] p-6 md:p-8 mt-6 shadow-2xl items-center justify-between relative overflow-hidden flex-col md:flex-row gap-6 md:gap-0 ax-neon-ring'):
            ui.element('div').classes('absolute top-0 right-0 w-64 h-64 bg-[#D0FD3E]/5 rounded-full blur-3xl pointer-events-none')
            
            with ui.column().classes('gap-1 z-10 text-center md:text-left'):
                ui.label('DIRECT BANK TRANSFER').classes('text-[10px] text-[#D0FD3E] font-black tracking-widest uppercase mb-2')
                ui.label('ธนาคารกสิกรไทย (KBank)').classes('text-xl font-bold text-white')
                ui.label('135-1-344-691').classes('text-3xl md:text-4xl font-black text-white tracking-[0.1em] my-1 font-mono drop-shadow')
                ui.label('นาย เกียรติศักดิ์ วุฒิจันทร์').classes('text-sm text-gray-400 font-bold uppercase tracking-wider')
            
            with ui.column().classes('items-center text-center w-full max-w-[300px] gap-3 bg-[#0D1117]/50 backdrop-blur-md p-6 rounded-2xl border border-white/5 z-10 shadow-inner'):
                ui.image(build_payment_qr_url()).classes('w-56 h-56 rounded-xl bg-white p-2')
                ui.label('โอนเงินตามแพ็กเกจ แล้วส่งสลิปให้บอท AI ตรวจสอบและอัปเกรดอัตโนมัติ').classes('text-xs text-gray-400 leading-relaxed')
                ui.button('ส่งสลิปใน TELEGRAM', icon='send', on_click=lambda: ui.navigate.to('https://t.me/Apexify_Trading_bot', new_tab=True)).classes('w-full bg-[#32D74B] text-black font-black py-3 rounded-xl mt-2 hover:scale-105 transition-transform shadow-[0_0_20px_rgba(50,215,75,0.3)]')

# ==========================================
# 9. หน้าจัดการการแจ้งเตือน (PRICE ALERTS) - Premium UI
# ==========================================
@ui.page('/alerts')
@standard_page_frame
async def alerts_page():
    ui.query('body').style(f'background-color: {COLORS.get("bg", "#0D1117")}; font-family: "Inter", sans-serif;')
    create_ticker() 

    tid = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(tid) if tid else {}
    role = str(user_info.get('role', 'free')).lower()

    with ui.column().classes('w-full max-w-7xl mx-auto p-4 md:p-8 gap-6 pt-20 md:pt-24'):
        
        with ui.row().classes('w-full justify-between items-end flex flex-col md:flex-row gap-4'):
            with ui.column().classes('gap-1'):
                ui.label('SMART PRICE ALERTS').classes('text-2xl md:text-3xl font-black text-white tracking-widest uppercase')
                ui.label('ระบบแจ้งเตือนราคาหุ้นและคริปโตอัตโนมัติ 24 ชม.').classes('text-xs md:text-sm text-gray-400')
            
            if role in ['free']:
                ui.button('?? UPGRADE PRO TO UNLOCK', on_click=lambda: ui.navigate.to('/payment')).classes('bg-gradient-to-r from-[#FFD700]/10 to-transparent text-[#FFD700] border border-[#FFD700]/30 font-black px-6 py-3 rounded-full text-xs tracking-widest shadow-lg w-full md:w-auto')
            else:
                ui.button('+ NEW ALERT (VIA BOT)', icon='telegram', on_click=lambda: ui.navigate.to('https://t.me/Apexify_Trading_bot', new_tab=True)).classes('bg-gradient-to-r from-[#D0FD3E] to-[#32D74B] text-black font-black px-6 py-3 rounded-full shadow-[0_0_20px_rgba(208,253,62,0.4)] hover:scale-105 transition-all text-xs md:text-sm w-full md:w-auto')

        alerts = await run.io_bound(get_user_price_alerts, str(tid))

        if not alerts:
            with ui.column().classes('w-full items-center justify-center p-8 md:p-16 bg-[#12161E]/50 backdrop-blur-md border border-white/5 rounded-[32px] mt-6 shadow-inner'):
                ui.icon('notifications_off', size='4xl').classes('text-gray-600 mb-4')
                ui.label('No Active Alerts').classes('text-lg md:text-xl font-bold text-gray-400')
                ui.label('คุณยังไม่มีการตั้งเตือนราคา เข้า Telegram แล้วพิมพ์ /alert เพื่อเริ่มต้นได้เลย').classes('text-xs md:text-sm text-gray-500 mt-2 text-center')
        else:
            with ui.grid(columns='grid-cols-1 sm:grid-cols-2 lg:grid-cols-3').classes('w-full gap-4 md:gap-6 mt-4'):
                for alert in alerts:
                    a_id = alert['id']
                    sym = alert['symbol']
                    target = alert['target_price']
                    cond = alert['condition']
                    is_active = alert['is_active'] == 1
                    
                    curr_price = await run.io_bound(get_live_price, sym)
                    dist_pct = ((target - curr_price) / curr_price * 100) if curr_price > 0 else 0
                    
                    status_color = '#32D74B' if is_active else '#8B949E'
                    status_text = '?? ACTIVE' if is_active else '? TRIGGERED'
                    bg_card = 'bg-[#12161E]/80' if is_active else 'bg-[#0B0E14]/50 opacity-70'
                    
                    # Alert Card (Glassmorphism)
                    with ui.column().classes(f'{bg_card} backdrop-blur-xl border border-white/5 p-5 md:p-6 rounded-[32px] shadow-lg relative overflow-hidden group hover:border-[#D0FD3E]/30 transition-all hover:-translate-y-1'):
                        if is_active:
                            ui.element('div').classes('absolute -top-10 -right-10 w-32 h-32 bg-[#D0FD3E]/10 rounded-full blur-[40px] pointer-events-none')

                        with ui.row().classes('w-full justify-between items-start mb-4 z-10'):
                            with ui.column().classes('gap-0'):
                                ui.label(sym).classes('text-2xl font-black text-white tracking-wider')
                                ui.label(status_text).classes(f'text-[10px] font-bold tracking-widest').style(f'color: {status_color}')
                            
                            def do_delete(alert_id=a_id):
                                if delete_price_alert(alert_id):
                                    ui.notify('??? ลบการแจ้งเตือนแล้ว', type='info')
                                    ui.navigate.reload()

                            ui.button(icon='delete', on_click=do_delete).props('flat dense').classes('text-gray-500 hover:text-[#FF453A] md:opacity-0 md:group-hover:opacity-100 transition-opacity bg-white/5 rounded-full p-2')

                        with ui.row().classes('w-full items-center justify-between bg-[#0B0E14]/80 backdrop-blur-md p-3 md:p-4 rounded-[20px] border border-white/5 z-10 shadow-inner'):
                            with ui.column().classes('gap-0'):
                                ui.label('TARGET').classes('text-[9px] text-gray-500 font-bold tracking-widest uppercase')
                                cond_str = "สูงกว่า" if cond == '>' else "ต่ำกว่า"
                                ui.label(f'{cond} ${target:,.2f}').classes('text-lg md:text-xl font-black text-[#D0FD3E] drop-shadow-[0_0_10px_rgba(208,253,62,0.3)]')
                            with ui.column().classes('gap-0 items-end'):
                                ui.label('CURRENT').classes('text-[9px] text-gray-500 font-bold tracking-widest uppercase')
                                ui.label(f'${curr_price:,.2f}').classes('text-lg md:text-xl font-bold text-white')

                        with ui.column().classes('w-full gap-2 mt-4 z-10'):
                            ui.label(f'Distance: {dist_pct:+.2f}%').classes('text-[10px] md:text-xs text-gray-400 font-bold tracking-wider uppercase')
                            with ui.element('div').classes('w-full h-2 bg-[#0B0E14] rounded-full overflow-hidden shadow-inner border border-white/5'):
                                progress = min(max(100 - abs(dist_pct)*2, 0), 100) 
                                bar_color = 'from-[#32D74B] to-[#D0FD3E]' if is_active else 'from-gray-600 to-gray-400'
                                ui.element('div').classes(f'h-full bg-gradient-to-r {bar_color} shadow-[0_0_10px_rgba(208,253,62,0.5)]').style(f'width: {progress}%')
# ==========================================
# ?? หน้าปัดเตือนภัยเศรษฐกิจ (MACRO-ECONOMIC HUD)
# ==========================================
@ui.page('/macro')
@standard_page_frame
async def macro_page(client):
    create_ticker() 
    await client.connected()

    with ui.column().classes('w-full max-w-7xl mx-auto p-4 md:p-8 gap-6 md:gap-8 pt-[110px] md:pt-[120px] items-center relative'):
        
        # ?? Header ของเพจ
        with ui.column().classes('items-center text-center gap-2 mb-4'):
            ui.label('INSTITUTIONAL RADAR').classes('text-[10px] text-[#FF453A] font-black tracking-[0.4em] uppercase border border-[#FF453A]/30 px-5 py-1.5 rounded-full bg-[#FF453A]/10')
            ui.label('Macro-Economic HUD').classes('text-3xl md:text-5xl font-black text-white tracking-wide mt-2')
            ui.label('หน้าปัดเตือนภัยเศรษฐกิจโลก สแกนความเสี่ยงระดับมหภาคแบบ Real-time').classes('text-sm md:text-lg text-gray-400 mt-2 px-4 text-center')

        # ?? ดึงข้อมูล 3 อินดิเคเตอร์หลักระดับโลก (เปลี่ยน CL=F เป็น USO ป้องกัน Error)
        try:
            vix = await run.io_bound(get_live_price, '^VIX') or 0.0  # ดัชนีความกลัว
            tnx = await run.io_bound(get_live_price, '^TNX') or 0.0  # ดอกเบี้ยพันธบัตร 10 ปี
            oil = await run.io_bound(get_live_price, 'USO') or 0.0   # ราคากองทุนน้ำมันดิบ USO
        except:
            vix, tnx, oil = 0.0, 0.0, 0.0

        # คำนวณความเสี่ยง (Logic สไตล์ Quant)
        vix_color = '#FF453A' if vix > 25 else '#FCD535' if vix > 18 else '#32D74B'
        vix_status = 'HIGH RISK (เทขาย)' if vix > 25 else 'WARNING (เฝ้าระวัง)' if vix > 18 else 'SAFE (ปลอดภัย)'
        
        tnx_color = '#FF453A' if tnx > 4.5 else '#FCD535' if tnx > 4.0 else '#32D74B'
        tnx_status = 'BEARISH (กดดันหุ้น)' if tnx > 4.5 else 'NEUTRAL (ทรงตัว)' if tnx > 4.0 else 'BULLISH (หนุนตลาด)'

        # กองทุนน้ำมัน USO ถ้าราคาเกิน 80 ดอลลาร์ แปลว่าเงินเฟ้อพลังงานเริ่มมา
        oil_color = '#FF453A' if oil > 80 else '#00BFFF'
        oil_status = 'INFLATION THREAT (เงินเฟ้อพุ่ง)' if oil > 80 else 'STABLE (พลังงานปกติ)'

        # ?? แผงหน้าปัด (Dashboard Grid)
        with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-3 gap-6 mt-2'):
            
            # หน้าปัด 1: VIX (Volatility)
            with ui.column().classes('bg-[#12161E]/80 backdrop-blur-xl border border-white/5 p-6 md:p-8 rounded-[32px] shadow-lg items-center text-center relative overflow-hidden transition-all hover:-translate-y-1'):
                ui.element('div').classes('absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl pointer-events-none').style(f'background-color: {vix_color}30;')
                ui.label('VOLATILITY INDEX (VIX)').classes('text-[10px] text-gray-400 font-black tracking-widest uppercase')
                ui.label(f'{vix:.2f}').classes('text-5xl md:text-6xl font-black mt-4 drop-shadow-md').style(f'color: {vix_color};')
                ui.label('ดัชนีความกลัวของนักลงทุน').classes('text-xs font-bold text-gray-500 mt-2')
                ui.label(vix_status).classes(f'text-xs font-black tracking-widest px-4 py-1.5 rounded-full mt-4 border').style(f'color: {vix_color}; border-color: {vix_color}50; background-color: {vix_color}10;')

            # หน้าปัด 2: US 10Y Yield
            with ui.column().classes('bg-[#12161E]/80 backdrop-blur-xl border border-white/5 p-6 md:p-8 rounded-[32px] shadow-lg items-center text-center relative overflow-hidden transition-all hover:-translate-y-1'):
                ui.element('div').classes('absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl pointer-events-none').style(f'background-color: {tnx_color}30;')
                ui.label('US 10-YEAR YIELD').classes('text-[10px] text-gray-400 font-black tracking-widest uppercase')
                ui.label(f'{tnx:.2f}%').classes('text-5xl md:text-6xl font-black mt-4 drop-shadow-md').style(f'color: {tnx_color};')
                ui.label('ผลตอบแทนพันธบัตรรัฐบาล').classes('text-xs font-bold text-gray-500 mt-2')
                ui.label(tnx_status).classes(f'text-xs font-black tracking-widest px-4 py-1.5 rounded-full mt-4 border').style(f'color: {tnx_color}; border-color: {tnx_color}50; background-color: {tnx_color}10;')

            # หน้าปัด 3: USO (US Oil Fund)
            with ui.column().classes('bg-[#12161E]/80 backdrop-blur-xl border border-white/5 p-6 md:p-8 rounded-[32px] shadow-lg items-center text-center relative overflow-hidden transition-all hover:-translate-y-1'):
                ui.element('div').classes('absolute -top-10 -right-10 w-32 h-32 rounded-full blur-3xl pointer-events-none').style(f'background-color: {oil_color}30;')
                ui.label('US OIL FUND (USO)').classes('text-[10px] text-gray-400 font-black tracking-widest uppercase')
                ui.label(f'${oil:.2f}').classes('text-5xl md:text-6xl font-black mt-4 drop-shadow-md').style(f'color: {oil_color};')
                ui.label('ต้นทุนพลังงานโลก (น้ำมัน)').classes('text-xs font-bold text-gray-500 mt-2')
                ui.label(oil_status).classes(f'text-xs font-black tracking-widest px-4 py-1.5 rounded-full mt-4 border').style(f'color: {oil_color}; border-color: {oil_color}50; background-color: {oil_color}10;')

        # ?? กล่อง AI สรุปกลยุทธ์ (AI Strategy Brief)
        with ui.row().classes('w-full bg-gradient-to-r from-[#161B22] to-[#1C2128] border border-white/10 rounded-[24px] p-6 md:p-8 mt-6 shadow-2xl items-center gap-6 flex-col md:flex-row relative overflow-hidden'):
            bg_glow = '#FF453A' if vix > 25 or tnx > 4.5 else '#32D74B'
            ui.element('div').classes('absolute top-0 left-0 w-2 h-full').style(f'background-color: {bg_glow}; box-shadow: 0 0 20px {bg_glow};')
            
            ui.icon('smart_toy' if vix <= 25 else 'warning', size='xl').style(f'color: {bg_glow};').classes('animate-pulse')
            
            with ui.column().classes('gap-1 flex-1 text-center md:text-left'):
                ui.label('AI SYSTEM ANALYSIS').classes('text-[10px] text-gray-500 font-black tracking-widest uppercase')
                
                if vix > 25:
                    ui.label('?? ตลาดมีความผันผวนและตื่นตระหนกสูงมาก แนะนำให้ "ลดพอร์ต" หรือถือเงินสด (Cash) เพิ่มขึ้นเพื่อป้องกันความเสี่ยง หลีกเลี่ยงหุ้นเติบโต (Growth Stocks)').classes('text-sm md:text-base text-white font-bold leading-relaxed')
                elif tnx > 4.5:
                    ui.label('?? ดอกเบี้ยและผลตอบแทนพันธบัตรอยู่ในระดับสูง กดดันตลาดหุ้น แนะนำให้เน้นลงทุนในหุ้นคุณค่า (Value Stocks) หรือหุ้นปันผลสูง').classes('text-sm md:text-base text-white font-bold leading-relaxed')
                else:
                    ui.label('? สภาวะเศรษฐกิจมหภาคอยู่ในเกณฑ์ปกติ ความเสี่ยงระบบ (Systemic Risk) ต่ำ สามารถถือรันเทรนด์ (Let Profit Run) หรือ DCA ได้ตามกลยุทธ์').classes('text-sm md:text-base text-white font-bold leading-relaxed')


@ui.page('/gemini')
@standard_page_frame
async def gemini_page(client):
    await client.connected()
    tid = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(tid) if tid else {}
    role = str(user_info.get('role', 'free')).lower()

    with ui.column().classes('w-full max-w-4xl mx-auto p-4 md:p-8 gap-4 pt-[110px] md:pt-[120px]'):
        with ui.card().classes('w-full bg-[#12161E]/70 border border-white/10 rounded-[24px] p-5 md:p-6'):
            ui.label('GEMINI COPILOT').classes('text-2xl md:text-3xl font-black text-white tracking-widest')
            ui.label('คุยกับ AI แบบต่อเนื่องหลายข้อความ').classes('text-sm text-gray-400')

        history = ui.column().classes('w-full min-h-[380px] max-h-[60vh] overflow-y-auto gap-3 bg-[#0B1320]/80 border border-[#39C8FF]/20 rounded-[20px] p-4')
        prompt_input = ui.textarea(placeholder='พิมพ์คำถามของคุณ...').props('outlined dark autogrow').classes('w-full')

        state = {'sending': False}

        async def send_prompt():
            if state['sending']:
                return
            q = (prompt_input.value or '').strip()
            if not q:
                return

            state['sending'] = True
            prompt_input.value = ''
            typing = None
            with history:
                ui.markdown(f'**You:** {q}').classes('text-sm text-white bg-white/5 rounded-xl p-3')
                typing = ui.row().classes('items-center gap-2 text-xs text-gray-400')
                with typing:
                    ui.spinner(size='sm', color='#39C8FF')
                    ui.label('Gemini is thinking...')

            try:
                from services.gemini_ai import generate_copilot_reply
                resp = await run.io_bound(generate_copilot_reply, q, role)
            except Exception as e:
                resp = f'AI unavailable: {e}'
            finally:
                if typing is not None:
                    try:
                        typing.delete()
                    except RuntimeError:
                        pass

            try:
                with history:
                    ui.markdown(f'**Gemini:** {resp}').classes('text-sm text-gray-100 bg-[#39C8FF]/10 border border-[#39C8FF]/20 rounded-xl p-3')
            except RuntimeError:
                pass
            finally:
                state['sending'] = False

        with ui.row().classes('w-full gap-2'):
            ui.button('Send', on_click=send_prompt, icon='send').classes('bg-[#20D6A1] text-black font-black rounded-xl px-5')
            ui.button('Back Dashboard', on_click=lambda: ui.navigate.to('/')).props('flat').classes('text-gray-300')


@ui.page('/healthz')
def healthz():
    ui.label('ok')


# สิ้นสุดไฟล์
# ==========================================
def run_web() -> None:
    ui.run(
        title=APP_TITLE,
        favicon="??",
        dark=True,
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_RELOAD,
        storage_secret=NICEGUI_STORAGE_SECRET or None,
    )


if __name__ in {"__main__", "__mp_main__"}:
    run_web()

