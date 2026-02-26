import json
import os
import requests
import customtkinter as ctk
from PIL import Image
from io import BytesIO
from datetime import datetime
import pandas as pd
import xml.etree.ElementTree as ET
import re
from config import *

# --- Data Management ---
def load_data(filepath):
    if not os.path.exists(filepath): return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

def save_data(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def clean_duplicates(data):
    seen, unique = set(), []
    for item in data:
        t = item['ticker']
        if t not in seen:
            unique.append(item); seen.add(t)
    return unique

# --- Formatting ---
def format_money(val, mode="USD", rate=35.0):
    symbol = "฿" if mode == "THB" else "$"
    mult = rate if mode == "THB" else 1.0
    return f"{symbol}{abs(val * mult):,.2f}"

def format_with_trend(val, mode="USD", rate=35.0, show_sign=False):
    symbol = "฿" if mode == "THB" else "$"
    mult = rate if mode == "THB" else 1.0
    final_val = val * mult
    icon = ""
    if show_sign:
        if val > 0: icon = "+"
        elif val < 0: icon = "-"
    return f"{icon}{symbol}{abs(final_val):,.2f}"

# --- Analytics & Calculation ---
def get_sector_distribution(portfolio, sector_map):
    dist = {}
    for item in portfolio:
        t = item['ticker']
        sector = "Others"
        for sec_name, tickers in sector_map.items():
            if t in tickers:
                sector = sec_name
                break
        val = item.get('value', item.get('cost', 0) * item.get('shares', 0))
        dist[sector] = dist.get(sector, 0) + val
    return dist

# --- [NEW] AI News Brain (Sentiment) ---
def analyze_sentiment(text):
    """ วิเคราะห์ Keyword เพื่อดูว่าเป็นข่าวดีหรือร้าย """
    text = text.lower()
    pos_words = ['surge', 'jump', 'gain', 'record', 'beat', 'bull', 'launch', 'approve', 'dividend', 'profit', 'high', 'strong', 'growth', 'buy', 'up']
    neg_words = ['drop', 'fall', 'plunge', 'miss', 'bear', 'lose', 'lawsuit', 'cut', 'down', 'crash', 'warn', 'weak', 'sell', 'risk']
    
    score = 0
    for w in pos_words: 
        if w in text: score += 1
    for w in neg_words: 
        if w in text: score -= 1
        
    if score > 0: return "Positive", COLORS["success"]  # เขียว
    elif score < 0: return "Negative", COLORS["danger"]   # แดง
    return "Neutral", "gray"                              # เทา

# --- [NEW] Technical Scanner (RSI) ---
# --- ในไฟล์ core.py ---

def get_technical_signal(prices_list):
    """ คำนวณ RSI 14-period พร้อม Emoji และสีที่สื่อความหมาย """
    if not prices_list or len(prices_list) < 15: 
        return "Neutral", "gray", 0
    
    try:
        series = pd.Series(prices_list)
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        
        if pd.isna(val): return "Neutral", "gray", 0
        
        # --- Logic ใหม่: ใส่ Emoji และปรับสี ---
        if val >= 75:
            return f"EXTREME🔥({val:.0f})", COLORS["danger"], val  # ร้อนแรงมาก ระวัง!
        elif val >= 70:
            return f"Overbought⚠️({val:.0f})", COLORS["warning"], val # เริ่มแพง
        elif val <= 25:
            return f"Oversold💎({val:.0f})", COLORS["gold"], val    # ถูกมาก เพชรเม็ดงาม
        elif val <= 30:
            return f"Oversold🌈({val:.0f})", COLORS["success"], val # น่าเก็บ
        else:
            return f"Neutral🪐({val:.0f})", "gray", val
            
    except: 
        return "N/A", "gray", 0

# --- Logo & RSS Loader ---
def load_logo(ticker):
    ticker = ticker.upper().replace("-", ".")
    if not os.path.exists("logos"): os.makedirs("logos")
    local_path = f"logos/{ticker}.png"
    
    if os.path.exists(local_path):
        try: return ctk.CTkImage(Image.open(local_path), size=(32, 32))
        except: pass

    domain = DOMAIN_MAP.get(ticker)
    urls = []
    if domain: urls.append(f"https://logo.clearbit.com/{domain}")
    else:
        urls.append(f"https://logo.clearbit.com/{ticker.lower()}.com")
        urls.append(f"https://ui-avatars.com/api/?name={ticker}&background=random&color=fff&size=128")

    for url in urls:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=3)
            if r.status_code == 200:
                img_data = BytesIO(r.content)
                img = Image.open(img_data)
                img.save(local_path)
                return ctk.CTkImage(img, size=(32, 32))
        except: continue
    return None

# --- ในไฟล์ core.py ---

