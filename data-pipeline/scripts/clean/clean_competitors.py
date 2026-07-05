import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from pathlib import Path

# เพิ่มโฟลเดอร์ scripts เข้า sys.path เพื่อให้หาโมดูล utils เจอ
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import load_config, get_logger

# ตั้งค่า Logger และ Config
logger = get_logger("clean_competitors")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
config = load_config()

input_file = str(BASE_DIR / "data" / "interim" / "bangkok_competitors.json")
output_file = str(BASE_DIR / "data" / "processed" / "bangkok_competitors_clean.csv")
report_dir = BASE_DIR / "reports" / "figures"

def main():
    logger.info("เริ่มต้นขั้นตอนทำความสะอาดข้อมูลคู่แข่งร้านอาหาร (Competitors Cleaning)...")
    if not os.path.exists(input_file):
        logger.error(f"ไม่พบไฟล์ดิบชั่วคราวที่ {input_file}")
        return

    df = pd.read_json(input_file)

    logger.info("สร้างและบันทึกภาพรายงานความสมบูรณ์ข้อมูลดิบ...")
    os.makedirs(str(report_dir), exist_ok=True)
    plt.figure(figsize=(10, 6))
    sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
    plt.title("Heatmap of Missing Values in Bangkok Competitors Dataset")
    heatmap_path = str(report_dir / "competitors_missing_values.png")
    plt.savefig(heatmap_path)
    plt.close()
    logger.info(f"บันทึกไฟล์ภาพ Heatmap สำเร็จ: {heatmap_path}")

    logger.info("กรองทำความสะอาดข้อมูลคู่แข่งทางธุรกิจ...")
    
    if 'amenity_type' in df.columns:
        df = df.rename(columns={'amenity_type': 'amenity'})
        
    expected_cols = {
        'name': 'Unknown Business',
        'amenity': 'restaurant',
        'cuisine': 'general',
        'latitude': None,
        'longitude': None
    }
    for col, default_val in expected_cols.items():
        if col not in df.columns:
            df[col] = default_val

    # ทำการอุดรอยรั่วฟิลด์ที่เป็นค่าว่าง
    df['name'] = df['name'].fillna(df['amenity'])
    df['cuisine'] = df['cuisine'].fillna('general')

    df = df.rename(columns={'amenity': 'amenity_type'})

    selected_cols = config.get("competitor_columns", ["name", "amenity_type", "cuisine", "latitude", "longitude"])
    df_clean = df[selected_cols].copy()

    # ล้างจุดที่ไม่มีพิกัด และล้างจุดพิกัดร้านที่ปักหมุดซ้ำกันเป๊ะๆ (Deduplication)
    df_clean = df_clean.dropna(subset=['latitude', 'longitude'])
    df_clean = df_clean.drop_duplicates(subset=['latitude', 'longitude'])

    logger.info(f"ล้างค่าซ้ำเสร็จสิ้น คงเหลือร้านคู่แข่งในระบบ: {len(df_clean)} จุด")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_clean.to_csv(output_file, index=False)
    logger.info(f"ทำความสะอาดและบันทึกไฟล์ข้อมูลคู่แข่งพร้อมใช้งานสำเร็จ: {output_file}")

if __name__ == "__main__":
    main()