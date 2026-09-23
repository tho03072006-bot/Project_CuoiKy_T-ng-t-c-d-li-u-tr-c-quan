"""
05 - Lam sach, tao truong tinh toan, JOIN tat ca bang -> data/processed/ + SQLite.
Day la script tuong ung truc tiep voi muc 1 cua barem (2.5 diem).
"""
import sqlite3
import numpy as np
import pandas as pd
from _common import RAW, INTERIM, PROCESSED, log

# ---------------------------------------------------------------- 1. NAP
log("Nap cac bang trung gian")
crypto = pd.read_csv(INTERIM / "fact_crypto_daily.csv", parse_dates=["date"])
macro  = pd.read_csv(INTERIM / "fact_macro_daily.csv", parse_dates=["date"])
cmacro = pd.read_csv(INTERIM / "fact_country_macro.csv")
cdim   = pd.read_csv(INTERIM / "dim_country_wb.csv")

def try_read(path, **kw):
    try:
        return pd.read_csv(path, **kw)
    except Exception:
        log(f"  (bo qua, chua co: {path.name})")
        return None

vol    = try_read(INTERIM / "fact_volume_daily.csv", parse_dates=["date"])
coin   = try_read(INTERIM / "dim_coin.csv")

# Bang quoc gia tu Kaggle (co cot CryptoCurrencyStatus + ISO3)
kg = list((RAW / "country_kaggle").glob("*.csv"))
cstatus = pd.read_csv(kg[0]) if kg else None

# ------------------------------------------------- 2. LAM SACH (rubric 0.5d)
log("Lam sach: missing value, outlier, chuan hoa dinh dang")

# 2a. Bo dong gia <= 0 (loi nguon), bo coin co qua it lich su
crypto = crypto[crypto["close"] > 0]
keep = crypto.groupby("ticker")["date"].count()
crypto = crypto[crypto["ticker"].isin(keep[keep >= 180].index)]

# 2b. Missing value trong chuoi gia: noi suy tuyen tinh toi da 3 ngay lien tiep
crypto = crypto.sort_values(["ticker", "date"])
for col in ["open", "high", "low", "close"]:
    crypto[col] = (crypto.groupby("ticker")[col]
                          .transform(lambda s: s.interpolate(limit=3)))
crypto = crypto.dropna(subset=["close"])

# 2c. Outlier: danh dau ngay bien dong bat thuong bang z-score cua log-return
crypto["log_return"] = (crypto.groupby("ticker")["close"]
                              .transform(lambda s: np.log(s).diff()))
z = crypto.groupby("ticker")["log_return"].transform(
        lambda s: (s - s.mean()) / s.std())
crypto["is_outlier"] = z.abs() > 4          # GIU LAI va danh dau, khong xoa
log(f"  danh dau {int(crypto['is_outlier'].sum()):,} ngay outlier (|z| > 4)")

# ------------------------------------ 3. TRUONG TINH TOAN (rubric 0.75d)
log("Tao calculated fields")
g = crypto.groupby("ticker")
crypto["daily_return_pct"] = g["close"].pct_change() * 100
crypto["ma7"]   = g["close"].transform(lambda s: s.rolling(7).mean())
crypto["ma30"]  = g["close"].transform(lambda s: s.rolling(30).mean())
crypto["ma90"]  = g["close"].transform(lambda s: s.rolling(90).mean())
crypto["volatility_30d"] = g["log_return"].transform(
        lambda s: s.rolling(30).std() * np.sqrt(365) * 100)   # bien dong nam hoa
crypto["drawdown_pct"] = g["close"].transform(
        lambda s: (s / s.cummax() - 1) * 100)
crypto["intraday_range_pct"] = (crypto["high"] - crypto["low"]) / crypto["close"] * 100
crypto["year"] = crypto["date"].dt.year
crypto["is_up_day"] = (crypto["daily_return_pct"] > 0).astype(int)  # target Logistic

