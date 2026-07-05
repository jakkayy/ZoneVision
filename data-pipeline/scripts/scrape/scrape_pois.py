import pandas as pd
from pyrosm import OSM
import gc
import os
import sys
from pathlib import Path

# เพิ่มโฟลเดอร์ scripts เข้า sys.path เพื่อให้หาโมดูล utils เจอ
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import load_config, get_logger

# โหลดคอนฟิกและตั้งค่า Logger
logger = get_logger("scrape_pois")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
config = load_config()

osm_filepath = os.getenv("OSM_FILEPATH", str(BASE_DIR / "data" / "raw" / "thailand-260703.osm.pbf"))
bkk_bbox = config.get("bkk_bbox", [100.30, 13.45, 100.95, 13.95])
target_pois = config.get("target_pois", ["apartments", "residential", "office", "commercial", "retail"])

def main():
    logger.info("🚀 เริ่มต้นเชื่อมต่อไฟล์ดิบ OSM และจำกัดขอบเขตกรุงเทพฯ...")
    if not os.path.exists(osm_filepath):
        logger.error(f"ไม่พบไฟล์ OSM ที่ {osm_filepath}")
        return

    osm = OSM(osm_filepath, bounding_box=bkk_bbox)

    logger.info(f"🏗️ กำลังสกัดข้อมูลตึกดิบกลุ่มจุดสนใจ (ประเภท: {target_pois})...")
    buildings_gdf = osm.get_buildings()

    if buildings_gdf is None or len(buildings_gdf) == 0:
        logger.warning("ไม่พบข้อมูลตึกใด ๆ ในขอบเขตพื้นที่ที่ระบุ")
        return

    logger.info(f"ดึงข้อมูลดิบมาได้: {len(buildings_gdf)} แถว. กำลังประมวลผลพิกัด...")
    buildings_gdf['latitude'] = buildings_gdf.geometry.centroid.y
    buildings_gdf['longitude'] = buildings_gdf.geometry.centroid.x

    # แปลงโครงสร้างเป็น DataFrame และทำลาย geometry เพื่อประหยัดแรม
    df_flat = pd.DataFrame(buildings_gdf)
    if 'geometry' in df_flat.columns:
        df_flat = df_flat.drop(columns=['geometry'])

    # บันทึกไฟล์ระดับดิบลงในคลัง interim
    os.makedirs(str(BASE_DIR / "data" / "interim"), exist_ok=True)
    output_file = str(BASE_DIR / "data" / "interim" / "bangkok_pois.json")
    df_flat.to_json(output_file, orient='records', force_ascii=False, indent=4)
    logger.info(f"💾 บันทึกสกัดไฟล์ระดับดิบเข้าคลัง interim สำเร็จ: {output_file}")

    # เคลียร์แรม
    del buildings_gdf
    del df_flat
    gc.collect()
    logger.info("ทำความสะอาดตัวแปรยักษ์ในแรมเรียบร้อย")

if __name__ == "__main__":
    main()