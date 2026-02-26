# ไฟล์: backend/api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import core  # เรียกใช้สูตรคำนวณเดิมของคุณ

app = FastAPI()

# อนุญาตให้เว็บเข้าถึงข้อมูลได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PORTFOLIO_FILE = "my_portfolio.json"
HISTORY_FILE = "portfolio_history.json"

# โมเดลรับคำถาม Chat
class ChatRequest(BaseModel):
    message: str

@app.get("/")
def check_status():
    return {"status": "ok", "message": "Apex Backend is running!"}

@app.get("/api/portfolio")
def get_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return {"status": "error", "message": "No portfolio file"}
    
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # คำนวณยอดรวม (ใช้ Logic เดิมของคุณ)
    total_cost = sum([d['cost'] * d['shares'] for d in data])
    # จำลองราคาปัจจุบัน (ของจริงจะใช้ yfinance ใน core.py)
    total_value = sum([d.get('last_price', d['cost']*1.05) * d['shares'] for d in data])
    profit = total_value - total_cost
    
    return {
        "summary": {
            "total_cost": total_cost,
            "total_value": total_value,
            "profit": profit,
            "profit_percent": (profit/total_cost)*100 if total_cost > 0 else 0
        },
        "assets": data
    }

@app.get("/api/history")
def get_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f) # ส่งข้อมูลประวัติให้กราฟ

@app.post("/api/chat")
def chat_ai(req: ChatRequest):
    # ตรงนี้ใส่ Logic Gemini ได้เลย
    return {"reply": f"AI ได้รับข้อความว่า: {req.message} (กำลังวิเคราะห์พอร์ต...)"}