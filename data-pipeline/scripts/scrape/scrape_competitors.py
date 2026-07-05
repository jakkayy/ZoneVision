import pandas as pd
from pyrosm import OSM
import gc
import os
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

osm_filepath = os.getenv("OSM_FILEPATH", str(BASE_DIR / "data" / "raw" / "thailand-260703.osm.pbf"))
bkk_bbox = config.get("bkk_bbox", [100.30, 13.45, 100.95, 13.95])
target_competitors = config.get("target_competitors", ['restaurant', 'cafe', 'fast_food', 'bar'])

def main():
    logger.info("เริ่มต้นเชื่อมต่อไฟล์ดิบ OSM และจำกัดขอบเขตกรุงเทพฯ...")
    if not os.path.exists(osm_filepath):
        logger.error(f"ไม่พบไฟล์ OSM ที่ {osm_filepath}")
        return

    osm = OSM(osm_filepath, bounding_box=bkk_bbox)

    logger.info(f"กำลังสกัดข้อมูลดิบกลุ่มคู่แข่ง (ประเภท: {target_competitors})...")
    pois_gdf = osm.get_pois(custom_filter={"amenity": target_competitors})

    if pois_gdf is None or len(pois_gdf) == 0:
        logger.warning("ไม่พบข้อมูลคู่แข่งใด ๆ ในขอบเขตพื้นที่ที่ระบุ")
        return

    logger.info(f"ดึงข้อมูลดิบมาได้: {len(pois_gdf)} แถว. กำลังประมวลผลพิกัด...")
    pois_gdf['latitude'] = pois_gdf.geometry.centroid.y
    pois_gdf['longitude'] = pois_gdf.geometry.centroid.x

    # แปลงโครงสร้างเป็น DataFrame และทำลายคอลัมน์ geometry เพื่อประหยัดแรม
    df_pois_flat = pd.DataFrame(pois_gdf)
    if 'geometry' in df_pois_flat.columns:
        df_pois_flat = df_pois_flat.drop(columns=['geometry'])

    # บันทึกไฟล์ดิบเชิงโครงสร้างลงในคลัง interim
    os.makedirs(str(BASE_DIR / "data" / "interim"), exist_ok=True)
    output_competitor_file = str(BASE_DIR / "data" / "interim" / "bangkok_competitors.json")
    df_pois_flat.to_json(output_competitor_file, orient='records', force_ascii=False, indent=4)
    logger.info(f"บันทึกสกัดไฟล์ระดับดิบเข้าคลัง interim สำเร็จ: {output_competitor_file}")
    
    del pois_gdf
    del df_pois_flat
    gc.collect()

    # 8. 🗺️ โหลดข้อมูลเฉพาะที่บันทึกเสร็จแล้วมา 2,000 จุด เพื่อวาดแผนที่แสดงผล
    print("\n🗺️ กำลังประมวลผลวาดแผนที่คู่แข่ง... (ดึง 2,000 ร้านแรกมาพล็อตเพื่อป้องกันระบบค้าง)")
    m_comp = folium.Map(location=[13.7563, 100.5018], zoom_start=11)
    marker_cluster_comp = MarkerCluster().add_to(m_comp)

    comp_color_map = {
        'restaurant': 'orange',
        'cafe': 'purple',
        'fast_food': 'darkred',
        'bar': 'black'
    }

    df_map_view = pd.read_json(output_competitor_file)

    for idx, row in df_map_view.head(2000).iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=f"<b>{row['name']}</b><br>ประเภท: {row['amenity_type']}<br>สไตล์อาหาร: {row['cuisine']}",
            icon=folium.Icon(color=comp_color_map.get(row['amenity_type'], 'gray'), icon='shopping-cart')
        ).add_to(marker_cluster_comp)

    map_output_path = str(BASE_DIR / "data" / "processed" / "bangkok_competitors_map.html")
    m_comp.save(map_output_path)
    print(f"💾 🎉 บันทึกแผนที่ HTML สำเร็จ! จัดเก็บไว้ที่: {map_output_path}")

    del df_map_view
    gc.collect()
    print("🤖 [สถานะ: ปลอดภัย] ล้างแรมเกลี้ยงหมดจด 100% เรียบร้อยครับ!")

if __name__ == "__main__":
    main()

