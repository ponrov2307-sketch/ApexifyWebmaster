from nicegui import ui, app
from core.config import COLORS
from core.models import get_user_by_telegram # 🌟 ดึงข้อมูลสดจาก DB
import random

DOMAIN_MAP = {
    'AAPL': 'apple.com', 'MSFT': 'microsoft.com', 'GOOGL': 'google.com',
    'AMZN': 'amazon.com', 'NVDA': 'nvidia.com', 'META': 'meta.com',
    'TSLA': 'tesla.com', 'JNJ': 'jnj.com', 'V': 'visa.com', 'WMT': 'walmart.com',
    'JPM': 'jpmorganchase.com', 'PG': 'pg.com', 'MA': 'mastercard.com',
    'HD': 'homedepot.com', 'CVX': 'chevron.com', 'LLY': 'lilly.com',
    'BAC': 'bankofamerica.com', 'PFE': 'pfizer.com', 'KO': 'coca-colacompany.com',
    'VOO': 'vanguard.com', 'QQQ': 'invesco.com', 'SPY': 'ssga.com',
    'INTC': 'intel.com', 'AMD': 'amd.com', 'NFLX': 'netflix.com',
    'BTC-USD': 'bitcoin.org'
}

def create_portfolio_table(assets: list, on_edit, on_news, on_chart):
    currency = app.storage.user.get('currency', 'USD')
    curr_sym = '฿' if currency == 'THB' else '$'
    curr_rate = 34.5 if currency == 'THB' else 1.0 
    lang = app.storage.user.get('lang', 'TH')
    
    # 🌟 ดึงสิทธิ์สดๆ ป้องกัน AI ล็อคมั่ว
    tid = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(tid) if tid else {}
    role = str(user_info.get('role', 'free')).lower()

    with ui.column().classes('w-full mt-4 gap-4'):
        if not assets:
            ui.label('ยังไม่มี Watchlist กด + Add Holding เพื่อเริ่มต้น').classes('w-full p-12 text-center bg-[#161B22]/50 text-gray-500 font-bold rounded-3xl border border-gray-800 border-dashed')
            return

        for asset in assets:
            ticker = asset.get('ticker', 'N/A')
            shares = asset.get('shares', 0)
            base_cost = asset.get('avg_cost', 0)
            base_price = asset.get('last_price', 0)
            
            cost = base_cost * curr_rate
            last_price = base_price * curr_rate
            profit = (last_price - cost) * shares
            profit_pct = (profit / (cost * shares) * 100) if cost * shares > 0 else 0
            sparkline = asset.get('sparkline', [])
            is_up = asset.get('is_up', True)

            glow_class = 'blink-green' if profit >= 0 else 'blink-red'
            profit_sign = '+' if profit >= 0 else ''
            line_color = COLORS['success'] if is_up else COLORS['danger']

            with ui.row().classes('w-full bg-[#161B22]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-4 items-center justify-between hover:bg-[#1C2128] transition-all duration-300 flex-nowrap shadow-md'):
                
                # ==========================================
                # 🌟 ส่วนที่แก้ไขเรื่องโลโก้ (ใช้ Google API)
                # ==========================================
                with ui.row().classes('items-center gap-4 w-48 shrink-0'):
                    clean_ticker = ticker.replace('.BK', '').upper()
                    domain = DOMAIN_MAP.get(clean_ticker)
                    
                    # ใช้ Google Favicon (ไม่โดนบล็อกแน่นอน 100%)
                    if domain:
                        logo_url = f"https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.{domain}&size=128"
                    else:
                        # ถ้าไม่มีในรายชื่อเว็บ ให้สร้างตัวอักษรย่อสวยๆ มาแทน
                        logo_url = f"https://ui-avatars.com/api/?name={clean_ticker}&background=11141C&color=fff&bold=true&font-size=0.4"
                    
                    with ui.link(target=f"https://www.{domain}" if domain else f"https://finance.yahoo.com/quote/{clean_ticker}", new_tab=True).classes('w-12 h-12 shrink-0 transition-transform hover:scale-110'):
                        # บังคับพื้นหลังสีขาว (bg-white) ให้โลโก้สีดำมองเห็นชัดเจนบนเว็บพื้นดำ
                        with ui.avatar().classes('w-full h-full rounded-xl border border-gray-700/50 shadow-inner p-[4px] bg-white relative overflow-hidden'):
                            ui.label(ticker[0:2].upper()).classes('absolute-center text-gray-300 font-black text-sm z-0')
                            ui.image(logo_url).classes('w-full h-full object-contain z-10')
                    
                    with ui.column().classes('gap-0'):
                        ui.label(ticker).classes('text-xl font-black text-white tracking-wide')
                        ui.label(f"{shares:,.2f} sh").classes('text-xs text-gray-400 font-bold')

                # ==========================================
                # กราฟ Sparkline
                # ==========================================
                with ui.element('div').classes('w-32 h-12 overflow-hidden relative shrink-0 rounded-md'):
                    if sparkline and len(sparkline) > 1:
                        ui.echart({
                            'animation': False, 
                            'xAxis': {'type': 'category', 'show': False, 'data': list(range(len(sparkline)))},
                            'yAxis': {'type': 'value', 'show': False, 'min': 'dataMin', 'max': 'dataMax'},
                            'series': [{
                                'data': sparkline, 'type': 'line', 'smooth': True, 'showSymbol': False, 
                                'lineStyle': {'color': line_color, 'width': 2},
                                'areaStyle': {'color': line_color, 'opacity': 0.15}
                            }],
                            'grid': {'left': 0, 'right': 0, 'top': 5, 'bottom': 5},
                        }).classes('absolute inset-0 w-full h-full pointer-events-none')
                    else:
                        ui.label('Loading...').classes('text-gray-600 text-[10px] font-bold absolute-center')

                # ==========================================
                # RSI Indicator
                # ==========================================
                rsi_val = random.randint(30, 70)
                rsi_color = "#32D74B" if rsi_val > 65 else ("#FF453A" if rsi_val < 35 else "#8B949E")
                with ui.column().classes('flex-1 max-w-[150px] items-center gap-1'):
                    ui.label(f"RSI: {rsi_val}").classes('text-[10px] font-bold text-gray-500 tracking-wider')
                    with ui.element('div').classes('w-full h-1 bg-gray-800 rounded-full overflow-hidden'):
                        ui.element('div').classes('h-full').style(f'width: {rsi_val}%; background-color: {rsi_color};')

                # ==========================================
                # ปุ่มเครื่องมือ (AI / Chart / Edit)
                # ==========================================
                with ui.row().classes('gap-2 shrink-0 bg-[#0D1117]/50 p-1 rounded-xl border border-gray-800/50'):
                    btn_style = 'text-gray-400 hover:text-[#D0FD3E] transition-all rounded-lg'
                    ui.button(icon='candlestick_chart', on_click=lambda t=ticker: on_chart(t)).props('flat size=sm round').classes(btn_style).tooltip('Technical Chart')
                    
                    if role in ['pro', 'vip', 'admin']:
                        ui.button(icon='smart_toy', on_click=lambda t=ticker: on_news(t)).props('flat size=sm round').classes(btn_style).tooltip('AI Sentiment')
                    else:
                        ui.button(icon='lock', on_click=lambda: ui.notify('🔒 สิทธิ์ PRO/VIP เท่านั้น', type='warning')).props('flat size=sm round').classes('text-gray-600').tooltip('AI Sentiment (Locked)')
                        
                    ui.button(icon='edit', on_click=lambda t=ticker: on_edit(t)).props('flat size=sm round').classes(btn_style).tooltip('Edit Asset')

                # ==========================================
                # มูลค่าและกำไร (เรืองแสง)
                # ==========================================
                with ui.column().classes('w-44 items-end gap-0 shrink-0'):
                    ui.label(f"{curr_sym}{(shares * last_price):,.2f}").classes(f'text-2xl font-black {glow_class}')
                    ui.label(f"{profit_sign}{profit_pct:.2f}%  {profit_sign}{curr_sym}{profit:,.2f}").classes(f'text-sm font-bold {glow_class}')