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
รันไฟล์ประสานงานหลักเพื่อทำความสะอาดและจัดเตรียมข้อมูล:
```bash
python data-pipeline/run_pipeline.py
```
*ระบบจะทำความสะอาดข้อมูลที่อยู่อาศัย, วิเคราะห์คู่แข่ง F&B, จัดระเบียบ POIs ประชากร และดึงสถิติผู้โดยสารรถไฟฟ้ารายวันอัตโนมัติพร้อมรายงานความสมบูรณ์*

### 4. วิธีประเมินศักยภาพทำเลรายจุด (CLI Suitability Evaluation)
คุณสามารถรันตัวประเมินทำเลเป้าหมายอย่างเป็นขั้นตอนด้วยคำสั่งภาษาธรรมดา (ย่อชื่อพิกัด/ประเภทธุรกิจ) ดังนี้:

* **คำสั่งแบบย่อพิกัดตามชื่อสถานที่ (Presets):**
  ```bash
  python data-pipeline/scripts/analysis/evaluate_location.py siam-paragon cafe
  ```
  *(ระบบจะดึงพิกัดสยามพารากอนมาประเมินโอกาสสำเร็จของร้านกาแฟให้ทันที)*

* **คำสั่งแบบป้อนพิกัดตรงด้วยละติจูด,ลองจิจูด:**
  ```bash
  python data-pipeline/scripts/analysis/evaluate_location.py 13.7456,100.5342 restaurant
  ```
  *(ระบุประเภทเป็น `restaurant` เพื่อทดสอบคะแนนร้านอาหารตามสั่งทั่วไปได้)*

* **ตัวเลือกประเภทธุรกิจอาหารที่รองรับ:**
  - `restaurant` (หรือ `general`): ร้านอาหารทั่วไป
  - `cafe`                     : ร้านกาแฟ/คาเฟ่
  - `fast_food`                : ร้านอาหารจานด่วน
  - `bar`                      : ร้านเหล้า/สถานบันเทิง
  - `family_buffet`            : ร้านบุฟเฟต์ปิ้งย่าง

---

## 🧪 คู่มือการทดสอบระบบแบบเต็มรูปแบบ (End-to-End Testing Guide)

หากต้องการทดสอบตัวระบบ Data Pipeline ตั้งแต่ต้นน้ำถึงปลายน้ำ ให้ทดสอบดังนี้:

### ขั้นตอนที่ 1: รันดึงพิกัดล่าสุดผ่านอินเทอร์เน็ต (Overpass API Ingestion)
ทำการรันสคริปต์สกัดตำแหน่งคู่แข่งและตึกผู้ซื้อจากเซิร์ฟเวอร์หลัก (ใช้เวลาประมาณ 10-30 วินาที):
```bash
# ดึงพิกัดคู่แข่งอาหาร (ร้านอาหาร, คาเฟ่, บาร์)
python data-pipeline/scripts/scrape/scrape_competitors.py

# ดึงพิกัดจุดความต้องการ (ออฟฟิศ, คอนโด, ห้างสรรพสินค้า)
python data-pipeline/scripts/scrape/scrape_pois.py
```

### ขั้นตอนที่ 2: รันคลีนและจัดโครงสร้างไพป์ไลน์ข้อมูล
ประมวลผลทำความสะอาดคัดแยกข้อมูลที่ได้มาใน **ขั้นตอนที่ 1** พร้อมบันทึกรูป Heatmap:
```bash
python data-pipeline/run_pipeline.py
```

### ขั้นตอนที่ 3: ตรวจสอบรายงานและแผนที่ปฏิสัมพันธ์
* เปิดเช็ครายงาน Heatmap ตรวจสอบค่าว่างได้ที่โฟลเดอร์: [data-pipeline/reports/figures/](data-pipeline/reports/figures/)
* ดับเบิ้ลคลิกเปิดดูแผนที่พล็อตคู่แข่ง Cluster บนบราวเซอร์ได้ที่ไฟล์: [data-pipeline/data/processed/bangkok_competitors_map.html](data-pipeline/data/processed/bangkok_competitors_map.html)

### ขั้นตอนที่ 4: รันวิเคราะห์จุดปักหมุด
ทดลองรันคำสั่งหาคำตอบศักยภาพพื้นที่ย่านเป้าหมาย:
```bash
python data-pipeline/scripts/analysis/evaluate_location.py asok cafe
```
*(หากใส่ชื่อย่อยที่ระบบไม่รู้จัก สคริปต์จะพ่นรายชื่อ Presets ทั้งหมดที่รอบรับในระบบออกมาแสดงทันที)*

