from nicegui import ui, app
from core.models import get_user_by_telegram
from core.config import COLORS


def login_page():
    """Login UI with existing auth flow (Telegram ID + 4-digit password)."""
    with ui.column().classes('absolute inset-0 items-center justify-center'):
        ui.element('div').classes('absolute top-10 left-1/2 -translate-x-1/2 w-[560px] h-[560px] rounded-full blur-[120px] bg-[#56D3FF]/16 pointer-events-none')
        with ui.card().classes('w-[94vw] max-w-[430px] p-8 md:p-10 items-center bg-[#0E1822]/92 border border-[#56D3FF]/24 rounded-[28px] shadow-[0_20px_60px_rgba(0,0,0,0.55)] backdrop-blur-xl relative overflow-hidden'):
            ui.element('div').classes('absolute -top-24 -right-24 w-64 h-64 rounded-full blur-3xl bg-[#7EF7CF]/12 pointer-events-none')
            ui.icon('shield_lock', size='3.2rem').classes('text-[#56D3FF] mb-2 z-10')
            ui.label('APEXIFY LOGIN').classes('text-3xl font-black text-white tracking-widest text-center z-10')
            ui.label('Sign in with your Telegram ID').classes('text-gray-400 text-sm mt-1 mb-6 z-10')

            telegram_id_input = ui.input('Telegram ID').classes('w-full mb-3').props('outlined dark')
            password_input = ui.input('Password').classes('w-full mb-2').props('outlined dark password type=password')
            ui.label('Current method: password = last 4 digits of Telegram ID').classes('text-[11px] text-amber-300 mb-6 text-center')

            def try_login():
                try:
                    tid_str = (telegram_id_input.value or '').strip()
                    tid = int(tid_str)
                    pwd = (password_input.value or '').strip()

                    if pwd != tid_str[-4:]:
                        ui.notify('Password incorrect (must be last 4 digits of Telegram ID)', type='negative')
                        return

                    user = get_user_by_telegram(tid)
                    if user:
                        app.storage.user['authenticated'] = True
                        app.storage.user['telegram_id'] = str(tid)
                        app.storage.user['user_id'] = user['user_id']

                        if 'currency' not in app.storage.user:
                            app.storage.user['currency'] = 'USD'
                        if 'lang' not in app.storage.user:
                            app.storage.user['lang'] = 'TH'

                        role = user.get('role', 'free')
                        role_str = role.upper() if role else 'FREE'
                        ui.notify(f'Login success ({role_str})', type='positive')
                        ui.navigate.to('/')
                    else:
                        ui.notify('Telegram ID not found. Please start bot first.', type='negative')
                except ValueError:
                    ui.notify('Telegram ID must be numeric', type='negative')

            ui.button('LOGIN', on_click=try_login).classes('w-full bg-gradient-to-r from-[#20D6A1] to-[#39C8FF] text-black font-black rounded-xl py-3 hover:scale-[1.01] transition-transform')


def require_login():
    """Check login permission for protected pages."""
    if not app.storage.user.get('authenticated', False):
        ui.navigate.to('/login')
        return False
    return True


def logout():
    """Logout while preserving non-auth preferences."""
    app.storage.user['authenticated'] = False
    app.storage.user.pop('telegram_id', None)
    app.storage.user.pop('user_id', None)
    ui.navigate.to('/login')
