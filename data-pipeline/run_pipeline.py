#!/usr/bin/env python
"""
ZoneVision Data Pipeline Orchestrator
Runs the data extraction and cleaning steps sequentially with proper logging and status checks.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# หาพาธหลักของโปรเจกต์
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"

# ลำดับสคริปต์ที่ต้องรัน
PIPELINE_STEPS = [
    # ขั้นตอนทำความสะอาดข้อมูล (Data Cleaning & Preparation)
    ("scripts/clean/clean_housing.py", "ทำความสะอาดข้อมูลที่อยู่อาศัย (Housing Cleaning)"),
    ("scripts/clean/clean_competitors.py", "ทำความสะอาดข้อมูลคู่แข่ง (Competitors Cleaning)"),
    ("scripts/clean/clean_pois.py", "ทำความสะอาดข้อมูลจุดสนใจ (POIs Cleaning)"),
]

def run_script(script_relative_path, description):
    script_path = BASE_DIR / script_relative_path
    if not script_path.exists():
        print(f"\n❌ ข้อผิดพลาด: ไม่พบสคริปต์ที่ {script_path}")
        return False

    print("\n" + "="*80)
    print(f"🚀 เริ่มรัน: {description}")
    print(f"📂 ไฟล์: {script_relative_path}")
    print("="*80)

    start_time = time.time()
    
    try:
        # สั่งรันในฐานะ Subprocess เพื่อหลีกเลี่ยง Memory Leak ใน RAM ระหว่างไลบรารี GIS
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR), # บังคับให้ Current Working Directory เป็น data-pipeline เสมอ
            check=True
        )
        
        elapsed_time = time.time() - start_time
        print(f"✅ สำเร็จ: {description} (ใช้เวลา: {elapsed_time:.2f} วินาที)")
        return True
        
    except subprocess.CalledProcessError as e:
        elapsed_time = time.time() - start_time
        print(f"❌ ล้มเหลว: {description} (รหัสข้อผิดพลาด: {e.returncode})")
        return False
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดที่คาดไม่ถึง: {str(e)}")
        return False

def main():
    print("================================================================================")
    print("                       ZoneVision Data Pipeline Orchestrator                    ")
    print("================================================================================")
    print(f"📁 Root Directory: {BASE_DIR}")
    print(f"📅 เวลาเริ่มต้นรัน: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    pipeline_start_time = time.time()
    success_count = 0
    
    for idx, (script, desc) in enumerate(PIPELINE_STEPS, 1):
        print(f"\n[ขั้นตอนที่ {idx}/{len(PIPELINE_STEPS)}]")
        success = run_script(script, desc)
        if not success:
            print("\n🚨 ท่อส่งข้อมูล (Pipeline) หยุดทำงานกลางคันเนื่องจากมีขั้นตอนที่เกิดข้อผิดพลาด")
            sys.exit(1)
        success_count += 1

    total_time = time.time() - pipeline_start_time
    print("\n" + "="*80)
    print("                       🎉 การทำงานของ PIPELINE เสร็จสมบูรณ์!                     ")
    print("="*80)
    print(f"• จำนวนขั้นตอนที่ทำสำเร็จ: {success_count}/{len(PIPELINE_STEPS)} ขั้นตอน")
    print(f"• เวลาที่ใช้ทั้งหมด: {total_time:.2f} วินาที (ประมาณ {total_time/60:.2f} นาที)")
    print(f"• ข้อมูลคลีนเสร็จเรียบร้อยและพร้อมใช้งานใน: {BASE_DIR / 'data' / 'processed'}")
    print("="*80)

if __name__ == "__main__":
    main()
