import subprocess
import time
from datetime import datetime

def auto_push():
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] 🚀 Starting Auto-Sync...")
        
        try:
            # 1. เพิ่มไฟล์ทั้งหมด
            subprocess.run(["git", "add", "."], check=True)
            
            # 2. บันทึกพร้อมเวลา
            commit_message = f"Auto-sync at {now}"
            # ใช้ stdout=subprocess.DEVNULL เพื่อไม่ให้ข้อความ git commit รกหน้าจอ
            subprocess.run(["git", "commit", "-m", commit_message], capture_output=True)
            
            # 3. ดันขึ้น GitHub
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            print(f"[{now}] ✅ Cloud Updated! Next sync in 3 minutes...")
            
        except Exception as e:
            print(f"[{now}] ❌ Sync failed (Check internet or Git status)")

        # ⏳ รอ 180 วินาที (3 นาที)
        time.sleep(180)

if __name__ == "__main__":
    auto_push()