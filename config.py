import platform
import os
from dotenv import load_dotenv
# เพิ่ม 1 บรรทัดนี้ลงใน config.py
GEMINI_API_KEY = "AIzaSyBCzf-sxJ_LWuwmnkwZduxnC24FpOkfHUs"  # ปล่อยว่างไว้ก่อนได้ถ้ายังไม่มี

load_dotenv()

# --- Configuration ---
MAIN_FONT = "Segoe UI" if platform.system() == "Windows" else "Helvetica"
BOLD_FONT = (MAIN_FONT, 12, "bold")
HEADER_FONT = (MAIN_FONT, 26, "bold")
SUB_FONT = (MAIN_FONT, 11)

# [Telegram Settings]
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DIVIDEND_TAX_RATE = 0.15 

TARGETS_DCA = { "VOO": 30.0, "SCHD": 20.0, "BRK.B": 15.0, "MSFT": 12.5, "NVDA": 12.5, "GOOGL": 10.0 }
TARGETS_DIV = { "JEPQ": 50.0, "O": 50.0 }

# --- THEME COLORS ---
COLORS = {
    "bg": "#0B0E14",             
    "header": "#11141C",         
    "card": "#161B22",           
    "card_hover": "#21262D", 
    "surface": "#252B3A",        
    "input_bg": "#0D1117",       
    
    "text": "#F0F6FC",           
    "text_sub": "#8B949E",       
    
    "border": "#30363D",      
    "border_light": "#484F58",
    
    "accent": "#07A74F",         
    "success": "#00D668",        
    "danger": "#DA3633",         
    "warning": "#D29922", 
    "gold": "#FFD700",           
    
    "tab_bg": "#21262D",         
    "tab_hover": "#30363D",      
    "tab_selected": "#00D668",   
    "tab_text": "#FFFFFF",       
    "tab_text_active": "#000000",

    "chart_dca": ['#00D668', '#34D399', '#6EE7B7', '#10B981', '#059669', '#047857'],
    "chart_div": ['#F472B6', '#EC4899', '#DB2777', '#BE185D', '#9D174D', '#831843'],
    "chart_line": "#58A6FF",     
    "chart_fill": "#1F6FEB",     

    "sec_tech": "#00D668", "sec_fin": "#58A6FF", "sec_health": "#F472B6", "sec_cons": "#D29922", "sec_other": "#8B949E"
}

PORTFOLIO_GROUPS = {
    "DCA": ["VOO", "BRK.B", "NVDA", "GOOGL", "MSFT", "SCHD", "QQQ", "VTI", "TSLA", "AAPL"], 
    "DIVIDEND": ["JEPQ", "O", "JEPI", "VNQ", "MAIN", "MO"] 
}

SECTOR_MAP = {
    "Technology": ["NVDA", "MSFT", "GOOGL", "AAPL", "TSLA", "QQQ"],
    "Financial": ["BRK.B", "JEPQ", "JEPI", "MAIN"],
    "Real Estate": ["O", "VNQ"],
    "Consumer": ["MO", "KO", "PEP"],
    "ETF": ["VOO", "VTI", "SCHD"]
}

DOMAIN_MAP = {
    "VOO": "vanguard.com", "SCHD": "schwab.com", 
    "BRK.B": "bhspecialty.com", "BRK-B": "bhspecialty.com",
    "JEPQ": "jpmorgan.com", "MSFT": "microsoft.com", "NVDA": "nvidia.com", 
    "GOOGL": "google.com", "O": "realtyincome.com"
}

TEXTS = {
    "TH": {
        "net_val": "มูลค่าพอร์ตลงทุน", 
        "add_btn": "+ เพิ่มสินทรัพย์", 
        "tab_all": "ภาพรวม", "tab_dca": "เติบโต (DCA)", "tab_div": "ปันผล (Div)", 
        
        # Analytics & Sort
        "reb_title": "วิเคราะห์พอร์ต", 
        "sort_title": "จัดเรียงลำดับ",
        "sort_manual": "ลากวาง (Manual)", "sort_val": "มูลค่ามากสุด", "sort_share": "หุ้นมากสุด",
        "btn_save_order": "บันทึกลำดับ",

        # Edit Dialog
        "dialog_edit": "แก้ไขรายการ", "dialog_add": "เพิ่มรายการ",
        "lbl_ticker": "ชื่อย่อหุ้น (Ticker)", "lbl_shares": "จำนวนหุ้น", "lbl_cost": "ราคาทุนเฉลี่ย",
        "lbl_alert": "แจ้งเตือนราคา", "lbl_group": "กลุ่ม",
        "btn_check": "เช็คราคาปัจจุบัน", "btn_supp": "ตั้งเตือนที่แนวรับ",
        "btn_save": "บันทึกข้อมูล", "btn_delete": "ลบรายการ",

        # Dividend & News
        "div_title": "ปันผลรับ",
        "news_title": "ข่าวสาร",
        "news_read": "อ่านข่าว"
    },
    "EN": {
        "net_val": "Net Worth", 
        "add_btn": "+ Add Asset", 
        "tab_all": "Overview", "tab_dca": "Growth", "tab_div": "Dividend",
        
        # Analytics & Sort
        "reb_title": "Analytics", 
        "sort_title": "Sort Assets",
        "sort_manual": "Manual Drag", "sort_val": "By Value", "sort_share": "By Shares",
        "btn_save_order": "Save Order",

        # Edit Dialog
        "dialog_edit": "Edit Asset", "dialog_add": "Add Asset",
        "lbl_ticker": "Ticker Symbol", "lbl_shares": "Shares", "lbl_cost": "Avg Cost",
        "lbl_alert": "Alert Price", "lbl_group": "Group",
        "btn_check": "Check Price", "btn_supp": "Set Alert to Support",
        "btn_save": "Save Asset", "btn_delete": "Delete Asset",

        # Dividend & News
        "div_title": "Dividends",
        "news_title": "News",
        "news_read": "Read"
    }
}