from nicegui import ui, app
from services.yahoo_finance import get_candlestick_data
from core.config import COLORS
import pandas as pd

def calculate_ma(day_count, data):
    result = []
    for i in range(len(data)):
        if i < day_count - 1:
            result.append('-')
            continue
        sum_val = sum(data[i - j]['close'] for j in range(day_count))
        result.append(round(sum_val / day_count, 2))
    return result

def calculate_macd(data):
    """🌟 ฟังก์ชันคำนวณ MACD ขั้นเทพ"""
    if not data: return [], [], []
    closes = pd.Series([d['close'] for d in data])
    ema12 = closes.ewm(span=12, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    
    macd_list = [round(x, 2) if not pd.isna(x) else '-' for x in macd]
    signal_list = [round(x, 2) if not pd.isna(x) else '-' for x in signal]
    hist_list = [round(x, 2) if not pd.isna(x) else '-' for x in hist]
    return macd_list, signal_list, hist_list

def find_support_resistance(data):
    """🌟 Smart Support/Resistance AI (หาแนวรับ-แนวต้านอัตโนมัติ)"""
    if not data: return 0, 0
    recent_data = data[-90:] # วิเคราะห์ 90 วันล่าสุด
    lows = sorted([d['low'] for d in recent_data])
    highs = sorted([d['high'] for d in recent_data], reverse=True)
    
    # ใช้ค่าเฉลี่ยของจุดต่ำสุด/สูงสุด 5 จุด เพื่อหาแนวรับแนวต้านที่แข็งแกร่ง (Smart S/R)
    support = sum(lows[:5]) / 5 if len(lows) >= 5 else lows[0]
    resistance = sum(highs[:5]) / 5 if len(highs) >= 5 else highs[0]
    return round(support, 2), round(resistance, 2)

async def show_candlestick_chart(ticker: str):
    raw_data = get_candlestick_data(ticker, period="6mo") 
    
    if not raw_data:
        ui.notify(f'ไม่พบข้อมูลกราฟสำหรับ {ticker}', type='warning')
        return

    dates = [item['date'] for item in raw_data]
    values = [[item['open'], item['close'], item['low'], item['high']] for item in raw_data]
    
    ma20 = calculate_ma(20, raw_data)
    ma50 = calculate_ma(50, raw_data)
    macd, signal, hist = calculate_macd(raw_data)
    support, resistance = find_support_resistance(raw_data)
    
    volumes = []
    hist_data = []
    for i, item in enumerate(raw_data):
        is_up = item['close'] >= item['open']
        volumes.append([i, item.get('volume', 0), 1 if is_up else -1])
        hist_val = hist[i] if hist[i] != '-' else 0
        hist_data.append({'value': hist_val, 'itemStyle': {'color': '#32D74B' if hist_val >= 0 else '#FF453A'}})

    with ui.dialog() as dialog, ui.card().classes('w-full max-w-6xl bg-[#0D1117]/95 backdrop-blur-2xl border border-white/10 p-0 rounded-3xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.8)]'):
        
        with ui.row().classes('w-full bg-gradient-to-r from-[#161B22] to-[#1C2128] p-5 border-b border-white/5 justify-between items-start z-10'):
            with ui.row().classes('items-center gap-4'):
                ui.icon('ssid_chart', size='lg').classes('text-[#D0FD3E]')
                with ui.column().classes('gap-0'):
                    ui.label(f"{ticker} - ADVANCED AI CHART").classes('text-2xl font-black text-white tracking-widest')
                    ui.label('Indicators: MA(20,50) • MACD • Smart S/R').classes('text-xs text-[#D0FD3E] font-bold tracking-wider')
            
            ui.button(icon='close', on_click=dialog.close).props('flat dense').classes('text-gray-400 hover:text-[#FF453A]')

        with ui.column().classes('w-full p-6 bg-[#0D1117] relative'):
            # 🌟 ป้ายบอกราคาแนวรับ-แนวต้านบนกราฟ
            with ui.row().classes('absolute top-8 left-20 z-20 gap-4 bg-[#11141C]/80 p-2 rounded-xl border border-white/10 backdrop-blur-sm shadow-lg'):
                with ui.row().classes('items-center gap-2'):
                    ui.element('div').classes('w-3 h-1 bg-[#FF453A]')
                    ui.label(f'Resistance: ${resistance:,.2f}').classes('text-xs font-bold text-white')
                with ui.row().classes('items-center gap-2'):
                    ui.element('div').classes('w-3 h-1 bg-[#32D74B]')
                    ui.label(f'Support: ${support:,.2f}').classes('text-xs font-bold text-white')

            ui.echart({
                'animation': False,
                'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'cross'}},
                'axisPointer': {'link': [{'xAxisIndex': 'all'}], 'label': {'backgroundColor': '#777'}}, 
                'grid': [
                    {'left': '8%', 'right': '8%', 'height': '45%', 'top': '8%'},          
                    {'left': '8%', 'right': '8%', 'top': '58%', 'height': '12%'},         
                    {'left': '8%', 'right': '8%', 'top': '76%', 'height': '15%'}          
                ],
                'xAxis': [
                    {'type': 'category', 'data': dates, 'boundaryGap': False, 'axisLine': {'lineStyle': {'color': '#8B949E'}}, 'min': 'dataMin', 'max': 'dataMax'},
                    {'type': 'category', 'gridIndex': 1, 'data': dates, 'axisLabel': {'show': False}, 'min': 'dataMin', 'max': 'dataMax'},
                    {'type': 'category', 'gridIndex': 2, 'data': dates, 'axisLabel': {'show': False}, 'min': 'dataMin', 'max': 'dataMax'}
                ],
                'yAxis': [
                    {'scale': True, 'splitLine': {'lineStyle': {'color': '#1C2128', 'type': 'dashed'}}},
                    {'scale': True, 'gridIndex': 1, 'splitNumber': 2, 'axisLabel': {'show': False}, 'splitLine': {'show': False}},
                    {'scale': True, 'gridIndex': 2, 'splitNumber': 2, 'splitLine': {'lineStyle': {'color': '#1C2128', 'type': 'dashed'}}}
                ],
                'dataZoom': [
                    {'type': 'inside', 'xAxisIndex': [0, 1, 2], 'start': 30, 'end': 100},
                    {'show': True, 'xAxisIndex': [0, 1, 2], 'type': 'slider', 'bottom': '0%', 'textStyle': {'color': '#8B949E'}, 'borderColor': '#1C2128'}
                ],
                'series': [
                    {
                        'name': 'Candle', 'type': 'candlestick', 'data': values, 
                        'itemStyle': {'color': COLORS['success'], 'color0': COLORS['danger'], 'borderColor': COLORS['success'], 'borderColor0': COLORS['danger']},
                        # 🌟 ตีเส้นแนวรับแนวต้านใน ECharts
                        'markLine': {
                            'symbol': ['none', 'none'],
                            'data': [
                                {'yAxis': resistance, 'name': 'Resistance', 'lineStyle': {'color': '#FF453A', 'type': 'dashed', 'width': 1.5}},
                                {'yAxis': support, 'name': 'Support', 'lineStyle': {'color': '#32D74B', 'type': 'dashed', 'width': 1.5}}
                            ],
                            'label': {'show': False}
                        }
                    },
                    {'name': 'MA20', 'type': 'line', 'data': ma20, 'smooth': True, 'showSymbol': False, 'lineStyle': {'width': 2, 'color': '#3b82f6'}},
                    {'name': 'MA50', 'type': 'line', 'data': ma50, 'smooth': True, 'showSymbol': False, 'lineStyle': {'width': 2, 'color': '#f97316'}},
                    {'name': 'Volume', 'type': 'bar', 'xAxisIndex': 1, 'yAxisIndex': 1, 'data': volumes, 'itemStyle': {'color': """new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: '#32D74B'}, {offset: 1, color: '#FF453A'}])"""}},
                    {'name': 'MACD', 'type': 'line', 'xAxisIndex': 2, 'yAxisIndex': 2, 'data': macd, 'showSymbol': False, 'lineStyle': {'color': '#3b82f6', 'width': 1.5}},
                    {'name': 'Signal', 'type': 'line', 'xAxisIndex': 2, 'yAxisIndex': 2, 'data': signal, 'showSymbol': False, 'lineStyle': {'color': '#f97316', 'width': 1.5}},
                    {'name': 'Histogram', 'type': 'bar', 'xAxisIndex': 2, 'yAxisIndex': 2, 'data': hist_data}
                ]
            }).classes('w-full h-[600px]')

    dialog.on('hide', lambda: app.storage.client.update({'modal_open': False}))
    dialog.open()