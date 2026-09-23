"""
04 - Gop 96 file CSV roi tu dataset Kaggle svaningelgem thanh 1 bang fact.
Truoc khi chay: giai nen dataset vao data/raw/crypto_kaggle/
Ket qua: data/interim/fact_crypto_daily.csv
"""
import pandas as pd
from _common import RAW, INTERIM, log

src = RAW / "crypto_kaggle"
files = sorted(src.glob("*.csv"))
if not files:
    raise SystemExit(
        f"Khong thay file CSV nao trong {src}\n"
        "Hay tai dataset Kaggle svaningelgem/crypto-currencies-daily-prices "
        "va giai nen vao thu muc do truoc.")

log(f"Tim thay {len(files)} file CSV")
frames = []
for f in files:
    df = pd.read_csv(f)
    df.columns = [c.strip().lower() for c in df.columns]
    if "ticker" not in df.columns:          # phong truong hop file thieu cot ticker
        df["ticker"] = f.stem.upper()
    frames.append(df)

fact = pd.concat(frames, ignore_index=True)
fact["date"] = pd.to_datetime(fact["date"], errors="coerce")
fact = fact.dropna(subset=["date", "close"])
fact = fact.drop_duplicates(["ticker", "date"]).sort_values(["ticker", "date"])

fact.to_csv(INTERIM / "fact_crypto_daily.csv", index=False)
log(f"XONG -> fact_crypto_daily.csv  {len(fact):,} dong, "
    f"{fact['ticker'].nunique()} coin, {fact['date'].min().date()} -> {fact['date'].max().date()}")
