import pandas as pd
import os
from pathlib import Path

# ป้องกันบั๊กพาธสัมพัทธ์โดยใช้อ้างอิงพาธจากไฟล์ปัจจุบัน
BASE_DIR = Path(__file__).resolve().parent.parent.parent
input_file = BASE_DIR / "data" / "raw" / "bts.csv"
output_file = BASE_DIR / "data" / "processed" / "bts_clean.csv"

print(f"กำลังโหลดข้อมูลรถไฟฟ้าดิบจาก: {input_file}...")
df = pd.read_csv(input_file, encoding='latin-1')

df.drop(columns=["Note", "_id", 'No.'], inplace=True)

df["Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=True)
df = df.rename(columns={
    "Date": "date",
    "Organization": "organization",
    "Number_Passenger": "passenger_count"
})

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["day"] = df["date"].dt.day
df["weekday"] = df["date"].dt.dayofweek
df["is_weekend"] = df["weekday"] >= 5

os.makedirs(output_file.parent, exist_ok=True)
df.to_csv(output_file, index=False)
print(f"✅ ทำความสะอาดข้อมูลรถไฟฟ้าและบันทึกสำเร็จที่: {output_file}")