def fetch_rss(ticker):
    symbol = ticker.replace('.', '-')
    # ลองดึงจาก Yahoo Finance
    url = f"https://finance.yahoo.com/rss/headline?s={symbol}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        
        # ล้าง Namespace ที่มักทำให้ parse ยาก
        content = r.content.decode('utf-8')
        content = re.sub(' xmlns="[^"]+"', '', content, count=1)
        
        root = ET.fromstring(content)
        items = []
        
        for item in root.findall('.//item')[:10]: # ดึง 10 ข่าว
            title = item.find('title').text
            link = item.find('link').text.strip()
            pub = item.find('pubDate').text
            date_str = pub[:16] if pub else "Recent"
            
            # AI Sentiment Analysis
            sent_txt, sent_col = analyze_sentiment(title)
            
            # --- Image Extraction Logic (Improved) ---
            img_url = None
            
            # 1. ลองหาจาก media:content (ถ้า namespace ยังอยู่)
            # (ข้ามไปเพราะเราลบ namespace แล้ว แต่มักจะอยู่ใน tag ลูก)
            
            # 2. ลองหาจาก Description โดยใช้ Regex (วิธีที่ได้ผลสุดกับ Yahoo)
            description = ""
            desc_tag = item.find('description')
            if desc_tag is not None:
                description = desc_tag.text or ""
                # หา tag <img src="...">
                match = re.search(r'<img[^>]+src="([^">]+)"', description)
                if match:
                    img_url = match.group(1)
            
            # 3. ถ้าไม่มีรูป ให้ใช้ None (เดี๋ยว UI จะใส่ Logo แทน)
            
            items.append({
                'title': title, 
                'link': link, 
                'date': date_str,
                'sentiment': sent_txt,
                'sentiment_color': sent_col,
                'image_url': img_url
            })
            
        return items
    except Exception as e: 
        print(f"RSS Error: {e}")
        return []

# --- FX & History ---
def get_fx():
    try: return requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()['rates']['THB']
    except: return 35.0

def update_history_log(filepath, total_val, dca_val, div_val):
    new_entry = {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "val": total_val, "dca": dca_val, "div": div_val}
    data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding='utf-8') as f: data = json.load(f)
        except: pass
    if data:
        last = data[-1]
        t_last = datetime.strptime(last['date'], "%Y-%m-%d %H:%M")
        t_now = datetime.now()
        if (t_now - t_last).total_seconds() < 60 and abs(last['val'] - total_val) < 0.1: return
    data.append(new_entry)
    with open(filepath, "w", encoding='utf-8') as f: json.dump(data[-5000:], f, indent=4)

# --- Telegram Notifications ---
def send_price_alert(token, chat_id, ticker, current_price, target_price):
    msg = f"🔔 *Price Alert: {ticker}*\nCurrent: ${current_price:,.2f}\nTarget: ${target_price:,.2f}\nCondition Met!"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

def send_daily_report(token, chat_id, portfolio, market_data, indices, history_file):
    total, cost, dca_val, div_val = 0, 0, 0, 0
    div_tickers = PORTFOLIO_GROUPS.get("DIVIDEND", [])
    
    for item in portfolio:
        t = item['ticker']
        p = market_data.get(t, item['cost'])
        val = p * item['shares']
        total += val
        cost += item['cost'] * item['shares']
        
        is_div = (item.get('group') == 'DIVIDEND') or (t in div_tickers)
        if is_div: div_val += val
        else: dca_val += val

    profit = total - cost
    pct = (profit/cost*100) if cost>0 else 0
    
    # Movers (Best/Worst Performers)
    movers = []
    for item in portfolio:
        t = item['ticker']
        curr = market_data.get(t, 0)
        c = item['cost']
        if curr > 0 and c > 0:
            chg = (curr - c) / c * 100
            movers.append((t, chg))
    
    best = max(movers, key=lambda x: x[1]) if movers else ("-", 0)
    worst = min(movers, key=lambda x: x[1]) if movers else ("-", 0)

    # [FIXED] แปลงชื่อ Market Indices ให้เป็นภาษาคน + เพิ่ม Emoji
    market_map = {
        "^GSPC": "🇺🇸 S&P 500",
        "^IXIC": "💻 Nasdaq",
        "GC=F": "🥇 Gold",
        "THB=X": "🇹🇭 Exchange Rate"
    }

    m_lines = []
    for k, v in indices.items():
        name = market_map.get(k, k) # ถ้ามีชื่อใน map ให้ใช้ชื่อใหม่ ถ้าไม่มีใช้ชื่อเดิม
        if k == "THB=X":
            m_lines.append(f"{name}: {v:.2f}฿")
        else:
            m_lines.append(f"{name}: {v:,.0f}")
            
    m_txt = "\n".join(m_lines)

    msg = (
        f"☀️ *Morning Report* ☀️\n"
        f"📅 {datetime.now().strftime('%d %b %Y')}\n\n"
        f"💰 *Net Worth:* ${total:,.2f}\n"
        f"📈 *Profit:* ${profit:,.2f} ({pct:+.2f}%)\n"
        f"------------------\n"
        f"🚀 *Growth:* ${dca_val:,.2f}\n"
        f"💵 *Dividend:* ${div_val:,.2f}\n"
        f"------------------\n"
        f"🏆 Best: {best[0]} ({best[1]:+.1f}%)\n"
        f"📉 Worst: {worst[0]} ({worst[1]:+.1f}%)\n"
        f"------------------\n"
        f"🌍 *Markets:*\n{m_txt}"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except Exception as e: print(f"TG Error: {e}")