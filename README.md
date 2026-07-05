# ZoneVision - Location Intelligence for F&B in Bangkok

โปรเจกต์วิเคราะห์ทำเลศักยภาพ (Location Suitability Analysis) ในกรุงเทพฯ สำหรับประเภทร้านอาหารต่าง ๆ (ทั่วไป, คาเฟ่, ฟาสต์ฟู้ด, บาร์, บุฟเฟ่ต์ครอบครัว) โดยใช้ข้อมูลเชิงพื้นที่และ H3 Grid System ของ Uber

---

## 📁 โครงสร้างระบบ
* **`data-pipeline/data/raw/`**: ที่เก็บข้อมูลดิบ (เช่น ไฟล์ผังเมืองประเทศไทย `thailand-260703.osm.pbf` และสถิติสิ่งปลูกสร้าง `housing-infomation.csv`)
* **`data-pipeline/data/interim/`**: ข้อมูลที่สกัดออกมาจากการแปลงพิกัดเบื้องต้น (JSON)
* **`data-pipeline/data/processed/`**: ข้อมูลที่ทำความสะอาดพร้อมใช้งาน และผลลัพธ์คะแนนทำเลทอง (`bangkok_h3_opportunity_scores.csv`)
* **`data-pipeline/reports/figures/`**: แผนภูมิวิเคราะห์ค่าว่าง (Heatmaps) สำหรับประเมินความถูกต้องของชุดข้อมูล

---

## 🚀 ขั้นตอนและวิธีใช้งาน

### 1. เข้าใช้งานสภาพแวดล้อมเสมือน (Activate Virtual Environment)
เปิด Terminal ในโฟลเดอร์โปรเจกต์ (`ZoneVision`) แล้วเรียกใช้งาน `venv` ด้วยคำสั่ง:
```bash
source venv/bin/activate
```

### 2. อัปเดตและติดตั้งไลบรารีเพิ่มเติม
หากต้องการตรวจสอบว่าไลบรารีที่จำเป็นถูกติดตั้งครบถ้วนแล้ว ให้รันคำสั่ง:
```bash
pip install -r requirements.txt
```

### 3. วิธีรันระบบวิเคราะห์ทำเลทอง (Run Pipeline)
รันไฟล์ประสานงานหลักเพื่อทำความสะอาดข้อมูลดิบในเครื่องและคำนวณคะแนนทำเลทองทันที:
```bash
python data-pipeline/run_pipeline.py
```
*ระบบจะทำความสะอาดตารางข้อมูล ตรวจสอบค่าว่าง บันทึกรูป Heatmap รายงานความผิดพลาด และคำนวณคะแนนความเหมาะสมของร้านอาหารแต่ละประเภทแยกรายกริดให้โดยอัตโนมัติ*

### 4. ตรวจสอบผลลัพธ์ (Check Output)
หลังจากรันเสร็จสิ้น คุณสามารถนำข้อมูลไปใช้งานต่อได้ที่โฟลเดอร์ผลลัพธ์:
* **ไฟล์คะแนนทำเลแยกรายกริดหกเหลี่ยม:** [bangkok_h3_opportunity_scores.csv](data-pipeline/data/processed/bangkok_h3_opportunity_scores.csv)
* **รูปภาพรายงานตรวจสุขภาพข้อมูล (Heatmaps):** สามารถเปิดดูภาพตรวจสอบค่าว่างได้ในโฟลเดอร์ [reports/figures/](data-pipeline/reports/figures/)

---

## 🛠️ วิธีการรันขั้นตอนสกัดข้อมูลดิบใหม่ (Optional)
หากในอนาคตคุณได้ไฟล์ข้อมูลดิบ PBF หรือ CSV ชุดใหม่มาแทนที่ในโฟลเดอร์ `raw/` และต้องการโหลดนำเข้าใหม่ตั้งแต่ต้น (ก่อนรัน Pipeline คลีนข้อมูล) ให้รันสคริปต์เหล่านี้ตามลำดับ:
```bash
# 1. สกัดข้อมูลสิ่งปลูกสร้างจดทะเบียนระดับเขต
python data-pipeline/scripts/scrape/scrape_housing.py

# 2. สกัดข้อมูลพิกัดคู่แข่งธุรกิจอาหารในกรุงเทพฯ
python data-pipeline/scripts/scrape/scrape_competitors.py

# 3. สกัดข้อมูลพิกัดสิ่งปลูกสร้างที่เป็นแหล่งดึงดูดคน (Offices, Malls, Condos)
python data-pipeline/scripts/scrape/scrape_pois.py
```
*(เมื่อรันสคริปต์ข้างต้นเสร็จสิ้น ไฟล์ใน interim/ จะอัปเดต และคุณสามารถรัน `python data-pipeline/run_pipeline.py` เพื่อคลีนและประมวลผลคะแนนใหม่ได้ทันที)*
# ZoneVision
