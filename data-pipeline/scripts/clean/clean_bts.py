import pandas as pd

df = pd.read_csv('../../data/raw/bts.csv', encoding='latin-1')

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

df.to_csv("../../data/processed/bts_clean.csv", index=False)