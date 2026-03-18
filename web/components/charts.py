from nicegui import ui, app
from core.models import get_user_by_telegram
from web.i18n import tr
from services.yahoo_finance import calculate_bollinger_bands, calculate_rsi_series, calculate_macd_series
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

    state = {
        'interval': '1d',
        'period': '6mo',
        'show_rsi': False,
        'show_macd': False,
        'raw_data': None,
    }

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
            # ── Header ────────────────────────────────────────────────────────
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
                # ── Toolbar ───────────────────────────────────────────────────
                with ui.row().classes('w-full justify-between items-center mb-3 z-10 relative flex-wrap gap-2'):
                    with ui.row().classes('gap-2 items-center flex-wrap'):
                        ui.label('Interactive TradingView Style').classes(
                            'text-[10px] font-bold text-gray-500 tracking-widest uppercase '
                            'bg-[#161B22] px-3 py-1 rounded-md border border-white/5'
                        )
                        with ui.row().classes('gap-3 text-[10px] font-black tracking-wider'):
                            ui.label('MA 9').classes('text-[#D0FD3E]')
                            ui.label('MA 20').classes('text-[#00BFFF]')
                        # Indicator toggle buttons
                        btn_rsi = ui.button('RSI').props('flat size=sm').classes(
                            'text-gray-400 hover:text-[#FF9F0A] font-bold '
                            'border border-white/10 rounded-md transition-all px-2'
                        )
                        btn_macd = ui.button('MACD').props('flat size=sm').classes(
                            'text-gray-400 hover:text-[#AF52DE] font-bold '
                            'border border-white/10 rounded-md transition-all px-2'
                        )

                    # Timeframe buttons
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

                # ── Chart ────────────────────────────────────────────────────
                chart_element = ui.echart({}).classes('w-full rounded-xl overflow-hidden')
                chart_element.style('height: 600px')

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

                def _build_chart_options(raw_data, interval_code):
                    show_rsi = state['show_rsi']
                    show_macd = state['show_macd']
                    n_extra = (1 if show_rsi else 0) + (1 if show_macd else 0)

                    dates = [d['date'] for d in raw_data]
                    k_data = [[d['open'], d['close'], d['low'], d['high']] for d in raw_data]
                    closes = [d['close'] for d in raw_data]

                    # MA 9/20
                    ma9, ma20 = [], []
                    for i in range(len(k_data)):
                        ma9.append(round(sum([x[1] for x in k_data[i - 8:i + 1]]) / 9, 2) if i >= 8 else '-')
                        ma20.append(round(sum([x[1] for x in k_data[i - 19:i + 1]]) / 20, 2) if i >= 19 else '-')

                    bb_upper, _, bb_lower = calculate_bollinger_bands(closes)

                    volumes = []
                    for d in raw_data:
                        color = '#32D74B' if d['close'] >= d['open'] else '#FF453A'
                        volumes.append({'value': d['volume'], 'itemStyle': {'color': color, 'opacity': 0.7}})

                    # ── Grid layout positions ─────────────────────────────────
                    extra1_top = extra_h = extra2_top = '0%'
                    if n_extra == 0:
                        candle_top, candle_h = '5%', '65%'
                        vol_top, vol_h = '75%', '15%'
                        slider_bottom = '2%'
                        chart_height = '600px'
                    elif n_extra == 1:
                        candle_top, candle_h = '4%', '47%'
                        vol_top, vol_h = '54%', '9%'
                        extra1_top, extra_h = '66%', '19%'
                        slider_bottom = '2%'
                        chart_height = '740px'
                    else:  # 2
                        candle_top, candle_h = '3%', '34%'
                        vol_top, vol_h = '40%', '8%'
                        extra1_top, extra_h = '51%', '15%'
                        extra2_top = '69%'
                        slider_bottom = '2%'
                        chart_height = '880px'

                    chart_element.style(f'height: {chart_height}')

                    grids = [
                        {'left': '2%', 'right': '6%', 'top': candle_top, 'height': candle_h},
                        {'left': '2%', 'right': '6%', 'top': vol_top, 'height': vol_h},
                    ]
                    x_axes = [
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
                    ]
                    y_axes = [
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
                    ]
                    all_x_indices = [0, 1]

                    # Base series (always shown)
                    series = [
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
                            'name': 'MA9', 'type': 'line', 'data': ma9,
                            'smooth': True, 'symbol': 'none',
                            'lineStyle': {'color': '#D0FD3E', 'width': 1.5, 'opacity': 0.8}, 'z': 3,
                        },
                        {
                            'name': 'MA20', 'type': 'line', 'data': ma20,
                            'smooth': True, 'symbol': 'none',
                            'lineStyle': {'color': '#00BFFF', 'width': 1.5, 'opacity': 0.8}, 'z': 3,
                        },
                        {
                            'name': 'BB Upper', 'type': 'line', 'data': bb_upper,
                            'smooth': True, 'symbol': 'none',
                            'lineStyle': {'color': 'rgba(255,255,255,0.2)', 'type': 'dashed'}, 'z': 1,
                        },
                        {
                            'name': 'BB Lower', 'type': 'line', 'data': bb_lower,
                            'smooth': True, 'symbol': 'none',
                            'lineStyle': {'color': 'rgba(255,255,255,0.2)', 'type': 'dashed'},
                            'areaStyle': {'color': 'rgba(255,255,255,0.02)'}, 'z': 1,
                        },
                        {
                            'name': 'Volume', 'type': 'bar',
                            'xAxisIndex': 1, 'yAxisIndex': 1,
                            'data': volumes, 'z': 2,
                        },
                    ]

                    # ── RSI panel ──────────────────────────────────────────────
                    if show_rsi:
                        rsi_series_data = calculate_rsi_series(closes)
                        rsi_grid_idx = len(grids)
                        grids.append({'left': '2%', 'right': '6%', 'top': extra1_top, 'height': extra_h})
                        all_x_indices.append(rsi_grid_idx)
                        x_axes.append({
                            'type': 'category',
                            'gridIndex': rsi_grid_idx,
                            'data': dates,
                            'axisLabel': {'show': False},
                            'axisLine': {'lineStyle': {'color': '#2D3748'}},
                            'splitLine': {'show': False},
                        })
                        rsi_y_idx = len(y_axes)
                        y_axes.append({
                            'gridIndex': rsi_grid_idx,
                            'min': 0, 'max': 100,
                            'position': 'right',
                            'splitNumber': 2,
                            'axisLabel': {'color': '#FF9F0A', 'fontSize': 9,
                                         'formatter': '{value}'},
                            'splitLine': {'show': False},
                            'axisLine': {'show': False},
                            'axisTick': {'show': False},
                        })
                        series.append({
                            'name': 'RSI(14)',
                            'type': 'line',
                            'xAxisIndex': rsi_grid_idx,
                            'yAxisIndex': rsi_y_idx,
                            'data': rsi_series_data,
                            'smooth': False,
                            'symbol': 'none',
                            'lineStyle': {'color': '#FF9F0A', 'width': 1.5},
                            'z': 2,
                            'markLine': {
                                'silent': True,
                                'symbol': ['none', 'none'],
                                'label': {
                                    'show': True,
                                    'position': 'insideEndTop',
                                    'fontSize': 9,
                                    'color': '#8B949E',
                                },
                                'lineStyle': {'type': 'dashed', 'color': 'rgba(255,255,255,0.15)'},
                                'data': [
                                    {'yAxis': 70, 'name': '70', 'lineStyle': {'color': '#FF453A', 'opacity': 0.4}},
                                    {'yAxis': 30, 'name': '30', 'lineStyle': {'color': '#32D74B', 'opacity': 0.4}},
                                ],
                            },
                        })

                    # ── MACD panel ─────────────────────────────────────────────
                    if show_macd:
                        macd_line_data, signal_data, hist_data = calculate_macd_series(closes)
                        macd_grid_idx = len(grids)
                        macd_top = extra1_top if not show_rsi else extra2_top
                        grids.append({'left': '2%', 'right': '6%', 'top': macd_top, 'height': extra_h})
                        all_x_indices.append(macd_grid_idx)
                        x_axes.append({
                            'type': 'category',
                            'gridIndex': macd_grid_idx,
                            'data': dates,
                            'axisLabel': {'show': False},
                            'axisLine': {'lineStyle': {'color': '#2D3748'}},
                            'splitLine': {'show': False},
                        })
                        macd_y_idx = len(y_axes)
                        y_axes.append({
                            'gridIndex': macd_grid_idx,
                            'scale': True,
                            'position': 'right',
                            'splitNumber': 2,
                            'axisLabel': {'color': '#AF52DE', 'fontSize': 9},
                            'splitLine': {'show': False},
                            'axisLine': {'show': False},
                            'axisTick': {'show': False},
                        })
                        # Histogram with green/red coloring
                        hist_colored = []
                        for v in hist_data:
                            if v == '-':
                                hist_colored.append({'value': '-', 'itemStyle': {'color': 'transparent'}})
                            else:
                                hist_colored.append({
                                    'value': v,
                                    'itemStyle': {
                                        'color': '#32D74B' if v >= 0 else '#FF453A',
                                        'opacity': 0.65,
                                    },
                                })
                        series.append({
                            'name': 'MACD Hist',
                            'type': 'bar',
                            'xAxisIndex': macd_grid_idx,
                            'yAxisIndex': macd_y_idx,
                            'data': hist_colored,
                            'z': 1,
                        })
                        series.append({
                            'name': 'MACD',
                            'type': 'line',
                            'xAxisIndex': macd_grid_idx,
                            'yAxisIndex': macd_y_idx,
                            'data': macd_line_data,
                            'smooth': False,
                            'symbol': 'none',
                            'lineStyle': {'color': '#AF52DE', 'width': 1.5},
                            'z': 3,
                        })
                        series.append({
                            'name': 'Signal',
                            'type': 'line',
                            'xAxisIndex': macd_grid_idx,
                            'yAxisIndex': macd_y_idx,
                            'data': signal_data,
                            'smooth': False,
                            'symbol': 'none',
                            'lineStyle': {'color': '#FF9F0A', 'width': 1.2, 'type': 'dashed'},
                            'z': 3,
                        })

                    zoom_start = 0 if interval_code in ['1wk', '1mo'] else 60
                    return {
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
                        'grid': grids,
                        'xAxis': x_axes,
                        'yAxis': y_axes,
                        'dataZoom': [
                            {
                                'type': 'inside',
                                'xAxisIndex': all_x_indices,
                                'start': zoom_start,
                                'end': 100,
                            },
                            {
                                'show': True,
                                'xAxisIndex': all_x_indices,
                                'type': 'slider',
                                'bottom': slider_bottom,
                                'start': zoom_start,
                                'end': 100,
                                'textStyle': {'color': '#8B949E'},
                                'borderColor': '#1C2128',
                                'backgroundColor': '#0D1117',
                                'fillerColor': 'rgba(208,253,62,0.05)',
                                'handleStyle': {'color': '#D0FD3E'},
                            },
                        ],
                        'series': series,
                    }

                def _refresh_chart():
                    """Re-render chart from cached data (no re-fetch)."""
                    raw_data = state.get('raw_data')
                    if raw_data:
                        opts = _build_chart_options(raw_data, state['interval'])
                        chart_element.options.clear()
                        chart_element.options.update(opts)
                        chart_element.update()

                def change_timeframe(interval_code, period_code, active_btn):
                    if not is_paid_user and interval_code in ['1wk', '1mo']:
                        ui.notify(tr('charts.locked_timeframe', lang), type='warning')
                        return

                    state['interval'] = interval_code
                    state['period'] = period_code

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
                        set_status(tr('charts.data_feed_unavailable', lang, ticker=ticker, interval=interval_code))
                        render_empty_chart(tr('charts.data_feed_unavailable_short', lang))
                        ui.notify(tr('charts.load_failed', lang, ticker=ticker, interval=interval_code), type='warning')
                        return

                    state['raw_data'] = raw_data
                    set_status('')
                    opts = _build_chart_options(raw_data, interval_code)
                    chart_element.options.clear()
                    chart_element.options.update(opts)
                    chart_element.update()

                def toggle_rsi():
                    state['show_rsi'] = not state['show_rsi']
                    if state['show_rsi']:
                        btn_rsi.props('unelevated remove=flat').classes(
                            replace='bg-[#FF9F0A]/20 text-[#FF9F0A] font-black border border-[#FF9F0A]/50 rounded-md'
                        )
                    else:
                        btn_rsi.props('flat remove=unelevated').classes(
                            replace='text-gray-400 hover:text-[#FF9F0A] font-bold border border-white/10 rounded-md'
                        )
                    _refresh_chart()

                def toggle_macd():
                    state['show_macd'] = not state['show_macd']
                    if state['show_macd']:
                        btn_macd.props('unelevated remove=flat').classes(
                            replace='bg-[#AF52DE]/20 text-[#AF52DE] font-black border border-[#AF52DE]/50 rounded-md'
                        )
                    else:
                        btn_macd.props('flat remove=unelevated').classes(
                            replace='text-gray-400 hover:text-[#AF52DE] font-bold border border-white/10 rounded-md'
                        )
                    _refresh_chart()

                btn_rsi.on_click(toggle_rsi)
                btn_macd.on_click(toggle_macd)
                btn_1d.on_click(lambda: change_timeframe('1d', '6mo', btn_1d))
                btn_1w.on_click(lambda: change_timeframe('1wk', '2y', btn_1w))
                btn_1m.on_click(lambda: change_timeframe('1mo', '5y', btn_1m))

                change_timeframe('1d', '6mo', btn_1d)

        dialog.on('hide', lambda: clear_modal_state())
        dialog.open()
    except Exception:
        clear_modal_state()
        raise
