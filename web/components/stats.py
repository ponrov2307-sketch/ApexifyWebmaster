from nicegui import ui
from core.config import COLORS

def create_stats_cards(total_invested: float, net_worth: float, total_profit: float):
    profit_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
    is_profit = total_profit >= 0
    profit_color = COLORS['success'] if is_profit else COLORS['danger']
    profit_sign = "+" if is_profit else ""

    # 📱 ลด gap บนมือถือให้ชิดกันขึ้น
    with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-6 mt-4 md:mt-6 z-10'):
        
        with ui.column().classes('bg-[#11141C]/80 backdrop-blur-xl border border-white/5 p-4 md:p-6 rounded-2xl shadow-lg hover:-translate-y-1 transition-transform relative overflow-hidden group'):
            ui.element('div').classes('absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-3xl pointer-events-none group-hover:bg-white/10')
            ui.label('TOTAL INVESTED').classes('text-gray-500 text-[9px] md:text-[10px] font-black tracking-widest uppercase')
            ui.label(f"${total_invested:,.2f}").classes('text-xl md:text-3xl font-black text-white mt-1')
            
        with ui.column().classes('bg-gradient-to-br from-[#161B22] to-[#0B0E14] border border-[#FCD535]/30 p-4 md:p-6 rounded-2xl shadow-[0_0_20px_rgba(252,213,53,0.1)] hover:-translate-y-1 transition-transform relative overflow-hidden'):
            ui.element('div').classes('absolute -bottom-10 -right-10 w-32 h-32 bg-[#FCD535]/10 rounded-full blur-3xl pointer-events-none')
            ui.label('NET WORTH').classes('text-[#FCD535] text-[9px] md:text-[10px] font-black tracking-widest uppercase drop-shadow-md')
            ui.label(f"${net_worth:,.2f}").classes('text-2xl md:text-4xl font-black text-white mt-1')
            
        with ui.column().classes('bg-[#11141C]/80 backdrop-blur-xl border border-white/5 p-4 md:p-6 rounded-2xl shadow-lg hover:-translate-y-1 transition-transform relative overflow-hidden group'):
            bg_glow = 'bg-[#0ECB81]/10' if is_profit else 'bg-[#F6465D]/10'
            ui.element('div').classes(f'absolute top-0 right-0 w-32 h-32 {bg_glow} rounded-full blur-3xl pointer-events-none group-hover:opacity-80')
            ui.label('TOTAL RETURN').classes('text-gray-500 text-[9px] md:text-[10px] font-black tracking-widest uppercase')
            ui.label(f"{profit_sign}${abs(total_profit):,.2f} ({profit_sign}{profit_pct:.2f}%)").style(f'color: {profit_color}').classes('text-xl md:text-3xl font-black mt-1')