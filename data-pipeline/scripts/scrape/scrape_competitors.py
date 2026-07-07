import pandas as pd
import requests
import json
import os
import gc
import sys
from pathlib import Path
from folium.plugins import MarkerCluster
import folium

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import load_config, get_logger

# โหลดคอนฟิกและตั้งค่า Logger
logger = get_logger("scrape_competitors")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
config = load_config()

bkk_bbox = config.get("bkk_bbox", [100.30, 13.45, 100.95, 13.95])
target_competitors = config.get("target_competitors", ['restaurant', 'cafe', 'fast_food', 'bar'])

def main():
    logger.info("เริ่มต้นดาวน์โหลดข้อมูลกลุ่มคู่แข่งจาก Overpass API...")
    
    # แปลง Bounding Box เป็นฟอร์แมต Overpass: (min_lat, min_lon, max_lat, max_lon)
    bbox_str = f"{bkk_bbox[1]},{bkk_bbox[0]},{bkk_bbox[3]},{bkk_bbox[2]}"
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # คอนฟิกคิวรีดึงเฉพาะโหนด/เส้นที่มี amenity ในกลุ่มเป้าหมาย
    amenity_regex = "|".join(target_competitors)
    query_str = f"""
    [out:json][timeout:120];
    (
      node["amenity"~"{amenity_regex}"]({bbox_str});
      way["amenity"~"{amenity_regex}"]({bbox_str});
    );
    out center;
    """
    
    headers = {
        'User-Agent': 'ZoneVisionSeniorProject/1.0 (contact: naeiger@example.com)'
    }
    
    try:
        response = requests.post(overpass_url, data={'data': query_str}, headers=headers, timeout=120)
        if response.status_code != 200:
            logger.error(f"การดึงข้อมูลล้มเหลว: HTTP Code {response.status_code}")
            return
            
        data = response.json()
        elements = data.get('elements', [])
        logger.info(f"ดึงข้อมูลจากเซิร์ฟเวอร์สำเร็จ! พบรายการข้อมูลคู่แข่ง: {len(elements)} รายการ")
        
        competitors = []
        for el in elements:
            lat = el.get('lat') or el.get('center', {}).get('lat')
            lon = el.get('lon') or el.get('center', {}).get('lon')
            tags = el.get('tags', {})
            name = tags.get('name') or tags.get('name:en') or tags.get('name:th')
            amenity = tags.get('amenity')
            cuisine = tags.get('cuisine')
            
            competitors.append({
                'name': name,
                'amenity_type': amenity,
                'cuisine': cuisine,
                'latitude': lat,
                'longitude': lon
            })
            
        df_pois_flat = pd.DataFrame(competitors)
        
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดระหว่างดึงข้อมูล: {str(e)}")
        return

    if len(df_pois_flat) == 0:
        logger.warning("ไม่พบข้อมูลคู่แข่งใดๆ ในเขตพื้นที่ป้อนคำสั่ง")
        return

    # บันทึกข้อมูลดิบลงใน interim
    os.makedirs(str(BASE_DIR / "data" / "interim"), exist_ok=True)
    output_competitor_file = str(BASE_DIR / "data" / "interim" / "bangkok_competitors.json")
    df_pois_flat.to_json(output_competitor_file, orient='records', force_ascii=False, indent=4)
    logger.info(f"บันทึกไฟล์ระดับดิบเข้าคลัง interim สำเร็จ: {output_competitor_file}")
    
    # วาดแผนที่แสดงผล 2,000 จุดแรก
    logger.info("กำลังประมวลผลแผนที่ HTML คู่แข่ง...")
    m_comp = folium.Map(location=[13.7563, 100.5018], zoom_start=11)
    marker_cluster_comp = MarkerCluster().add_to(m_comp)

    comp_color_map = {
        'restaurant': 'orange',
        'cafe': 'purple',
        'fast_food': 'red',
        'bar': 'black'
    }

    # พลอต 2,000 ตัวอย่างร้านแรกเพื่อกันแผนที่โหลดช้า
    df_map_view = df_pois_flat.head(2000)
    for idx, row in df_map_view.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"<b>{row['name']}</b><br>ประเภท: {row['amenity_type']}<br>สไตล์อาหาร: {row['cuisine']}",
            icon=folium.Icon(color=comp_color_map.get(row['amenity_type'], 'gray'), icon='shopping-cart')
        ).add_to(marker_cluster_comp)

    map_output_path = str(BASE_DIR / "data" / "processed" / "bangkok_competitors_map.html")
    m_comp.save(map_output_path)
    logger.info(f"บันทึกแผนที่ HTML สำเร็จ! จัดเก็บไว้ที่: {map_output_path}")
    
    del df_pois_flat
    del df_map_view
    gc.collect()
    logger.info("เคลียร์แรมระบบข้อมูลสำเร็จ")

if __name__ == "__main__":
    main()
