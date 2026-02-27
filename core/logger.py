import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name="Apexify", log_file="apexify.log"):
    """ตั้งค่าระบบ Logger มาตรฐานสำหรับโปรเจกต์"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # ป้องกันการสร้าง Handler ซ้ำซ้อน
    if not logger.handlers:
        # รูปแบบข้อความ Log: [เวลา] - [ชื่อ] - [ระดับ] - ข้อความ
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 1. แสดง Log ออกทางหน้าจอ (Console) เฉพาะระดับ INFO ขึ้นไป
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 2. บันทึก Log ลงไฟล์ เฉพาะระดับ DEBUG ขึ้นไป (เก็บไฟล์ละ 5MB สูงสุด 5 ไฟล์)
        try:
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=5 * 1024 * 1024, # 5 MB
                backupCount=5, 
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"⚠️ ไม่สามารถสร้างไฟล์ Log ได้: {e}")
            
    return logger

# สร้าง Instance หลักไว้ให้ไฟล์อื่นเรียกใช้ (from core.logger import logger)
logger = setup_logger()
