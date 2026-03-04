from nicegui import ui, app, run
from web.auth import logout, require_login
from core.models import get_user_by_telegram 
from functools import wraps
import inspect
from datetime import datetime, UTC
from services.yahoo_finance import get_real_fear_and_greed, get_live_price

ui.add_head_html('''
    <style>
        .q-ripple {
            display: none !important;
        }
        .q-btn {
            border-radius: 14px;
        }
        .q-btn:focus-visible {
            outline: 1px solid rgba(57, 200, 255, 0.5);
            outline-offset: 1px;
        }
    </style>
''', shared=True)


def _pulse_age_label(updated_at):
    if not updated_at:
        return 'updating...'
    try:
        dt = datetime.fromisoformat(updated_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        sec = max(int((datetime.now(UTC) - dt).total_seconds()), 0)
        if sec < 60:
            return f'{sec}s ago'
        return f'{sec // 60}m ago'
    except Exception:
        return 'recently'


def render_mini_market_pulse_sidebar(pulse):
    with ui.column().classes('w-full mt-5 bg-[#0E1C24]/80 border border-white/10 rounded-2xl p-3 gap-2 shadow-inner'):
        ui.label('MARKET PULSE').classes('text-[9px] text-[#39C8FF] font-black tracking-widest uppercase')
        with ui.row().classes('w-full justify-between items-center'):
            lbl_fg = ui.label('Fear&Greed --').classes('text-xs font-black')
            lbl_fg_status = ui.label('Loading').classes('text-[10px] text-gray-400 font-bold')
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('VIX').classes('text-[10px] text-gray-500 font-bold uppercase')
            lbl_vix = ui.label('--').classes('text-xs font-black')
        with ui.row().classes('w-full justify-between items-center mt-1'):
            lbl_age = ui.label('Updated ...').classes('text-[9px] text-gray-500')
            ui.button('Macro HUD', on_click=lambda: ui.navigate.to('/macro')).props('flat dense size=xs').classes('text-[#39C8FF] bg-[#39C8FF]/10 rounded-full px-2')

        async def refresh_pulse():
            current = app.storage.client.get('sidebar_pulse') or pulse or {}
            try:
                if not current:
                    fg_value, _ = await run.io_bound(get_real_fear_and_greed)
                    if fg_value <= 25:
                        fg_label, mood_color = 'EXTREME FEAR', '#FF453A'
                    elif fg_value <= 45:
                        fg_label, mood_color = 'FEAR', '#F97316'
                    elif fg_value <= 55:
                        fg_label, mood_color = 'NEUTRAL', '#8B949E'
                    elif fg_value <= 75:
                        fg_label, mood_color = 'GREED', '#FCD535'
                    else:
                        fg_label, mood_color = 'EXTREME GREED', '#32D74B'
                    vix = await run.io_bound(get_live_price, '^VIX') or 0.0
                    current = {
                        'fg_value': float(fg_value),
                        'fg_label': fg_label,
                        'vix': float(vix),
                        'mood_color': mood_color,
                        'updated_at': datetime.now(UTC).isoformat(),
                    }
                    app.storage.client['sidebar_pulse'] = current
            except Exception:
                current = current or {
                    'fg_value': 0.0,
                    'fg_label': 'UNAVAILABLE',
                    'vix': 0.0,
                    'mood_color': '#8B949E',
                    'updated_at': datetime.now(UTC).isoformat(),
                }

            fg_value = float(current.get('fg_value', 0))
            fg_label = current.get('fg_label', 'NEUTRAL')
            vix = float(current.get('vix', 0))
            mood_color = current.get('mood_color', '#8B949E')
            age = _pulse_age_label(current.get('updated_at'))
            vix_color = '#FF5E6C' if vix >= 25 else ('#FCD535' if vix >= 18 else '#20D6A1')

            lbl_fg.set_text(f'Fear&Greed {fg_value:.0f}')
            lbl_fg.style(f'color: {mood_color};')
            lbl_fg_status.set_text(fg_label)
            lbl_vix.set_text(f'{vix:,.2f}')
            lbl_vix.style(f'color: {vix_color};')
            lbl_age.set_text(f'Updated {age}')

        ui.timer(0.2, refresh_pulse, once=True)
        ui.timer(45.0, refresh_pulse)


def render_apexify_copilot_fab(role: str):
    is_pro = str(role).lower() in ['pro', 'vip', 'admin']
    with ui.dialog() as copilot_dialog, ui.card().classes('w-[92vw] max-w-[420px] h-[68vh] max-h-[640px] bg-[#0B1320]/95 border border-[#39C8FF]/30 rounded-3xl p-0 overflow-hidden'):
        with ui.column().classes('w-full h-full gap-0'):
            with ui.row().classes('w-full items-center justify-between px-4 py-3 border-b border-white/10'):
                ui.label('APEXIFY COPILOT').classes('text-sm font-black tracking-widest text-[#39C8FF]')
                ui.button(icon='close', on_click=copilot_dialog.close).props('flat round dense').classes('text-gray-400')
            with ui.column().classes('w-full h-full p-3 gap-3'):
                history = ui.column().classes('w-full flex-1 overflow-y-auto gap-2 pr-1')
                prompt_input = ui.textarea(placeholder='ถาม AI เช่น "วิเคราะห์ TSLA ล่าสุดแบบสั้นๆ"').props('outlined dark dense autogrow').classes('w-full')

                if not is_pro:
                    with history:
                        ui.markdown('**Copilot is a PRO/VIP feature.**\n\nอัปเกรดเพื่อใช้ AI บนเว็บแบบสดทันที').classes('text-sm text-gray-300')
                    ui.button('UPGRADE TO PRO', on_click=lambda: ui.navigate.to('/payment')).classes('w-full bg-[#FCD535] text-black font-black rounded-xl py-2')
                else:
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
                            ui.markdown(f'**You:** {q}').classes('text-sm text-white bg-white/5 rounded-xl p-2')
                            typing = ui.row().classes('items-center gap-2 text-xs text-gray-400')
                            with typing:
                                ui.spinner(size='sm', color='#39C8FF')
                                ui.label('Copilot is thinking...')
                        try:
                            from services.gemini_ai import generate_copilot_reply
                            resp = await run.io_bound(generate_copilot_reply, q, str(role).lower())
                        except Exception as e:
                            resp = f'AI unavailable: {e}'
                        finally:
                            if typing is not None:
                                try:
                                    typing.delete()
                                except RuntimeError:
                                    # The dialog/page may have been closed while the async task was running.
                                    return
                        try:
                            with history:
                                ui.markdown(f'**Copilot:** {resp}').classes('text-sm text-gray-100 bg-[#39C8FF]/10 border border-[#39C8FF]/20 rounded-xl p-2')
                        except RuntimeError:
                            # Ignore UI updates when user already navigated away.
                            return

                    with ui.row().classes('w-full gap-2'):
                        ui.button('Send', on_click=send_prompt, icon='send').classes('bg-[#20D6A1] text-black font-black rounded-xl px-4')
                        ui.button('Open Gemini Page', on_click=lambda: ui.navigate.to('/analytics')).props('flat').classes('text-gray-300')

    with ui.element('div').classes('fixed bottom-5 right-5 z-[1200]'):
        btn_cls = 'bg-[#20D6A1] text-black hover:scale-105' if is_pro else 'bg-[#FCD535] text-black hover:scale-105'
        ui.button('Apexify Copilot', icon='smart_toy', on_click=copilot_dialog.open).classes(f'{btn_cls} rounded-full px-5 py-3 font-black shadow-[0_12px_30px_rgba(0,0,0,0.45)] transition-transform')


def create_layout():
    if 'drawer_open' not in app.storage.user: app.storage.user['drawer_open'] = False 
        
    # 🌟 Sidebar ล้ำยุค (เหมือนเดิม)
    drawer = ui.left_drawer(fixed=True).classes('bg-gradient-to-b from-[#07121C]/95 to-[#060B12]/95 backdrop-blur-3xl p-4 w-64 border-r border-[#56D3FF]/12 shadow-[20px_0_50px_rgba(0,0,0,0.5)] z-50 transition-all duration-300').bind_value(app.storage.user, 'drawer_open')
    
    tid = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(tid) if tid else {}
    role = str(user_info.get('role', 'free')).lower()
    lang = app.storage.user.get('lang', 'TH')
    
    with drawer:
        with ui.row().classes('w-full items-center justify-center gap-3 mb-8 mt-4'):
            ui.icon('rocket_launch', size='md').classes('text-[#D0FD3E] drop-shadow-[0_0_15px_rgba(208,253,62,0.6)] animate-pulse')
            ui.label('APEXIFY').classes('text-2xl font-black text-white tracking-[0.2em]')

        ui.label('MAIN MENU' if lang == 'EN' else 'เมนูหลัก').classes('text-[9px] text-gray-500 font-black mb-2 tracking-widest uppercase pl-2')
        with ui.button(on_click=lambda: ui.navigate.to('/')).props('flat ripple=false').classes('w-full justify-start text-[#D0FD3E] bg-[#D0FD3E]/10 border border-[#D0FD3E]/20 rounded-2xl mb-2 transition-all shadow-inner py-3 overflow-hidden'):
            ui.icon('dashboard', size='sm').classes('drop-shadow-md')
            ui.label('Dashboard').classes('ml-2 font-black tracking-wide')

        ui.element('div').classes('w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent my-6')
        ui.label('PRO TOOLS' if lang == 'EN' else 'เครื่องมือ PRO').classes('text-[9px] text-gray-500 font-black mb-2 tracking-widest uppercase pl-2')
        
        pro_menus = [
            ('bar_chart', 'Analytics', '/analytics', ['pro', 'vip', 'admin']),
            ('favorite', 'AI Matchmaker', '/matchmaker', ['pro', 'vip', 'admin']),
            ('attach_money', 'Dividend', '/dividend', ['pro', 'vip', 'admin']),
            ('grid_on', 'Heatmap', '/heatmap', ['pro', 'vip', 'admin']),
            ('trending_up', 'vs S&P500', '/sp500', ['pro', 'vip', 'admin']),
            ('notifications_active', 'Price Alerts', '/alerts', ['pro', 'vip', 'admin']),
            ('download', 'Export', '/export', ['pro', 'vip', 'admin']),
            ('workspace_premium', 'Upgrade PRO', '/payment', ['free', 'pro', 'vip', 'admin'])
        ]
        
        for icon, name, link, req_roles in pro_menus:
            is_locked = role not in req_roles
            def nav(l=link, locked=is_locked, n=name):
                if locked: ui.notify(f'🔒 ฟีเจอร์ {n} สำหรับ PRO อัปเกรดเพื่อปลดล็อก!', type='warning')
                else: ui.navigate.to(l)

            btn_class = 'text-[#FFD700] bg-[#FFD700]/10 border border-[#FFD700]/30 hover:bg-[#FFD700]/20' if name == 'Upgrade PRO' else 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
            with ui.button(on_click=nav).props('flat ripple=false').classes(f'w-full justify-start {btn_class} rounded-2xl mb-1.5 transition-all relative py-2.5 group overflow-hidden'):
                ui.icon(icon, size='sm').classes('group-hover:scale-110 transition-transform')
                ui.label(name).classes('ml-2 font-bold tracking-wide')
                if is_locked: ui.icon('lock', size='xs').classes('absolute right-4 text-[#FFD700]')

        render_mini_market_pulse_sidebar(app.storage.client.get('sidebar_pulse'))

    # 🌟 Header แบบกระจกใส พร้อมปุ่มต่างๆ
    with ui.header().classes('w-full h-16 bg-gradient-to-r from-[#060B12]/88 via-[#0A1724]/88 to-[#060B12]/88 backdrop-blur-2xl border-b border-[#56D3FF]/12 p-4 flex justify-between items-center z-50 fixed'):
        # ฝั่งซ้าย (เมนูแฮมเบอร์เกอร์ + โลโก้มือถือ)
        with ui.row().classes('items-center gap-2'):
            ui.button(icon='menu', on_click=drawer.toggle).props('flat dense round').classes('text-gray-400 hover:text-[#D0FD3E] transition-colors')
            with ui.row().classes('items-center gap-2 cursor-pointer ml-2 md:hidden').on('click', lambda: ui.navigate.to('/')):
                ui.icon('rocket_launch', size='xs').classes('text-[#D0FD3E]')
                ui.label('APEX').classes('text-lg font-black text-white tracking-widest')
                
# 🌟 ฝั่งขวา (ปุ่มฟังก์ชันต่างๆ)
        with ui.row().classes('items-center gap-2 md:gap-4'):
            
            # 1. ปุ่มไปหน้าเว็บไซต์หลัก 
            # ใช้ gt-xs เพื่อโชว์ในคอม และ xs เพื่อโชว์ในมือถือ
            ui.button('MAIN SITE', icon='language', on_click=lambda: ui.navigate.to('https://apexify.co', new_tab=True)).props('flat size=sm').classes('text-gray-400 hover:text-white font-bold tracking-widest border border-white/10 rounded-full px-3 py-1 hover:bg-white/5 gt-xs')
            
            ui.button(icon='language', on_click=lambda: ui.navigate.to('https://apexify.co', new_tab=True)).props('flat round size=sm').classes('text-gray-400 hover:text-white border border-white/10 hover:bg-white/5 xs')

            # 2. ปุ่มสลับภาษา (TH / EN)
            def toggle_lang():
                app.storage.user['lang'] = 'EN' if app.storage.user.get('lang', 'TH') == 'TH' else 'TH'
                ui.navigate.reload()
            curr_lang = app.storage.user.get('lang', 'TH')
            ui.button(curr_lang, on_click=toggle_lang).props('flat round size=sm').classes('text-[#D0FD3E] font-black w-8 h-8 border border-[#D0FD3E]/30 bg-[#D0FD3E]/10 hover:bg-[#D0FD3E]/20 text-xs transition-all')

            # 4. ปุ่ม Logout
            ui.button(icon='power_settings_new', on_click=logout).props('flat round size=sm').classes('text-gray-500 hover:text-[#FF453A] hover:bg-[#FF453A]/10 transition-colors ml-1 md:ml-0')

    render_apexify_copilot_fab(role)

def standard_page_frame(content_func):
    @wraps(content_func)
    async def wrapper(*args, **kwargs):
        if not require_login(): return
        create_layout()
        if inspect.iscoroutinefunction(content_func): return await content_func(*args, **kwargs)
        else: return content_func(*args, **kwargs)
    return wrapper
