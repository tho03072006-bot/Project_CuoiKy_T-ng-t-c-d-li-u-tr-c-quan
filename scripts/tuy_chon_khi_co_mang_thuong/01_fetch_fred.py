"""
01 - Tai chi so vi mo My tu FRED (Federal Reserve Economic Data).
Khong can API key. Moi series la 1 file CSV cong khai.
Ket qua: data/raw/macro/<SERIES>.csv  va  data/interim/fact_macro_daily.csv
"""
import pandas as pd
from _common import RAW, INTERIM, get, log

# Ma series FRED -> ten cot de doc
SERIES = {
    "CPIAUCSL": "cpi_index",        # Chi so gia tieu dung (thang)
    "FEDFUNDS": "fed_funds_rate",   # Lai suat dieu hanh Fed (thang)
    "DTWEXBGS": "dxy_broad",        # Chi so USD (ngay)
    "M2SL":     "m2_supply",        # Cung tien M2 (thang)
    "VIXCLS":   "vix",              # Chi so so hai VIX (ngay)
    "SP500":    "sp500",            # S&P 500 (ngay)
    "DGS10":    "us10y_yield",      # Loi suat trai phieu 10 nam (ngay)
    "UNRATE":   "unemployment",     # Ty le that nghiep (thang)
    "T10YIE":   "breakeven_10y",    # Ky vong lam phat 10 nam (ngay)
}

BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"
frames = []

for code, name in SERIES.items():
    log(f"Tai FRED {code} ({name})")
    text = get(BASE, params={"id": code}, as_json=False)
    path = RAW / "macro" / f"{code}.csv"
    path.write_text(text, encoding="utf-8")

    # FRED dung '.' cho gia tri thieu; ten cot ngay co the la DATE hoac observation_date
    df = pd.read_csv(path, na_values=["."])
    date_col = df.columns[0]
    df = df.rename(columns={date_col: "date", df.columns[1]: name})
    df["date"] = pd.to_datetime(df["date"])
    df[name] = pd.to_numeric(df[name], errors="coerce")
    frames.append(df.set_index("date")[[name]])

# Gop tat ca series tren truc ngay, resample ve tan suat NGAY
macro = pd.concat(frames, axis=1).sort_index()
macro = macro.resample("D").mean()

# Series thang (CPI, M2, FEDFUNDS, UNRATE) chi co gia tri dau thang
# -> forward fill de ghep duoc voi gia crypto theo ngay
monthly = ["cpi_index", "m2_supply", "fed_funds_rate", "unemployment"]
macro[monthly] = macro[monthly].ffill()

# Truong tinh toan moi (Calculated fields - rubric muc 1 yeu cau)
macro["cpi_yoy_pct"] = macro["cpi_index"].pct_change(365) * 100
macro["m2_yoy_pct"] = macro["m2_supply"].pct_change(365) * 100
macro["dxy_ret"] = macro["dxy_broad"].pct_change()
macro["sp500_ret"] = macro["sp500"].pct_change()
macro["real_rate"] = macro["fed_funds_rate"] - macro["cpi_yoy_pct"]  # lai suat thuc

macro = macro.loc["2013-01-01":]     # cat tu 2013 cho khop du lieu crypto
macro.index.name = "date"
out = INTERIM / "fact_macro_daily.csv"
macro.to_csv(out)
log(f"XONG -> {out}  ({len(macro):,} dong x {macro.shape[1]} cot)")
