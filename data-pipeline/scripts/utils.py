import json
import logging
from pathlib import Path

# หาพาธรากหลักของ data-pipeline (ZoneVision/data-pipeline)
BASE_DIR = Path(__file__).resolve().parent.parent

def load_config():
    """โหลดไฟล์การตั้งค่าระบบจาก config.json"""
    config_path = BASE_DIR / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"ไม่พบไฟล์คอนฟิกที่ {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_logger(name):
    """สร้างและส่งกลับ Object Logger ที่มีการฟอร์แมตข้อความแจ้งเตือนอย่างเป็นระเบียบ"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # แสดงผลในรูปแบบ: [เวลา] - [ชื่อสคริปต์] - [สถานะ] - [ข้อความ]
        formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s', datefmt='%H:%M:%S')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger
