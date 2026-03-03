from nicegui import ui, app
from web.auth import logout, require_login
from core.models import get_user_by_telegram 
from functools import wraps
import inspect

def create_layout():
    if 'drawer_open' not in app.storage.user: app.storage.user['drawer_open'] = False 
        
    # 🌟 Sidebar ล้ำยุค (เหมือนเดิม)
    drawer = ui.left_drawer(fixed=True).classes('bg-[#05070A]/95 backdrop-blur-3xl p-4 w-64 border-r border-white/5 shadow-[20px_0_50px_rgba(0,0,0,0.5)] z-50').bind_value(app.storage.user, 'drawer_open')
    
    tid = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(tid) if tid else {}
    role = str(user_info.get('role', 'free')).lower()
    lang = app.storage.user.get('lang', 'TH')
    
    with drawer:
        with ui.row().classes('w-full items-center justify-center gap-3 mb-8 mt-4'):
            ui.icon('rocket_launch', size='md').classes('text-[#D0FD3E] drop-shadow-[0_0_15px_rgba(208,253,62,0.6)] animate-pulse')
            ui.label('APEXIFY').classes('text-2xl font-black text-white tracking-[0.2em]')

        ui.label('MAIN MENU' if lang == 'EN' else 'เมนูหลัก').classes('text-[9px] text-gray-500 font-black mb-2 tracking-widest uppercase pl-2')
        with ui.button(on_click=lambda: ui.navigate.to('/')).props('flat').classes('w-full justify-start text-[#D0FD3E] bg-[#D0FD3E]/10 border border-[#D0FD3E]/20 rounded-2xl mb-2 transition-all shadow-inner py-3'):
            ui.icon('dashboard', size='sm').classes('drop-shadow-md')
            ui.label('Dashboard').classes('ml-2 font-black tracking-wide')

        ui.element('div').classes('w-full h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent my-6')
        ui.label('PRO TOOLS' if lang == 'EN' else 'เครื่องมือ PRO').classes('text-[9px] text-gray-500 font-black mb-2 tracking-widest uppercase pl-2')
        
        pro_menus = [
            ('bar_chart', 'Analytics', '/analytics', ['pro', 'vip', 'admin']),
            ('radar', 'Macro HUD', '/macro', ['pro', 'vip', 'admin']), # 🌟 เพิ่มบรรทัดนี้
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
            with ui.button(on_click=nav).props('flat').classes(f'w-full justify-start {btn_class} rounded-2xl mb-1.5 transition-all relative py-2.5 group'):
                ui.icon(icon, size='sm').classes('group-hover:scale-110 transition-transform')
                ui.label(name).classes('ml-2 font-bold tracking-wide')
                if is_locked: ui.icon('lock', size='xs').classes('absolute right-4 text-[#FFD700]')

    # 🌟 Header แบบกระจกใส พร้อมปุ่มต่างๆ
    with ui.header().classes('w-full h-16 bg-[#05070A]/80 backdrop-blur-2xl border-b border-white/5 p-4 flex justify-between items-center z-50 fixed'):
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

def standard_page_frame(content_func):
    @wraps(content_func)
    async def wrapper(*args, **kwargs):
        if not require_login(): return
        create_layout()
        if inspect.iscoroutinefunction(content_func): return await content_func(*args, **kwargs)
        else: return content_func(*args, **kwargs)
    return wrapper