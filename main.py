import os
import requests
import pandas as pd

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc1MTMxNzczLCJpYXQiOjE3NzUwNDUzNzMsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA5NzEzOTI2In0.7spAcOgYnIElfV1Xokwe0Oo8uvU_EHBMpzYno4ZqftGqiHLh5gDLnFEwSqkhfF6WHc_mNd78PKkFMF2fnwTkcQ"
url = "https://api.dhan.co/v2/charts/intraday"


headers = {
    "Content-Type": "application/json",
    "access-token": ACCESS_TOKEN
}


if not ACCESS_TOKEN:
    print("❌ No token in environment")
else:
    print("✅ Token loaded")
    print("Token prefix:", ACCESS_TOKEN[:305], "...")
    print("Token length:", len(ACCESS_TOKEN))



payload = {
    "securityId": "13",
    "exchangeSegment": "IDX_I",
    "instrument": "INDEX",
    "interval": "15",
    "oi": False,
    "fromDate": "2025-01-01",
    "toDate": "2025-03-03"
}

resp = requests.post(url, headers=headers, json=payload, timeout=30)

print("HTTP:", resp.status_code)
print("Raw response:")
print(resp.text)

if resp.status_code != 200:
    raise SystemExit("Request failed")

data = resp.json()

df = pd.DataFrame({
    "datetime": pd.to_datetime(data["timestamp"], unit="s"),
    "open": data["open"],
    "high": data["high"],
    "low": data["low"],
    "close": data["close"],
    "volume": data["volume"]
}).set_index("datetime")

# ✅ INSERT STARTS HERE (after df is created)
df["candle_color"] = "DOJI"
df.loc[df["close"] > df["open"], "candle_color"] = "GREEN"
df.loc[df["close"] < df["open"], "candle_color"] = "RED"

df["points"] = (df["close"] - df["open"]).abs()

df = df.sort_index()

from_date = payload["fromDate"].replace(" ", "_").replace(":", "-")
to_date   = payload["toDate"].replace(" ", "_").replace(":", "-")

csv_name = f"nifty_{payload['interval']}min_{from_date}_to_{to_date}.csv"
df.to_csv(csv_name, index=True)

print("✅ Saved:", csv_name)

df.to_csv(csv_name, index=True)
print(f"✅ Exported CSV: {csv_name} | rows={len(df)}")
# ✅ INSERT ENDS HERE

print(df.head())
print(df.tail())
