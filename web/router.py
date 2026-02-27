from nicegui import ui, app
from web.auth import logout, require_login
from core.models import get_user_by_telegram 
from functools import wraps
import inspect

def create_layout():
    """สร้าง Layout หลัก: Sidebar (ซ้าย) และ Header (บน)"""
    
    # 🌟 ผูกค่า value ของ drawer กับตัวแปรใน Storage เพื่อจำสถานะ (แก้บั๊ก Sidebar เด้งเปิดเอง)
    if 'drawer_open' not in app.storage.user:
        app.storage.user['drawer_open'] = False # ซ่อนไว้ก่อนตอนเปิดครั้งแรกบนมือถือ
        
    drawer = ui.left_drawer(fixed=True).classes('bg-[#0D1117]/90 backdrop-blur-lg p-4 w-64 border-r border-white/5 z-50').bind_value(app.storage.user, 'drawer_open')
    
    tid = app.storage.user.get('telegram_id')
    if tid:
        user_info = get_user_by_telegram(tid)
        if user_info:
            app.storage.user['role'] = str(user_info.get('role', 'free')).lower()
            
    role = app.storage.user.get('role', 'free')
    lang = app.storage.user.get('lang', 'TH')
    
    menu_title = 'เมนูหลัก' if lang == 'TH' else 'MAIN MENU'
    pro_title = 'เครื่องมือ PRO & VIP' if lang == 'TH' else 'PRO & VIP TOOLS'
    
    with drawer:
        ui.label(menu_title).classes('text-xs text-gray-500 font-bold mb-4 tracking-widest uppercase')
        
        main_menus = [
            ('dashboard', 'Dashboard', '/'),
        ]
        
        for icon, name, link in main_menus:
            color = 'text-[#D0FD3E]' if name in ['Dashboard'] else 'text-gray-400'
            with ui.button(on_click=lambda l=link: ui.navigate.to(l)).props('flat').classes(f'w-full justify-start {color} hover:text-white hover:bg-white/5 rounded-xl mb-1 transition-all'):
                ui.icon(icon, size='sm')
                ui.label(name).classes('ml-2 font-bold')

        ui.label(pro_title).classes('text-xs text-gray-500 font-bold mt-8 mb-4 tracking-widest uppercase')
        
        # 🌟 เพิ่มเมนู Payment เข้าไป
        pro_menus = [
            ('bar_chart', 'Analytics', '/analytics', ['pro', 'vip', 'admin']),
            ('attach_money', 'Dividend Calendar', '/dividend', ['pro', 'vip', 'admin']),
            ('grid_on', 'Market Heatmap', '/heatmap', ['pro', 'vip', 'admin']),
            ('trending_up', 'vs S&P500 Tracker', '/sp500', ['pro', 'vip', 'admin']),
            ('download', 'Export to Excel', '/export', ['pro', 'vip', 'admin']),
            ('credit_card', 'Subscription & Payment', '/payment', ['free', 'pro', 'vip', 'admin'])
        ]
        
        for icon, name, link, req_roles in pro_menus:
            is_locked = role not in req_roles
            
            def navigate_or_warn(l=link, locked=is_locked):
                if locked:
                    ui.notify(f'🔒 ฟีเจอร์นี้สำหรับผู้ใช้ระดับสูง (PRO/VIP) ติดต่อแอดมินเพื่ออัปเกรด', type='warning', position='top')
                else:
                    ui.navigate.to(l)

            # ให้สีปุ่ม Payment ดูเด่นขึ้นนิดหน่อย
            btn_color = 'text-[#D0FD3E]' if name == 'Subscription & Payment' else 'text-gray-400'
            
            with ui.button(on_click=navigate_or_warn).props('flat').classes(f'w-full justify-start {btn_color} hover:text-white hover:bg-white/5 rounded-xl mb-1 transition-all relative'):
                ui.icon(icon, size='sm')
                ui.label(name).classes('ml-2 font-bold')
                if is_locked:
                    ui.icon('lock', size='xs').classes('absolute right-4 text-[#FF453A]/70')

    with ui.header().classes('w-full h-16 bg-[#0D1117]/70 backdrop-blur-xl border-b border-white/5 p-4 flex justify-between items-center z-50 fixed'):
        with ui.row().classes('items-center gap-2'):
            ui.button(icon='menu_open', on_click=drawer.toggle).props('flat dense round').classes('text-gray-400 hover:text-[#D0FD3E]')
            with ui.row().classes('items-center gap-3 cursor-pointer ml-2').on('click', lambda: ui.navigate.to('/')):
                ui.icon('rocket_launch', size='sm').classes('text-[#D0FD3E] drop-shadow-[0_0_8px_rgba(208,253,62,0.6)]')
                ui.label('APEX WEALTH').classes('text-xl font-black text-white tracking-[0.15em]')
                
        with ui.row().classes('items-center gap-4'):
            ui.link('MAIN SITE', 'https://apexify-bot.vercel.app/').classes('text-gray-400 hover:text-[#D0FD3E] text-xs font-bold tracking-widest no-underline transition-colors')

            with ui.row().classes('items-center bg-[#161B22]/80 border border-gray-700/50 rounded-full px-1 py-1 shadow-inner'):
                def toggle_currency():
                    app.storage.user['currency'] = 'THB' if app.storage.user.get('currency', 'USD') == 'USD' else 'USD'
                    ui.navigate.reload()
                def toggle_lang():
                    app.storage.user['lang'] = 'EN' if app.storage.user.get('lang', 'TH') == 'TH' else 'TH'
                    ui.navigate.reload()

                curr = app.storage.user.get('currency', 'USD')
                lang = app.storage.user.get('lang', 'TH')
                
                ui.button('฿' if curr == 'THB' else '$', on_click=toggle_currency).props('flat round size=sm').classes('text-[#D0FD3E] font-bold w-8 h-8 hover:bg-white/10')
                ui.element('div').classes('w-[1px] h-4 bg-gray-700')
                ui.button('TH' if lang == 'TH' else 'EN', on_click=toggle_lang).props('flat round size=sm').classes('text-[#D0FD3E] font-bold w-8 h-8 hover:bg-white/10')

            ui.button(icon='logout', on_click=logout).props('flat round size=sm').classes('text-[#FF453A] hover:bg-[#FF453A]/20')

def standard_page_frame(content_func):
    @wraps(content_func)
    async def wrapper(*args, **kwargs):
        if not require_login(): return
        create_layout()
        if inspect.iscoroutinefunction(content_func):
            return await content_func(*args, **kwargs)
        else:
            return content_func(*args, **kwargs)
    return wrapper