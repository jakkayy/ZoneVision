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
logger = get_logger("clean_housing")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
input_file = str(BASE_DIR / "data" / "interim" / "bangkok_housing.json")
output_file = str(BASE_DIR / "data" / "processed" / "bangkok_housing_clean.csv")
report_dir = BASE_DIR / "reports" / "figures"

def main():
    logger.info("🧹 เริ่มต้นขั้นตอนทำความสะอาดข้อมูลที่อยู่อาศัย (Housing Cleaning)...")
    if not os.path.exists(input_file):
        logger.error(f"ไม่พบไฟล์ดิบที่จัดเก็บชั่วคราวที่ {input_file}")
        return

    df = pd.read_json(input_file)

    logger.info("สร้างและจัดเก็บรายงาน Heatmap ความสมบูรณ์ของข้อมูลดิบ...")
    os.makedirs(str(report_dir), exist_ok=True)
    plt.figure(figsize=(10, 6))
    sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
    plt.title("Heatmap of Missing Values in Bangkok Housing Dataset")
    heatmap_path = str(report_dir / "housing_missing_values.png")
    plt.savefig(heatmap_path)
    plt.close()
    logger.info(f"บันทึกไฟล์ภาพ Heatmap สำเร็จ: {heatmap_path}")

    logger.info("ทำการคัดเลือกฟีเจอร์ แปลงชนิดตัวเลข และล้างสตริงชื่อเขต...")
    # เลือกแมปฟีเจอร์สำคัญสำหรับโมเดลทำเลที่อยู่อาศัย
    target_features = {
        'จังหวัด/อำเภอ': 'district',
        'บ้าน (1)': 'house',
        'ทาวน์เฮ้าส์ (39)': 'townhouse',
        'บ้านแฝด (45)': 'semi_detached_house',
        'อาคารชุด (22)': 'condo',
        'แฟลต (21)': 'flat',
        'หอพัก (14)': 'dormitory',
        'สำนักงาน (20)': 'office',
        'ร้านค้า (19)': 'shop',
        'ตึกแถว (16)': 'shophouse',
        'รวม': 'total_buildings'
    }
    
    df_clean = pd.DataFrame()
    for raw_col, new_col in target_features.items():
        if raw_col in df.columns:
            if raw_col == 'จังหวัด/อำเภอ':
                # ล้างตัวอักษรส่วนเกิน และปรับฟอร์แมตชื่อเขตให้สอดคล้องกับ Shapefile/GeoJSON
                df_clean[new_col] = df[raw_col].astype(str).str.replace('ท้องถิ่นเขต', 'เขต').str.strip()
            else:
                # ล้างเครื่องหมายลูกน้ำคอมมา "," ในข้อความ และแปลงเป็นจำนวนเต็ม Integer
                df_clean[new_col] = df[raw_col].astype(str).str.replace(',', '', regex=False).str.strip()
                df_clean[new_col] = pd.to_numeric(df_clean[new_col], errors='coerce').fillna(0).astype(int)

    # ล้างจุดพิกัดที่เป็นค่าว่าง หรือแถวที่ไม่มีข้อมูลเขต
    df_clean = df_clean.dropna(subset=['district'])
    df_clean = df_clean.drop_duplicates(subset=['district'])

    # สรุปภาพรวมออกทาง Log
    logger.info(f"คลีนข้อมูลเสร็จสิ้น ยอดรวมเขตที่บันทึก: {df_clean['district'].nunique()} เขต")
    logger.info(f"จำนวนคอนโดทั้งหมดในระบบ: {df_clean['condo'].sum():,} ยูนิต")

    # บันทึกข้อมูลที่สะอาดลงProcessed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_clean.to_csv(output_file, index=False)
    logger.info(f"💾 🎉 ทำความสะอาดและบันทึกไฟล์ข้อมูลที่อยู่อาศัยลง processed สำเร็จ: {output_file}")

if __name__ == "__main__":
    main()