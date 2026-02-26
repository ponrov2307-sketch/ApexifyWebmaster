from nicegui import ui
from core.config import COLORS

def create_stats_cards(total_invested: float, net_worth: float, total_profit: float):
    """สร้างการ์ดแสดงตัวเลขสรุปพอร์ต 3 ใบ (Stats)"""
    
    # คำนวณเปอร์เซ็นต์กำไร และเช็คสีเขียว/แดง
    profit_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
    is_profit = total_profit >= 0
    profit_color = COLORS['success'] if is_profit else COLORS['danger']
    profit_sign = "+" if is_profit else ""

    with ui.row().classes('w-full gap-6 mt-6'):
        # 💳 การ์ดใบที่ 1: Total Invested
        with ui.card().classes('flex-1 bg-[#161B22] border border-gray-800 p-6 rounded-2xl transition-all hover:border-[#D0FD3E]/50'):
            ui.label('TOTAL INVESTED').classes('text-gray-500 text-[10px] font-black tracking-widest uppercase')
            ui.label(f"${total_invested:,.2f}").classes('text-3xl font-black text-white mt-1')
            
        # 💳 การ์ดใบที่ 2: Net Worth (ใบหลัก เรืองแสงตลอด)
        with ui.card().classes('flex-1 bg-[#161B22] border border-[#D0FD3E]/30 p-6 rounded-2xl shadow-[0_0_15px_rgba(208,253,62,0.1)]'):
            ui.label('NET WORTH').classes('text-gray-400 text-[10px] font-black tracking-widest uppercase')
            ui.label(f"${net_worth:,.2f}").classes('text-4xl font-black text-[#D0FD3E] mt-1')
            
        # 💳 การ์ดใบที่ 3: Total Return (เปลี่ยนสีตามกำไร/ขาดทุน)
        with ui.card().classes('flex-1 bg-[#161B22] border border-gray-800 p-6 rounded-2xl transition-all hover:border-[#D0FD3E]/50'):
            ui.label('TOTAL RETURN').classes('text-gray-500 text-[10px] font-black tracking-widest uppercase')
            with ui.row().classes('items-baseline gap-2 mt-1'):
                ui.label(f"{profit_sign}${total_profit:,.2f}").style(f'color: {profit_color}').classes('text-3xl font-black')
                ui.label(f"({profit_sign}{profit_pct:.2f}%)").style(f'color: {profit_color}').classes('text-sm font-bold')