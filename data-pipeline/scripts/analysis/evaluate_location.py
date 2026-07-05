import pandas as pd
import numpy as np
import os
import sys
import argparse
from pathlib import Path

# เพิ่มโฟลเดอร์ scripts เข้า sys.path เพื่อให้โหลด utils ได้
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import load_config, get_logger

# ตั้งค่า Logger และ Config
logger = get_logger("evaluate_location")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
processed_dir = BASE_DIR / "data" / "processed"

# ตรรกะคณิตศาสตร์สำหรับคำนวณระยะห่างโค้งโลก (Haversine Formula)
def haversine_distance(lat1, lon1, lat2, lon2):
    """คำนวณระยะห่างระหว่างสองจุดบนผิวโลกจริง (หน่วย: กิโลเมตร)"""
    # แปลงองศาเป็นเรเดียน
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # คำนวณความยาวคอร์ด
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2.0 * np.arcsin(np.sqrt(a))
    
    # รัศมีเฉลี่ยของโลก (กิโลเมตร)
    r = 6371.0
    return c * r

# ฟังก์ชันคำนวณน้ำหนักลดทอนตามระยะทาง (Distance Decay Function)
def calculate_distance_decay(distance_km, beta=3.0):
    """คำนวณค่าน้ำหนักลดทอนตามระยะทางด้วย Exponential Decay"""
    return np.exp(-beta * distance_km)

