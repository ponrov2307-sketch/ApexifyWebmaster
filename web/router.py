from nicegui import ui
from web.auth import logout, require_login

def create_header():
    """สร้างแถบเมนูด้านบนของเว็บไซต์ (Navigation Bar)"""
    with ui.header().classes('w-full bg-[#0D1117] border-b border-gray-800 p-4 flex justify-between items-center z-40'):
        # โลโก้และชื่อโปรเจกต์
        with ui.row().classes('items-center gap-3 cursor-pointer').on('click', lambda: ui.navigate.to('/')):
            ui.icon('rocket_launch', size='sm').classes('text-[#D0FD3E]')
            ui.label('APEX WEALTH').classes('text-xl font-black text-white tracking-widest')
            ui.label('MASTER').classes('text-xl font-black text-[#D0FD3E] tracking-widest -ml-2')

        # เมนูทางขวา
        with ui.row().classes('items-center gap-6 text-sm font-bold'):
            ui.link('DASHBOARD', '/').classes('text-white hover:text-[#D0FD3E] no-underline transition-colors')
            ui.link('VIP UPGRADE', 'https://t.me/ApexifyBot').classes('text-gray-400 hover:text-white no-underline transition-colors') # ลิงก์ไปหาบอท
            
            # ปุ่ม Logout
            ui.button('LOGOUT', icon='logout', on_click=logout) \
                .props('flat dense').classes('text-[#FF453A] hover:bg-red-500/10 px-3 py-1 rounded-md transition-colors')

def standard_page_frame(content_func):
    """Wrapper สำหรับสร้างโครงสร้างมาตรฐานให้ทุกหน้าเว็บ"""
    def wrapper(*args, **kwargs):
        # เช็คสิทธิ์ก่อนเรนเดอร์เนื้อหาหน้าเว็บ
        if not require_login():
            return
            
        # วาด Header เสมอ
        create_header()
        
        # คืนค่าเนื้อหาหลักของหน้านั้นๆ (ที่ถูกหุ้มอยู่)
        with ui.column().classes('w-full min-h-screen bg-[#0D1117]'):
            content_func(*args, **kwargs)
            
    return wrapper