# ------------------------------------------------- 4. JOIN (rubric 0.75d)
log("Join cac bang")

# JOIN 1: crypto x volume (theo date + ticker)
if vol is not None:
    crypto = crypto.merge(vol, on=["date", "ticker"], how="left")

# JOIN 2: crypto x dim_coin (theo ticker)
if coin is not None:
    crypto = crypto.merge(
        coin[["ticker", "name", "market_cap", "market_cap_rank",
              "circulating_supply", "max_supply"]].drop_duplicates("ticker"),
        on="ticker", how="left")

# JOIN 3: crypto x macro (theo date)
crypto = crypto.merge(macro, on="date", how="left")

# JOIN 4: quoc gia — Kaggle status x World Bank panel x World Bank dim
country = cdim.copy()
if cstatus is not None:
    cs = cstatus.rename(columns={"cca3": "iso3"})
    cols = [c for c in ["iso3", "CryptoCurrencyStatus", "CryptoCurrencyNotes",
                        "pop2023", "density", "landAreaKm"] if c in cs.columns]
    country = country.merge(cs[cols].drop_duplicates("iso3"), on="iso3", how="left")

country_panel = cmacro.merge(country, on="iso3", how="inner")
# Truong tinh toan cho tang quoc gia
country_panel["log_gdp_pc"] = np.log(country_panel["gdp_per_capita_usd"].clip(lower=1))
country_panel["high_inflation"] = (country_panel["inflation_pct"] > 10).astype(int)

# ------------------------------------------------------------- 5. XUAT
log("Xuat data/processed/ + SQLite")
PROCESSED.mkdir(exist_ok=True, parents=True)
crypto.to_csv(PROCESSED / "fact_crypto_enriched.csv", index=False)
country_panel.to_csv(PROCESSED / "fact_country_panel.csv", index=False)
macro.to_csv(PROCESSED / "fact_macro_daily.csv", index=False)
country.to_csv(PROCESSED / "dim_country.csv", index=False)
if coin is not None:
    coin.to_csv(PROCESSED / "dim_coin.csv", index=False)

con = sqlite3.connect(PROCESSED / "crypto_macro.db")
crypto.to_sql("fact_crypto", con, if_exists="replace", index=False)
country_panel.to_sql("fact_country_panel", con, if_exists="replace", index=False)
macro.to_sql("fact_macro_daily", con, if_exists="replace", index=False)
country.to_sql("dim_country", con, if_exists="replace", index=False)
if coin is not None:
    coin.to_sql("dim_coin", con, if_exists="replace", index=False)
con.commit()

# ------------------------------------------------- 6. BAO CAO KIEM TRA
print("\n" + "=" * 58)
print("KIEM TRA DIEU KIEN RUBRIC")
print("=" * 58)
total = len(crypto) + len(country_panel) + len(macro) + len(country)
print(f"fact_crypto        : {len(crypto):>9,} dong x {crypto.shape[1]:>3} cot")
print(f"fact_country_panel : {len(country_panel):>9,} dong x {country_panel.shape[1]:>3} cot")
print(f"fact_macro_daily   : {len(macro):>9,} dong x {macro.shape[1]:>3} cot")
print(f"dim_country        : {len(country):>9,} dong x {country.shape[1]:>3} cot")
if coin is not None:
    print(f"dim_coin           : {len(coin):>9,} dong x {coin.shape[1]:>3} cot")
    total += len(coin)
print("-" * 58)
n_tables = 4 + (1 if coin is not None else 0)
print(f"TONG               : {total:>9,} dong / {n_tables} bang")
print(f"  >= 5.000 dong ?  : {'DAT' if total >= 5000 else 'CHUA DAT'}")
print(f"  >= 3 bang ?      : {'DAT' if n_tables >= 3 else 'CHUA DAT'}")
print(f"  co ISO3 cho map ?: {'DAT' if 'iso3' in country_panel.columns else 'CHUA DAT'}")
print("=" * 58)
log("HOAN TAT")
