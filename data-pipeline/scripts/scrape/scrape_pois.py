import pandas as pd
import requests
import json
import os
import gc
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import load_config, get_logger

# โหลดคอนฟิกและตั้งค่า Logger
logger = get_logger("scrape_pois")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
config = load_config()

bkk_bbox = config.get("bkk_bbox", [100.30, 13.45, 100.95, 13.95])
target_pois = config.get("target_pois", ["apartments", "residential", "office", "commercial", "retail"])

def main():
    logger.info("เริ่มต้นดาวน์โหลดข้อมูลจุดดึงดูดประชากร (Demand POIs) จาก Overpass API...")
    
    # แปลง Bounding Box เป็นฟอร์แมต Overpass: (min_lat, min_lon, max_lat, max_lon)
    bbox_str = f"{bkk_bbox[1]},{bkk_bbox[0]},{bkk_bbox[3]},{bkk_bbox[2]}"
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # คอนฟิกคิวรีดึงข้อมูลสิ่งปลูกสร้างที่มี building ตามที่ระบุใน config
    building_regex = "|".join(target_pois)
    query_str = f"""
    [out:json][timeout:180];
    (
      node["building"~"{building_regex}"]({bbox_str});
      way["building"~"{building_regex}"]({bbox_str});
      relation["building"~"{building_regex}"]({bbox_str});
    );
    out center;
    """
    
    headers = {
        'User-Agent': 'ZoneVisionSeniorProject/1.0 (contact: naeiger@example.com)'
    }
    
    try:
        response = requests.post(overpass_url, data={'data': query_str}, headers=headers, timeout=180)
        if response.status_code != 200:
            logger.error(f"การดึงข้อมูลล้มเหลว: HTTP Code {response.status_code}")
            return
            
        data = response.json()
        elements = data.get('elements', [])
        logger.info(f"ดึงข้อมูลจากเซิร์ฟเวอร์สำเร็จ! พบอาคารทั้งหมด: {len(elements)} รายการ")
        
        pois = []
        for el in elements:
            lat = el.get('lat') or el.get('center', {}).get('lat')
            lon = el.get('lon') or el.get('center', {}).get('lon')
            tags = el.get('tags', {})
            name = tags.get('name') or tags.get('name:en') or tags.get('name:th')
            building = tags.get('building')
            
            pois.append({
                'name': name,
                'building': building,
                'latitude': lat,
                'longitude': lon
            })
            
        df_flat = pd.DataFrame(pois)
        
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดระหว่างดึงข้อมูล: {str(e)}")
        return

    if len(df_flat) == 0:
        logger.warning("ไม่พบข้อมูลจุดสนใจความต้องการใดๆ ในเขตพื้นที่ป้อนคำสั่ง")
        return

    # บันทึกข้อมูลดิบลงใน interim
    os.makedirs(str(BASE_DIR / "data" / "interim"), exist_ok=True)
    output_file = str(BASE_DIR / "data" / "interim" / "bangkok_pois.json")
    df_flat.to_json(output_file, orient='records', force_ascii=False, indent=4)
    logger.info(f"บันทึกไฟล์ระดับดิบเข้าคลัง interim สำเร็จ: {output_file}")
    
    del df_flat
    gc.collect()
    logger.info("เคลียร์แรมระบบข้อมูลสำเร็จ")

if __name__ == "__main__":
    main()