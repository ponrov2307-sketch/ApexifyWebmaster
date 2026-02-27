from nicegui import ui
from web.auth import logout, require_login
from functools import wraps
import inspect

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
            # ลิงก์กลับไปหน้าเพจหลัก (Vercel)
            ui.link('MAIN SITE', 'https://apexify-bot.vercel.app/?hl=th-TH').classes('text-gray-400 hover:text-[#D0FD3E] no-underline transition-colors')
            
            ui.link('DASHBOARD', '/').classes('text-white hover:text-[#D0FD3E] no-underline transition-colors')
            ui.link('VIP UPGRADE', 'https://t.me/ApexifyBot').classes('text-gray-400 hover:text-white no-underline transition-colors') # ลิงก์ไปหาบอท
            
            # ปุ่ม Logout
            ui.button('LOGOUT', icon='logout', on_click=logout) \
                .props('flat dense').classes('text-[#FF453A] hover:bg-red-500/10 px-3 py-1 rounded-md transition-colors')

def standard_page_frame(content_func):
    """Wrapper สำหรับสร้างโครงสร้างมาตรฐานให้ทุกหน้าเว็บ"""
    
    @wraps(content_func)
    async def wrapper(*args, **kwargs):
        # เช็คสิทธิ์ก่อนเรนเดอร์เนื้อหาหน้าเว็บ
        if not require_login():
            return
            
        # วาด Header เมนูหลัก
        create_header()
        
        # 🌟 FIX: ปลดบล็อก ui.column() ออกไป เพื่อให้ Ticker สามารถสร้าง ui.header() ได้อย่างอิสระ
        if inspect.iscoroutinefunction(content_func):
            return await content_func(*args, **kwargs)
        else:
            return content_func(*args, **kwargs)
            
    return wrapper