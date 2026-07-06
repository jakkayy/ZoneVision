import pandas as pd
import json
import requests
import time

url = "https://drt.gdcatalog.go.th/en/api/3/action/datastore_search"
resource_id = "8a8d53fc-0c9c-4301-a354-8529bf487ceb"

all_records = []
limit = 10000
offset = 0

while True:
    params = {"resource_id": resource_id, "limit": limit, "offset": offset}

    print(f"กำลังดึงข้อมูล แถวที่ {offset} ถึง {offset + limit}...")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        result = response.json()["result"]
        records = result["records"]

        if not records:
            break

        all_records.extend(records)

        offset += limit

        time.sleep(1)
    else:
        print(f"เกิดข้อผิดพลาด: {response.status_code}")
        break

from pathlib import Path
import os

print(f"ดึงข้อมูลเสร็จสิ้น! ได้ข้อมูลทั้งหมด {len(all_records)} แถว")

df = pd.DataFrame(all_records)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
output_file = BASE_DIR / "data" / "raw" / "bts.csv"
os.makedirs(output_file.parent, exist_ok=True)

df.to_csv(output_file, index=False)
print(f"บันทึกไฟล์สำเร็จที่: {output_file}")