def evaluate_site(lat, lng, biz_type, max_radius_km=1.0):
    """
    ประเมินทำเลปักหมุดรายพิกัด
    """
    competitors_file = processed_dir / "bangkok_competitors_clean.csv"
    pois_file = processed_dir / "bangkok_pois_clean.csv"

    if not competitors_file.exists() or not pois_file.exists():
        logger.error("ไม่พบไฟล์ข้อมูลคลีนใน data/processed/ กรุณารัน run_pipeline.py ก่อน")
        return None

    # 1. โหลดข้อมูลคลีน
    df_competitors = pd.read_csv(competitors_file)
    df_pois = pd.read_csv(pois_file)

    # 2. คำนวณระยะทางจากพิกัดเป้าหมายไปยังทุกจุด
    df_competitors['distance'] = haversine_distance(lat, lng, df_competitors['latitude'], df_competitors['longitude'])
    df_pois['distance'] = haversine_distance(lat, lng, df_pois['latitude'], df_pois['longitude'])

    # 3. กรองข้อมูลเฉพาะจุดที่อยู่ในรัศมีสูงสุด
    df_comp_in_radius = df_competitors[df_competitors['distance'] <= max_radius_km].copy()
    df_pois_in_radius = df_pois[df_pois['distance'] <= max_radius_km].copy()

    # 4. คำนวณน้ำหนักลดทอนรายจุด
    df_comp_in_radius['weight'] = calculate_distance_decay(df_comp_in_radius['distance'])
    df_pois_in_radius['weight'] = calculate_distance_decay(df_pois_in_radius['distance'])

    # 5. โหลดค่าน้ำหนักแยกตามประเภทร้านอาหาร (Weights Matrix)
    # เพิ่มขนาดสเกลแรงดึงดูดของตึกฝั่ง Demand (condo/office/mall) เพื่อชดเชยปริมาณคนจำนวนมากในตึก 1 หลัง
    # [demand_condo, demand_office, demand_mall] | [supply_restaurant, supply_cafe, supply_fast_food, supply_bar]
    weights_matrix = {
        'general': {
            'demand': {'condo/apartment': 10.0, 'office': 15.0, 'mall': 8.0},
            'supply': {'restaurant': 1.0, 'cafe': 0.3, 'fast_food': 0.3, 'bar': 0.1}
        },
        'cafe': {
            'demand': {'condo/apartment': 5.0, 'office': 25.0, 'mall': 12.0},
            'supply': {'restaurant': 0.2, 'cafe': 1.2, 'fast_food': 0.2, 'bar': 0.1}
        },
        'fast_food': {
            'demand': {'condo/apartment': 4.0, 'office': 15.0, 'mall': 20.0},
            'supply': {'restaurant': 0.5, 'cafe': 0.2, 'fast_food': 1.2, 'bar': 0.1}
        },
        'bar': {
            'demand': {'condo/apartment': 12.0, 'office': 10.0, 'mall': 4.0},
            'supply': {'restaurant': 0.1, 'cafe': 0.1, 'fast_food': 0.1, 'bar': 1.2}
        },
        'family_buffet': {
            'demand': {'condo/apartment': 18.0, 'office': 6.0, 'mall': 15.0},
            'supply': {'restaurant': 1.0, 'cafe': 0.1, 'fast_food': 0.4, 'bar': 0.1}
        }
    }

    if biz_type not in weights_matrix:
        logger.error(f"ไม่รู้จักประเภทธุรกิจอาหาร: {biz_type}")
        return None

    w = weights_matrix[biz_type]

    # 6. คำนวณ Demand Score ถ่วงน้ำหนัก
    weighted_demand = 0.0
    demand_counts = {'condo/apartment': 0, 'office': 0, 'mall': 0}
    weighted_demand_counts = {'condo/apartment': 0.0, 'office': 0.0, 'mall': 0.0}

    for idx, row in df_pois_in_radius.iterrows():
        p_type = row['type']
        if p_type in w['demand']:
            demand_counts[p_type] += 1
            weighted_val = row['weight'] * w['demand'][p_type]
            weighted_demand += weighted_val
            weighted_demand_counts[p_type] += weighted_val

    # 7. คำนวณ Supply (Competitor) Score ถ่วงน้ำหนัก
    weighted_supply = 0.0
    supply_counts = {'restaurant': 0, 'cafe': 0, 'fast_food': 0, 'bar': 0}
    weighted_supply_counts = {'restaurant': 0.0, 'cafe': 0.0, 'fast_food': 0.0, 'bar': 0.0}

    for idx, row in df_comp_in_radius.iterrows():
        c_type = row['amenity_type']
        if c_type in w['supply']:
            supply_counts[c_type] += 1
            weighted_val = row['weight'] * w['supply'][c_type]
            weighted_supply += weighted_val
            weighted_supply_counts[c_type] += weighted_val

    # 8. สมการคำนวณคะแนนสุทธิและทำการปรับระดับเต็ม 100 ด้วย S-curve (Soft saturation)
    opportunity_ratio = weighted_demand / (weighted_supply + 1.0)
    # ปรับจูน Divisor เป็น 3.5 เพื่อเกลี่ยคะแนนให้สอดคล้องกับพฤติกรรมความหนาแน่นเมือง
    raw_score = 100.0 * (1.0 - np.exp(-opportunity_ratio / 3.5))
    score = round(raw_score, 1)

    # 9. ตัดเกรดศักยภาพทำเล
    if score >= 80:
        grade = "A (ทำเลทองศักยภาพสูงมาก)"
    elif score >= 60:
        grade = "B (ทำเลดี มีโอกาสเติบโต)"
    elif score >= 40:
        grade = "C (ทำเลปานกลาง การแข่งขันสูง)"
    else:
        grade = "D (ทำเลมีความเสี่ยงสูง)"

    # 10. สร้างข้อความแนะนำเชิงธุรกิจ (Rule-based Insights)
    insights = []
    if weighted_supply_counts.get(biz_type, 0.0) > 3.0:
        insights.append(f"ความเสี่ยง: มีคู่แข่งสายตรงประเภทเดียวกันหนาแน่นในระยะประชิด (นับหัวจริงได้ {supply_counts.get(biz_type, 0)} ร้าน)")
    else:
        insights.append("โอกาสเด่น: การแข่งขันจากคู่แข่งสายตรงในระยะใกล้ยังอยู่ในระดับต่ำ")

    if biz_type == 'cafe' and weighted_demand_counts['office'] > 5.0:
        insights.append("จุดแข็ง: ปริมาณคนทำงานหนาแน่นสูงมาก เหมาะสำหรับการเจาะกลุ่มตลาดพรีออเดอร์มื้อเช้า/กลางวัน")
    elif biz_type == 'family_buffet' and weighted_demand_counts['condo/apartment'] > 8.0:
        insights.append("จุดแข็ง: โซนที่พักอาศัยระดับกลาง-สูงหนาแน่น เหมาะกับกลุ่มตลาดมื้อเย็นและครอบครัว")
        
    if score < 40:
        insights.append("ข้อเสนอแนะ: ทำเลนี้ค่อนข้างท้าทาย ควรลดความเสี่ยงโดยปรับรูปแบบเป็น Cloud Kitchen หรือพิจารณาย้ายพิกัดปักหมุดใหม่")
    elif score >= 80:
        insights.append("ข้อเสนอแนะ: ทำเลมีศักยภาพยอดเยี่ยม สามารถเปิดร้านรูปแบบมีที่นั่งบริการหน้าร้านได้อย่างเต็มรูปแบบ")

    return {
        'score': score,
        'grade': grade,
        'demand_raw': demand_counts,
        'demand_weighted': {k: round(v, 2) for k, v in weighted_demand_counts.items()},
        'supply_raw': supply_counts,
        'supply_weighted': {k: round(v, 2) for k, v in weighted_supply_counts.items()},
        'insights': insights
    }

