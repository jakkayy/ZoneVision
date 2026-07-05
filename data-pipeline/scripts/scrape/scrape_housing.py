import pandas as pd
import json
import os
import gc
import sys
from pathlib import Path

# เพิ่มโฟลเดอร์ scripts เข้า sys.path เพื่อให้หาโมดูล utils เจอ
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import load_config, get_logger

# โหลดคอนฟิกและตั้งค่า Logger
logger = get_logger("scrape_housing")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
config = load_config()

raw_file_path = os.getenv("HOUSING_FILEPATH", str(BASE_DIR / "data" / "raw" / "housing-infomation.csv"))
output_file_path = str(BASE_DIR / "data" / "interim" / "bangkok_housing.json")

def main():
    logger.info("กำลังโหลดข้อมูลสิ่งปลูกสร้างจดทะเบียนดิบ (Housing Raw Data)...")
    if not os.path.exists(raw_file_path):
        logger.error(f"ไม่พบไฟล์ข้อมูลดิบที่ {raw_file_path}")
        return

    # อ่านไฟล์ดิบด้วย Skiprows ตามคอนฟิก
    skip_rows = config.get("housing_skiprows", 4)
    df_raw = pd.read_csv(raw_file_path, skiprows=skip_rows)

    logger.info("คัดกรองข้อมูลสิ่งปลูกสร้างเฉพาะฟิลด์ที่กำหนด...")
    # เลือกเฉพาะแถวที่มีสถิติจริง (ค่ายอดรวมและเขตย่อยแถวสุดท้ายจะไม่นำมาคิด)
    df_filtered = df_raw.dropna(subset=['ลำดับที่']).copy()

    # บันทึกข้อมูลดิบลงคลัง interim
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    df_filtered.to_json(output_file_path, orient='records', force_ascii=False, indent=4)
    logger.info(f"บันทึกไฟล์ข้อมูลสิ่งปลูกสร้างระดับดิบเข้าคลังอินเตอร์ริมสำเร็จ: {output_file_path}")

    # คืนพื้นที่หน่วยความจำ
    del df_raw
    del df_filtered
    gc.collect()
    logger.info("ทำความสะอาดตัวแปรยักษ์ในแรมเรียบร้อย")

if __name__ == "__main__":
    main()