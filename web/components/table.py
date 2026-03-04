from nicegui import app, ui

from core.models import get_user_by_telegram
from web.i18n import tr

DOMAIN_MAP = {
    "AAPL": "apple.com",
    "MSFT": "microsoft.com",
    "GOOGL": "google.com",
    "AMZN": "amazon.com",
    "NVDA": "nvidia.com",
    "META": "meta.com",
    "TSLA": "tesla.com",
    "JNJ": "jnj.com",
    "V": "visa.com",
    "WMT": "walmart.com",
    "AVGO": "broadcom.com",
    "AMD": "amd.com",
    "PLTR": "palantir.com",
    "JPM": "jpmorganchase.com",
    "COST": "costco.com",
    "NFLX": "netflix.com",
    "SPY": "ssga.com",
    "VOO": "vanguard.com",
    "BTC-USD": "bitcoin.org",
    "ETH-USD": "ethereum.org",
}
LOGO_URL_CACHE = {}

T_GREEN = "#32D74B"
T_RED = "#FF453A"


def _ensure_sparkline_series(series, fallback_value=50.0):
    values = [float(v) for v in (series or []) if v is not None]
    if not values:
        return [fallback_value, fallback_value]
    if len(values) == 1:
        return [values[0], values[0]]
    return values


def get_logo_url_for_ticker(ticker: str) -> str:
    clean_ticker = (ticker or "").replace(".BK", "").upper()
    if clean_ticker in LOGO_URL_CACHE:
        return LOGO_URL_CACHE[clean_ticker]

    domain = DOMAIN_MAP.get(clean_ticker)
    if domain:
        # More reliable than hotlinking brand logos directly.
        url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    else:
        base_symbol = clean_ticker.split("-")[0] if "-" in clean_ticker else clean_ticker
        if (ticker or "").upper().endswith(".BK"):
            url = "https://www.google.com/s2/favicons?domain=set.or.th&sz=128"
        elif len(base_symbol) <= 1:
            url = f"https://ui-avatars.com/api/?name={clean_ticker or 'NA'}&background=111827&color=e5e7eb&bold=true"
        else:
            url = f"https://ui-avatars.com/api/?name={base_symbol}&background=0f172a&color=e2e8f0&bold=true"

    LOGO_URL_CACHE[clean_ticker] = url
    return url


def create_table_skeleton(row_count=3):
    with ui.column().classes("w-full mt-2 gap-3 md:gap-4"):
        for _ in range(row_count):
            with ui.row().classes(
                "w-full bg-[#12161E]/40 backdrop-blur-md border border-white/5 rounded-[24px] "
                "p-4 md:p-5 items-center justify-between flex-wrap sm:flex-nowrap gap-4 animate-pulse"
            ):
                with ui.row().classes("items-center gap-4 shrink-0 min-w-[200px]"):
                    ui.element("div").classes("w-12 h-12 md:w-14 md:h-14 rounded-full bg-white/5")
                    with ui.column().classes("gap-2"):
                        ui.element("div").classes("w-20 h-6 bg-white/10 rounded-md")
                        ui.element("div").classes("w-32 h-4 bg-white/5 rounded-md")

                ui.element("div").classes(
                    "flex-1 w-full sm:w-[140px] h-[50px] bg-gradient-to-r from-transparent via-white/5 to-transparent rounded-lg"
                )

                with ui.column().classes("items-end gap-2 shrink-0 min-w-[160px]"):
                    ui.element("div").classes("w-24 h-6 bg-white/10 rounded-md")
                    ui.element("div").classes("w-16 h-5 bg-white/5 rounded-md")


def create_portfolio_table(assets: list, on_edit, on_news, on_chart, ui_refs: dict = None, empty_state: dict = None):
    if ui_refs is None:
        ui_refs = {}

    currency = app.storage.user.get("currency", "USD")
    lang = app.storage.user.get("lang", "TH")
    curr_sym = "฿" if currency == "THB" else "$"
    curr_rate = 34.5 if currency == "THB" else 1.0

    tid = app.storage.user.get("telegram_id")
    user_info = get_user_by_telegram(tid) if tid else {}
    role = str(user_info.get("role", "free")).lower()
    is_pro_ai = role in ["pro", "admin"]

    with ui.column().classes("w-full mt-2 gap-3 md:gap-4"):
        if not assets:
            empty_state = empty_state or {}
            empty_title = str(empty_state.get("title") or tr("table.empty.title", lang))
            empty_subtitle = str(empty_state.get("subtitle") or tr("table.empty.subtitle", lang))
            empty_cta = str(empty_state.get("cta") or "")
            with ui.column().classes(
                "w-full items-center justify-center p-12 bg-[#12161E]/50 "
                "backdrop-blur-md rounded-[24px] border border-white/5 border-dashed"
            ):
                ui.icon("inventory_2", size="4xl").classes("text-gray-600 mb-4")
                ui.label(empty_title).classes("text-lg text-gray-400 font-bold text-center")
                ui.label(empty_subtitle).classes("text-sm text-gray-500 text-center")
                if empty_cta:
                    ui.label(empty_cta).classes("text-xs text-[#D0FD3E] font-bold text-center mt-2")
            return

        for asset in assets:
            ticker = asset.get("ticker", "N/A")
            shares = float(asset.get("shares", 0))
            base_cost = float(asset.get("avg_cost", 0))
            base_price = float(asset.get("last_price", 0))
            cost = base_cost * curr_rate
            last_price = base_price * curr_rate
            total_value = shares * last_price
            profit = (last_price - cost) * shares
            profit_pct = (profit / (cost * shares) * 100) if cost * shares > 0 else 0
            sparkline = asset.get("sparkline") or []
            spark_data = _ensure_sparkline_series(sparkline)
            is_chart_up = bool(asset.get("is_up", spark_data[-1] >= spark_data[0]))

            profit_color = T_GREEN if profit >= 0 else T_RED
            profit_sign = "+" if profit >= 0 else ""
            spark_color = T_GREEN if is_chart_up else T_RED

            with ui.row().classes(
                "w-full bg-[#12161E]/60 hover:bg-[#1C2128]/90 backdrop-blur-xl border border-white/5 "
                "hover:border-white/10 rounded-[24px] p-4 md:p-5 transition-all duration-300 hover:-translate-y-1 "
                "shadow-lg hover:shadow-2xl items-center justify-between flex-wrap sm:flex-nowrap gap-4 group cursor-pointer"
            ):
                with ui.row().classes("items-center gap-4 shrink-0 min-w-[200px]"):
                    logo_url = get_logo_url_for_ticker(ticker)
                    with ui.element("div").classes("relative"):
                        ui.element("div").classes(
                            "absolute inset-0 bg-white/10 rounded-full blur-md group-hover:blur-lg transition-all"
                        )
                        ui.image(logo_url).classes(
                            "w-12 h-12 md:w-14 md:h-14 rounded-full border-2 border-white/10 relative z-10 bg-[#0B0E14]"
                        )

                    with ui.column().classes("gap-1"):
                        ui.label(ticker).classes("text-xl md:text-2xl font-black text-white leading-none tracking-wide")
                        with ui.row().classes("items-center gap-1.5 mt-1"):
                            ui_refs[f"lbl_price_{ticker}"] = ui.label(
                                f"{tr('table.meta.price', lang)}: {curr_sym}{last_price:,.2f}"
                            ).classes("tabular-nums text-[10px] md:text-xs text-gray-300 bg-white/10 px-2 py-0.5 rounded-md font-bold")
                            ui.label(f"{tr('table.meta.avg', lang)}: {curr_sym}{cost:,.2f}").classes(
                                "text-[10px] md:text-xs text-gray-400 bg-white/5 px-2 py-0.5 rounded-md"
                            )
                            ui.label(f"{tr('table.meta.hold', lang)}: {shares:,.4f}").classes(
                                "text-[10px] md:text-xs text-gray-400 bg-white/5 px-2 py-0.5 rounded-md hidden sm:block"
                            )

                with ui.column().classes("flex-1 items-center justify-center w-full sm:w-auto h-16 min-w-[120px]"):
                    ui_refs[f"spark_{ticker}"] = ui.echart(
                        {
                            "animation": False,
                            "xAxis": {"show": False, "type": "category"},
                            "yAxis": {"show": False, "min": "dataMin", "max": "dataMax"},
                            "series": [
                                {
                                    "data": spark_data,
                                    "type": "line",
                                    "smooth": True,
                                    "showSymbol": False,
                                    "lineStyle": {
                                        "color": spark_color,
                                        "width": 3,
                                        "shadowColor": spark_color,
                                        "shadowBlur": 5,
                                    },
                                    "areaStyle": {"color": spark_color, "opacity": 0.15},
                                }
                            ],
                            "grid": {"left": 0, "right": 0, "top": 5, "bottom": 5},
                        }
                    ).classes("pointer-events-none").style("width: 140px; height: 50px; margin: auto;")

                with ui.column().classes("items-end gap-1 shrink-0 min-w-[160px]"):
                    ui_refs[f"val_{ticker}"] = ui.label(f"{curr_sym}{total_value:,.2f}").classes(
                        "tabular-nums text-xl md:text-2xl font-black leading-none tracking-tight drop-shadow-md"
                    ).style(f"color: {profit_color};")

                    pnl_string = f"{profit_sign}{curr_sym}{abs(profit):,.2f} ({profit_sign}{profit_pct:.2f}%)"
                    ui_refs[f"prof_{ticker}"] = ui.label(pnl_string).classes(
                        "tabular-nums text-xs md:text-sm font-bold px-2 py-0.5 rounded-md"
                    ).style(f"color: {profit_color}; background-color: {profit_color}10;")

                    with ui.row().classes(
                        "gap-1 mt-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 "
                        "md:pointer-events-none md:group-hover:pointer-events-auto transition-opacity duration-300"
                    ):
                        ui.button(icon="candlestick_chart", on_click=lambda t=ticker: on_chart(t)).props(
                            "flat dense round size=sm"
                        ).classes("text-gray-400 hover:text-[#D0FD3E] bg-white/5")
                        if is_pro_ai:
                            ui.button(icon="psychology", on_click=lambda t=ticker: on_news(t)).props(
                                "flat dense round size=sm"
                            ).classes("text-[#D0FD3E] bg-[#D0FD3E]/10")
                        else:
                            ui.button(
                                icon="lock",
                                on_click=lambda: ui.notify(tr("table.lock.ai", lang), type="warning"),
                            ).props("flat dense round size=sm").classes("text-gray-600 bg-white/5")
                        ui.button(icon="edit", on_click=lambda t=ticker: on_edit(t)).props(
                            "flat dense round size=sm"
                        ).classes("text-gray-400 hover:text-white bg-white/5")
