import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from pathlib import Path

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
    logger.info("เริ่มต้นขั้นตอนทำความสะอาดข้อมูลจุดสนใจ (POIs Cleaning)...")
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
    
    if 'type' in df.columns:
        df_clean = df.copy()
    else:
        # กรณีข้อมูลดิบจาก OSM ต้องทำการจัดหมวดหมู่ตึก
        expected_cols = {
            'name': 'Unknown',
            'building': 'others',
            'latitude': None,
            'longitude': None
        }
        for col, default_val in expected_cols.items():
            if col not in df.columns:
                df[col] = default_val

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
        df_clean = df.copy()

    # อุดช่องว่างฟิลด์ชื่อ และคัดกรองเฉพาะคอลัมน์ที่ตั้งไว้ใน Config
    df_clean['name'] = df_clean['name'].fillna(df_clean['type'])
    selected_cols = config.get("poi_columns", ["name", "type", "latitude", "longitude"])
    df_clean = df_clean[selected_cols].copy()

    df_clean = df_clean.dropna(subset=['latitude', 'longitude'])
    df_clean = df_clean.drop_duplicates(subset=['latitude', 'longitude'])

    logger.info(f"ล้างค่าซ้ำเสร็จสิ้น คงเหลือจุดสนใจความต้องการ (Demand) ในระบบ: {len(df_clean)} จุด")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_clean.to_csv(output_file, index=False)
    logger.info(f"ทำความสะอาดและบันทึกไฟล์ข้อมูลจุดสนใจพร้อมใช้งานสำเร็จ: {output_file}")

if __name__ == "__main__":
    main()