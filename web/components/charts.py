from nicegui import ui, app
from core.models import get_user_by_telegram
from web.i18n import tr
import yfinance as yf
import pandas as pd


async def show_candlestick_chart(ticker: str):
    app.storage.client['modal_open'] = True

    def clear_modal_state():
        app.storage.client['modal_open'] = False

    tid = app.storage.user.get('telegram_id')
    user_info = get_user_by_telegram(tid) if tid else {}
    role = str(user_info.get('role', 'free')).lower()
    is_paid_user = role in ['vip', 'pro', 'admin']
    lang = str(app.storage.user.get('lang', 'TH')).upper()

    def fetch_dynamic_data(symbol, period, interval):
        try:
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            if data.empty:
                return []

            if isinstance(data.columns, pd.MultiIndex):
                data = data.xs(symbol, level=1, axis=1)

            ohlc = []
            for index, row in data.iterrows():
                ohlc.append({
                    'date': index.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']),
                })
            return ohlc
        except Exception:
            return []

    try:
        with ui.dialog() as dialog, ui.card().classes(
            'w-full max-w-6xl bg-[#0B0E14] border border-[#1F2937] '
            'p-0 rounded-2xl shadow-[0_0_80px_rgba(0,0,0,0.9)]'
        ):
            with ui.row().classes(
                'w-full bg-gradient-to-r from-[#161B22] to-[#0D1117] '
                'p-5 border-b border-white/5 justify-between items-center z-10'
            ):
                with ui.row().classes('items-center gap-4'):
                    ui.icon('candlestick_chart', size='lg').classes(
                        'text-[#D0FD3E] drop-shadow-[0_0_10px_rgba(208,253,62,0.5)]'
                    )
                    with ui.column().classes('gap-0'):
                        ui.label(f'{ticker}').classes(
                            'text-2xl font-black text-white tracking-widest leading-none'
                        )
                        ui.label('ADVANCED TECHNICAL CHART').classes(
                            'text-[10px] text-gray-500 font-bold tracking-[0.2em]'
                        )
                ui.button(icon='close', on_click=dialog.close).props('flat dense').classes(
                    'text-gray-500 hover:text-[#FF453A] transition-colors'
                )

            with ui.column().classes('w-full p-6 relative'):
                with ui.row().classes('w-full justify-between items-center mb-3 z-10 relative'):
                    with ui.row().classes('gap-4 items-center'):
                        ui.label('Interactive TradingView Style').classes(
                            'text-[10px] font-bold text-gray-500 tracking-widest uppercase '
                            'bg-[#161B22] px-3 py-1 rounded-md border border-white/5'
                        )
                        with ui.row().classes('gap-3 text-[10px] font-black tracking-wider'):
                            ui.label('MA 9').classes('text-[#D0FD3E]')
                            ui.label('MA 20').classes('text-[#00BFFF]')

                    with ui.row().classes(
                        'gap-1 bg-[#11141C] p-1 rounded-lg border border-gray-800 shadow-inner'
                    ):
                        btn_1d = ui.button('1D').props('unelevated size=sm').classes(
                            'bg-[#1F2937] text-[#D0FD3E] font-black border border-white/10 shadow-md'
                        )
                        btn_1w = ui.button('1W').props('flat size=sm').classes(
                            'text-gray-400 hover:text-white font-bold transition-colors'
                        )
                        btn_1m = ui.button('1M').props('flat size=sm').classes(
                            'text-gray-400 hover:text-white font-bold transition-colors'
                        )

                        if not is_paid_user:
                            btn_1w.props('icon=lock').classes(replace='text-gray-600')
                            btn_1m.props('icon=lock').classes(replace='text-gray-600')

                chart_element = ui.echart({}).classes(
                    'w-full h-[600px] rounded-xl overflow-hidden'
                )
                status_label = ui.label('').classes(
                    'text-xs md:text-sm text-[#FCD535] font-bold mt-2'
                )
                status_label.set_visibility(False)

                def set_status(message: str):
                    if message:
                        status_label.set_text(message)
                        status_label.set_visibility(True)
                    else:
                        status_label.set_text('')
                        status_label.set_visibility(False)

                def render_empty_chart(message: str):
                    chart_element.options.clear()
                    chart_element.options.update({
                        'backgroundColor': '#0B0E14',
                        'xAxis': {'show': False, 'type': 'category', 'data': []},
                        'yAxis': {'show': False, 'type': 'value'},
                        'series': [],
                        'graphic': [{
                            'type': 'text',
                            'left': 'center',
                            'top': 'middle',
                            'style': {
                                'text': message,
                                'fill': '#8B949E',
                                'fontSize': 14,
                                'fontWeight': 'bold',
                                'align': 'center',
                                'lineHeight': 22,
                            },
                        }],
                    })
                    chart_element.update()

                def change_timeframe(interval_code, period_code, active_btn):
                    if not is_paid_user and interval_code in ['1wk', '1mo']:
                        ui.notify(
                            tr('charts.locked_timeframe', lang),
                            type='warning',
                        )
                        return

                    for b in [btn_1d, btn_1w, btn_1m]:
                        if not is_paid_user and b in [btn_1w, btn_1m]:
                            continue
                        b.props('flat remove=unelevated').classes(
                            replace='text-gray-400 hover:text-white font-bold transition-colors'
                        )
                    active_btn.props('unelevated remove=flat').classes(
                        replace='bg-[#1F2937] text-[#D0FD3E] font-black border border-white/10 shadow-md'
                    )

                    raw_data = fetch_dynamic_data(ticker, period_code, interval_code)
                    if not raw_data:
                        status_message = tr(
                            'charts.data_feed_unavailable',
                            lang,
                            ticker=ticker,
                            interval=interval_code,
                        )
                        set_status(
                            status_message
                        )
                        render_empty_chart(
                            tr('charts.data_feed_unavailable_short', lang)
                        )
                        ui.notify(
                            tr('charts.load_failed', lang, ticker=ticker, interval=interval_code),
                            type='warning',
                        )
                        return

                    set_status('')

                    dates = [d['date'] for d in raw_data]
                    k_data = [[d['open'], d['close'], d['low'], d['high']] for d in raw_data]

                    ma9, ma20 = [], []
                    for i in range(len(k_data)):
                        ma9.append(
                            round(sum([x[1] for x in k_data[i - 8:i + 1]]) / 9, 2) if i >= 8 else '-'
                        )
                        ma20.append(
                            round(sum([x[1] for x in k_data[i - 19:i + 1]]) / 20, 2) if i >= 19 else '-'
                        )

                    from services.yahoo_finance import calculate_bollinger_bands
                    closes = [d['close'] for d in raw_data]
                    bb_upper, _, bb_lower = calculate_bollinger_bands(closes)

                    volumes = []
                    for d in raw_data:
                        color = '#32D74B' if d['close'] >= d['open'] else '#FF453A'
                        volumes.append({'value': d['volume'], 'itemStyle': {'color': color, 'opacity': 0.7}})

                    chart_element.options.clear()
                    chart_element.options.update({
                        'backgroundColor': '#0B0E14',
                        'title': {
                            'text': ticker,
                            'textStyle': {
                                'color': 'rgba(255, 255, 255, 0.03)',
                                'fontSize': 140,
                                'fontWeight': '900',
                                'fontFamily': 'sans-serif',
                            },
                            'left': 'center',
                            'top': 'center',
                            'z': 0,
                        },
                        'tooltip': {
                            'trigger': 'axis',
                            'axisPointer': {
                                'type': 'cross',
                                'lineStyle': {'color': '#32D74B', 'type': 'dashed'},
                            },
                            'backgroundColor': 'rgba(17, 20, 28, 0.9)',
                            'borderColor': '#1F2937',
                            'textStyle': {'color': '#fff'},
                            'borderWidth': 1,
                            'padding': 12,
                        },
                        'axisPointer': {'link': [{'xAxisIndex': 'all'}]},
                        'grid': [
                            {'left': '2%', 'right': '6%', 'top': '5%', 'height': '65%'},
                            {'left': '2%', 'right': '6%', 'top': '75%', 'height': '15%'},
                        ],
                        'xAxis': [
                            {
                                'type': 'category',
                                'data': dates,
                                'boundaryGap': False,
                                'axisLine': {'lineStyle': {'color': '#4B5563'}},
                                'splitLine': {'show': False},
                                'min': 'dataMin',
                                'max': 'dataMax',
                            },
                            {
                                'type': 'category',
                                'gridIndex': 1,
                                'data': dates,
                                'axisLabel': {'show': False},
                                'axisLine': {'show': False},
                            },
                        ],
                        'yAxis': [
                            {
                                'scale': True,
                                'position': 'right',
                                'splitArea': {
                                    'show': True,
                                    'areaStyle': {'color': ['rgba(255,255,255,0.01)', 'rgba(0,0,0,0)']},
                                },
                                'splitLine': {'lineStyle': {'color': '#1C2128', 'type': 'dashed'}},
                                'axisLabel': {'formatter': '${value}'},
                            },
                            {
                                'gridIndex': 1,
                                'splitNumber': 2,
                                'axisLabel': {'show': False},
                                'axisLine': {'show': False},
                                'axisTick': {'show': False},
                                'splitLine': {'show': False},
                            },
                        ],
                        'dataZoom': [
                            {
                                'type': 'inside',
                                'xAxisIndex': [0, 1],
                                'start': 0 if interval_code in ['1wk', '1mo'] else 60,
                                'end': 100,
                            },
                            {
                                'show': True,
                                'xAxisIndex': [0, 1],
                                'type': 'slider',
                                'bottom': '2%',
                                'start': 0 if interval_code in ['1wk', '1mo'] else 60,
                                'end': 100,
                                'textStyle': {'color': '#8B949E'},
                                'borderColor': '#1C2128',
                                'backgroundColor': '#0D1117',
                                'fillerColor': 'rgba(208,253,62,0.05)',
                                'handleStyle': {'color': '#D0FD3E'},
                            },
                        ],
                        'series': [
                            {
                                'name': ticker,
                                'type': 'candlestick',
                                'data': k_data,
                                'itemStyle': {
                                    'color': '#32D74B',
                                    'color0': '#FF453A',
                                    'borderColor': '#32D74B',
                                    'borderColor0': '#FF453A',
                                    'borderWidth': 1.5,
                                },
                                'z': 2,
                            },
                            {
                                'name': 'MA9',
                                'type': 'line',
                                'data': ma9,
                                'smooth': True,
                                'symbol': 'none',
                                'lineStyle': {'color': '#D0FD3E', 'width': 1.5, 'opacity': 0.8},
                                'z': 3,
                            },
                            {
                                'name': 'MA20',
                                'type': 'line',
                                'data': ma20,
                                'smooth': True,
                                'symbol': 'none',
                                'lineStyle': {'color': '#00BFFF', 'width': 1.5, 'opacity': 0.8},
                                'z': 3,
                            },
                            {
                                'name': 'BB Upper',
                                'type': 'line',
                                'data': bb_upper,
                                'smooth': True,
                                'symbol': 'none',
                                'lineStyle': {'color': 'rgba(255,255,255,0.2)', 'type': 'dashed'},
                                'z': 1,
                            },
                            {
                                'name': 'BB Lower',
                                'type': 'line',
                                'data': bb_lower,
                                'smooth': True,
                                'symbol': 'none',
                                'lineStyle': {'color': 'rgba(255,255,255,0.2)', 'type': 'dashed'},
                                'areaStyle': {'color': 'rgba(255,255,255,0.02)'},
                                'z': 1,
                            },
                            {
                                'name': 'Volume',
                                'type': 'bar',
                                'xAxisIndex': 1,
                                'yAxisIndex': 1,
                                'data': volumes,
                                'z': 2,
                            },
                        ],
                    })
                    chart_element.update()

                btn_1d.on_click(lambda: change_timeframe('1d', '6mo', btn_1d))
                btn_1w.on_click(lambda: change_timeframe('1wk', '2y', btn_1w))
                btn_1m.on_click(lambda: change_timeframe('1mo', '5y', btn_1m))

                change_timeframe('1d', '6mo', btn_1d)

        dialog.on('hide', lambda: clear_modal_state())
        dialog.open()
    except Exception:
        clear_modal_state()
        raise