if __name__ == "__main__":
    # รองรับการป้อนคำสั่งผ่าน Terminal เช่น:
    # python evaluate_location.py --lat 13.7456 --lng 100.5342 --type cafe
    parser = argparse.ArgumentParser(description="ZoneVision - Site Suitability Evaluation Tool")
    parser.add_argument("--lat", type=float, required=True, help="พิกัดละติจูดของร้านเป้าหมาย")
    parser.add_argument("--lng", type=float, required=True, help="พิกัดลองจิจูดของร้านเป้าหมาย")
    parser.add_argument("--type", type=str, required=True, choices=['general', 'cafe', 'fast_food', 'bar', 'family_buffet'], help="ประเภทของร้านอาหาร")
    parser.add_argument("--radius", type=float, default=1.0, help="รัศมีขอบเขตประเมินหน่วยเป็นกิโลเมตร (ค่าเริ่มต้น: 1.0)")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("                ZONEVISION SITE SUITABILITY REPORT               ")
    print("="*80)
    print(f"พิกัดเป้าหมาย: Lat {args.lat}, Lng {args.lng}")
    print(f"ประเภทร้านอาหาร: {args.type}")
    print(f"รัศมีวิเคราะห์: {args.radius} กิโลเมตร (ถ่วงน้ำหนักลดทอนตามระยะทาง)")
    print("-"*80)
    
    report = evaluate_site(args.lat, args.lng, args.type, args.radius)
    
    if report:
        print(f"คะแนนโอกาสสำเร็จ (Opportunity Score): {report['score']} / 100")
        print(f"เกรดประเมินทำเล: {report['grade']}")
        print("-"*80)
        
        print("สถิติตัวแปรความหนาแน่นลูกค้า (Demand Indicators):")
        for k in report['demand_raw'].keys():
            print(f"  - {k}: พบจริง {report['demand_raw'][k]} ตึก | คิดเป็นน้ำหนักแรงส่งยอดขายจริง: {report['demand_weighted'][k]}")
            
        print("\nสถิติการแข่งขันของคู่แข่งรายรอบ (Competitors/Supply):")
        for k in report['supply_raw'].keys():
            print(f"  - {k}: พบจริง {report['supply_raw'][k]} ร้าน | คิดเป็นน้ำหนักแรงเบียดแย่งลูกค้า: {report['supply_weighted'][k]}")
            
        print("-"*80)
        print("บทสรุปเชิงลึกและคำแนะนำเชิงธุรกิจ (Business Insights):")
        for idx, insight in enumerate(report['insights'], 1):
            print(f" {idx}. {insight}")
    print("="*80 + "\n")
