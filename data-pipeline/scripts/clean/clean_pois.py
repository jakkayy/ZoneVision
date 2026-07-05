import pandas as pd
import matplotlib
matplotlib.use('Agg') # ใช้ Non-interactive backend เพื่อความปลอดภัยสำหรับ headless server
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from pathlib import Path

# เพิ่มโฟลเดอร์ scripts เข้า sys.path เพื่อให้หาโมดูล utils เจอ
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import load_config, get_logger

# ตั้งค่า Logger และ Config
logger = get_logger("clean_pois")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
config = load_config()

input_file = str(BASE_DIR / "data" / "interim" / "bangkok_pois.json")
output_file = str(BASE_DIR / "data" / "processed" / "bangkok_pois_clean.csv")
report_dir = BASE_DIR / "reports" / "figures"

def main():
    logger.info("🧹 เริ่มต้นขั้นตอนทำความสะอาดข้อมูลจุดสนใจ (POIs Cleaning)...")
    if not os.path.exists(input_file):
        logger.error(f"ไม่พบไฟล์ดิบชั่วคราวที่ {input_file}")
        return

    df = pd.read_json(input_file)

    logger.info("สร้างและบันทึกภาพรายงานความสมบูรณ์ข้อมูลดิบ...")
    os.makedirs(str(report_dir), exist_ok=True)
    plt.figure(figsize=(10, 6))
    sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
    plt.title("Heatmap of Missing Values in Bangkok POIs Dataset")
    heatmap_path = str(report_dir / "pois_missing_values.png")
    plt.savefig(heatmap_path)
    plt.close()
    logger.info(f"บันทึกไฟล์ภาพ Heatmap สำเร็จ: {heatmap_path}")

    logger.info("จัดกลุ่มจัดประเภทตึก และคัดกรองพิกัด...")
    
    # 1. ระบบป้องกันคอลัมน์คีย์เวิร์ดดิบสูญหาย
    expected_cols = {
        'name': 'Unknown',
        'building': 'others',
        'latitude': None,
        'longitude': None
    }
    for col, default_val in expected_cols.items():
        if col not in df.columns:
            df[col] = default_val

    # 2. จัดกลุ่มประเภทตึกดิบจาก OSM ให้เข้าหมวดหมู่ง่ายต่อการประเมิน Demand
    def map_type(b_type):
        if b_type in ['apartments', 'residential']:
            return 'condo/apartment'
        elif b_type in ['office', 'commercial']:
            return 'office'
        elif b_type == 'retail':
            return 'mall'
        else:
            return 'others'

    df['type'] = df['building'].apply(map_type)

    # 3. อุดช่องว่างฟิลด์ชื่อ และคัดกรองเฉพาะคอลัมน์ที่ตั้งไว้ใน Config
    df['name'] = df['name'].fillna(df['type'])
    selected_cols = config.get("poi_columns", ["name", "type", "latitude", "longitude"])
    df_clean = df[selected_cols].copy()

    # 4. ล้างค่าพิกัดว่าง และล้างจุดซ้ำซ้อน
    df_clean = df_clean.dropna(subset=['latitude', 'longitude'])
    df_clean = df_clean.drop_duplicates(subset=['latitude', 'longitude'])

    logger.info(f"ล้างค่าซ้ำเสร็จสิ้น คงเหลือจุดสนใจความต้องการ (Demand) ในระบบ: {len(df_clean)} จุด")
    logger.info(f"แบ่งตามประเภทหมวดตึก: \n{df_clean['type'].value_counts()}")

    # บันทึกข้อมูลที่สะอาดลงProcessed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_clean.to_csv(output_file, index=False)
    logger.info(f"💾 🎉 ทำความสะอาดและบันทึกไฟล์ข้อมูลจุดสนใจพร้อมใช้งานสำเร็จ: {output_file}")

if __name__ == "__main__":
    main()