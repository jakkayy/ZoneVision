.PHONY: help install pipeline scrape run clean

# แสดงคำแนะนำการใช้งาน (Default Target)
help:
	@echo "=========================================================================="
	@echo "                   ZoneVision Makefile Command Center                     "
	@echo "=========================================================================="
	@echo "คำสั่งที่พร้อมใช้งาน:"
	@echo "  make install                  - ติดตั้งสภาพแวดล้อม venv และไลบรารีทั้งหมด"
	@echo "  make scrape                   - ดึงตำแหน่งจาก Overpass API ใหม่ (10-30s)"
	@echo "  make pipeline                 - รันขั้นตอนการคลีนข้อมูลทั้งหมด (16s)"
	@echo "  make run <สถานที่> <ประเภท>     - วิเคราะห์ประเมินศักยภาพทำเล"
	@echo "                                  (เช่น make run siam-square cafe)"
	@echo "  make clean                    - ล้างไฟล์แคชภายในโฟลเดอร์โครงการ"
	@echo "=========================================================================="

# 1. ติดตั้งสภาพแวดล้อม (Setup Virtual Environment)
install:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt
	@echo "✅ ติดตั้งสภาพแวดล้อมและไลบรารีทั้งหมดเรียบร้อย!"

# 2. สกัดข้อมูลใหม่จากอินเทอร์เน็ต (Scrape Data)
scrape:
	@echo "⏳ กำลังดึงตำแหน่งพิกัดร้านค้าและอาคารจาก Overpass API..."
	venv/bin/python data-pipeline/scripts/scrape/scrape_competitors.py
	venv/bin/python data-pipeline/scripts/scrape/scrape_pois.py
	@echo "✅ อัปเดตข้อมูลดิบล่าสุดเสร็จสิ้น!"

# 3. รันคลีนไพป์ไลน์ข้อมูล (Run Clean Pipeline)
pipeline:
	@echo "⏳ กำลังเริ่มรันไพป์ไลน์ประมวลผลข้อมูลหลัก..."
	venv/bin/python data-pipeline/run_pipeline.py

# 4. ล้างแคชส่วนเกิน (Clean Python Caches)
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ ทำความสะอาดเคลียร์ไฟล์แคชไพธอนเรียบร้อย!"

# ------------------------------------------------------------------------
# การประมวลผลอาร์กิวเมนต์แบบไดนามิกสำหรับคำสั่ง 'make run'
# ช่วยให้พิมพ์คำสั่งแบบย่อได้เลย เช่น: make run centralworld general
# ------------------------------------------------------------------------
ifeq (run,$(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # สั่งให้ Make ถือว่าอาร์กิวเมนต์ที่เหลืออยู่เป็นเป้าหมายเปล่าเพื่อไม่ให้เกิดข้อผิดพลาด
  $(eval $(RUN_ARGS):;@:)
endif

run:
	@if [ -z "$(RUN_ARGS)" ]; then \
		echo "❌ ข้อผิดพลาด: กรุณาระบุสถานที่ย่อและประเภทธุรกิจ เช่น: make run siam-square cafe"; \
		exit 1; \
	fi
	venv/bin/python data-pipeline/scripts/analysis/evaluate_location.py $(RUN_ARGS)
