from nicegui import ui, app
from core.models import get_user_by_telegram
from core.config import COLORS

def login_page():
    """หน้าต่างสำหรับการ Login"""
    with ui.card().classes('absolute-center w-96 p-8 items-center bg-[#161B22] border border-gray-800 rounded-2xl shadow-xl'):
        ui.icon('lock', size='3xl').classes('text-[#D0FD3E] mb-2')
        ui.label('APEX WEALTH MASTER').classes('text-2xl font-black text-white mb-6 tracking-wider text-center')
        
        ui.label('กรุณาเข้าสู่ระบบด้วย Telegram ID').classes('text-gray-400 text-sm mb-4')
        
        # ช่องกรอกข้อมูล
        telegram_id_input = ui.input('Telegram ID').classes('w-full mb-6').props('outlined dark')
        
        def try_login():
            try:
                tid = int(telegram_id_input.value)
                user = get_user_by_telegram(tid)
                if user:
                    # เก็บสถานะการล็อคอินลงใน Storage ของ Browser
                    app.storage.user['authenticated'] = True
                    app.storage.user['telegram_id'] = tid
                    app.storage.user['user_id'] = user['id']
                    
                    ui.notify(f'ยินดีต้อนรับคุณ {user["username"]}', type='positive')
                    ui.navigate.to('/') # พาไปหน้า Dashboard
                else:
                    ui.notify('ไม่พบ Telegram ID นี้ กรุณาพิมพ์ /start ในบอทก่อน', type='negative')
            except ValueError:
                ui.notify('Telegram ID ต้องเป็นตัวเลขเท่านั้น', type='negative')

        # ปุ่มกด Login
        ui.button('LOGIN', on_click=try_login).classes('w-full bg-[#D0FD3E] text-black font-black rounded-lg py-3 hover:bg-[#b5e62b] transition-colors')

def require_login():
    """ฟังก์ชันเช็คสิทธิ์การเข้าถึงหน้าเว็บ"""
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return False
    return True

def logout():
    """ฟังก์ชันออกจากระบบ"""
    app.storage.user.clear()
    ui.navigate.to('/login')