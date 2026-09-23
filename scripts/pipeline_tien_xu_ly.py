# -*- coding: utf-8 -*-
"""Pipeline tien xu ly - De tai 09: Crypto & chi so vi mo."""
import argparse, os, json, tarfile
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="Tái lập 7 bảng từ dữ liệu thô có sẵn; không tải mạng.")
parser.add_argument("--raw", type=Path, default=ROOT / "data" / "raw")
parser.add_argument("--out", type=Path, default=ROOT / "data" / "processed")
args = parser.parse_args()
RAW, OUT = args.raw.resolve(), args.out.resolve()
OUT.mkdir(parents=True, exist_ok=True)
log = lambda m: print(f"[*] {m}", flush=True)
raw_counts = {}


def coin_sources():
    """Đọc trực tiếp archive để tái lập được bản nộp mà không cần giải nén/tải lại."""
    files = sorted((RAW / "coinmetrics").glob("*.csv"))
    if files:
        for file in files:
            yield file.stem.upper(), pd.read_csv(file, low_memory=False, encoding="utf-8-sig")
    else:
        archive = RAW / "coinmetrics_raw.tar.gz"
        if not archive.exists():
            raise FileNotFoundError(f"Thiếu {archive} và thư mục coinmetrics/*.csv")
        with tarfile.open(archive, "r:gz") as tar:
            for member in sorted(tar.getmembers(), key=lambda item: item.name):
                if member.isfile() and member.name.endswith(".csv"):
                    with tar.extractfile(member) as stream:
                        yield Path(member.name).stem.upper(), pd.read_csv(stream, low_memory=False, encoding="utf-8-sig")

CATEGORY = {  # phan loai thu cong de lam dim_coin
 "BTC":"Layer 1","ETH":"Layer 1","BNB":"Layer 1","ADA":"Layer 1","SOL":"Layer 1",
 "XRP":"Payment","DOGE":"Meme","SHIB":"Meme","DOT":"Layer 1","AVAX":"Layer 1",
 "TRX":"Layer 1","LTC":"Payment","BCH":"Payment","XLM":"Payment","ETC":"Layer 1",
 "XMR":"Privacy","ZEC":"Privacy","DASH":"Privacy","ATOM":"Layer 1","NEAR":"Layer 1",
 "ALGO":"Layer 1","VET":"Layer 1","HBAR":"Layer 1","EOS":"Layer 1","NEO":"Layer 1",
 "QTUM":"Layer 1","XTZ":"Layer 1","ICP":"Layer 1","FTM":"Layer 1","THETA":"Layer 1",
 "WAVES":"Layer 1","APT":"Layer 1","MATIC":"Layer 2","LRC":"Layer 2",
 "USDT":"Stablecoin","USDC":"Stablecoin",
 "UNI":"DeFi","AAVE":"DeFi","MKR":"DeFi","COMP":"DeFi","CRV":"DeFi","SNX":"DeFi",
 "YFI":"DeFi","SUSHI":"DeFi","1INCH":"DeFi","ZRX":"DeFi","KNC":"DeFi","REN":"DeFi",
 "BAT":"Utility","LINK":"Oracle","GRT":"Infrastructure","FIL":"Storage",
 "STORJ":"Storage","AR":"Storage","CHZ":"Gaming","GALA":"Gaming","AXS":"Gaming",
 "SAND":"Metaverse","MANA":"Metaverse","ENJ":"Gaming","ANKR":"Infrastructure",
 "REP":"DeFi","OMG":"Layer 2","EGLD":"Layer 1",
}

# ============================== 1. CRYPTO ==============================
log("1/6 Gop du lieu Coin Metrics")
PRICE_COLS = ["PriceUSD","ReferenceRateUSD","ReferenceRate"]
price_rows, mkt_rows, meta = [], [], []

for tk, d in coin_sources():
    raw_counts[f"coinmetrics/{tk}"] = len(d)
    d["date"] = pd.to_datetime(d["time"], errors="coerce", utc=True).dt.tz_localize(None).dt.normalize()
    d = d.dropna(subset=["date"])

    # --- gia: uu tien PriceUSD, sau do ReferenceRateUSD/ReferenceRate ---
    price = None
    for c in PRICE_COLS:
        if c in d.columns and d[c].notna().sum() > 180:
            price = d[c]; break

    mcap = d["CapMrktCurUSD"] if "CapMrktCurUSD" in d.columns and d["CapMrktCurUSD"].notna().sum() > 100 \
           else (d["CapMrktEstUSD"] if "CapMrktEstUSD" in d.columns else pd.Series(np.nan, index=d.index))
    vol  = d["volume_reported_spot_usd_1d"] if "volume_reported_spot_usd_1d" in d.columns \
           else pd.Series(np.nan, index=d.index)

    # bang market cap / volume: gom CA cac coin khong co lich su gia
    m = pd.DataFrame({"date": d["date"], "ticker": tk,
                      "market_cap_usd": pd.to_numeric(mcap, errors="coerce"),
                      "volume_usd": pd.to_numeric(vol, errors="coerce")})
    m = m.dropna(subset=["market_cap_usd","volume_usd"], how="all")
    if len(m) >= 180: mkt_rows.append(m)

    if price is None:
        meta.append((tk, 0, "", "", "chi co market cap/volume")); continue

    p = pd.DataFrame({"date": d["date"], "ticker": tk,
                      "price_usd": pd.to_numeric(price, errors="coerce"),
                      "market_cap_usd": pd.to_numeric(mcap, errors="coerce"),
                      "volume_usd": pd.to_numeric(vol, errors="coerce")})
    for src, dst in [("AdrActCnt","active_addresses"), ("TxCnt","tx_count"),
                     ("TxTfrCnt","transfer_count"), ("HashRate","hashrate"),
                     ("SplyCur","supply"), ("CapMVRVCur","mvrv"),
                     ("FlowInExUSD","exchange_inflow_usd"),
                     ("FlowOutExUSD","exchange_outflow_usd")]:
        p[dst] = pd.to_numeric(d[src], errors="coerce") if src in d.columns else np.nan
    p = p.dropna(subset=["price_usd"]); p = p[p["price_usd"] > 0]
    if len(p) < 180:
        meta.append((tk, len(p), "", "", "qua ngan")); continue
    price_rows.append(p)
    meta.append((tk, len(p), str(p["date"].min().date()), str(p["date"].max().date()), "OK"))

if not price_rows or not mkt_rows:
    raise ValueError("Không có đủ lịch sử crypto hợp lệ trong nguồn đầu vào.")
crypto = pd.concat(price_rows, ignore_index=True).drop_duplicates(["ticker","date"])
market = pd.concat(mkt_rows,  ignore_index=True).drop_duplicates(["ticker","date"])
crypto = crypto.sort_values(["ticker","date"]); market = market.sort_values(["ticker","date"])
log(f"    fact_crypto_daily : {len(crypto):,} dong / {crypto.ticker.nunique()} coin")
log(f"    fact_market_daily : {len(market):,} dong / {market.ticker.nunique()} coin")

# ============================== 2. LAM SACH ==============================
log("2/6 Lam sach: missing value, outlier, chuan hoa")
# Giá thiếu/không dương đã bị loại ở bước đọc; không nội suy giá để tránh tạo lợi suất giả.
# Các biến on-chain thiếu có hệ thống được giữ NaN; macro được forward-fill có giới hạn bên dưới.
crypto["log_return"] = crypto.groupby("ticker")["price_usd"].transform(lambda s: np.log(s).diff())
z = crypto.groupby("ticker")["log_return"].transform(lambda s: (s - s.mean()) / s.std())
crypto["zscore_return"] = z.round(3)
crypto["is_outlier"] = (z.abs() > 4).astype(int)   # DANH DAU, khong xoa
n_out = int(crypto["is_outlier"].sum())
log(f"    danh dau {n_out:,} ngay outlier (|z|>4) - giu lai vi la su kien thi truong that")

# ========================= 3. CALCULATED FIELDS =========================
log("3/6 Tao truong tinh toan")
g = crypto.groupby("ticker")
crypto["daily_return_pct"]  = g["price_usd"].pct_change(fill_method=None) * 100
crypto["ma7"]               = g["price_usd"].transform(lambda s: s.rolling(7).mean())
crypto["ma30"]              = g["price_usd"].transform(lambda s: s.rolling(30).mean())
crypto["ma90"]              = g["price_usd"].transform(lambda s: s.rolling(90).mean())
crypto["volatility_30d"]    = g["log_return"].transform(lambda s: s.rolling(30).std()*np.sqrt(365)*100)
crypto["drawdown_pct"]      = g["price_usd"].transform(lambda s: (s/s.cummax()-1)*100)
crypto["volume_ma30"]       = g["volume_usd"].transform(lambda s: s.rolling(30).mean())
crypto["turnover_ratio"]    = crypto["volume_usd"] / crypto["market_cap_usd"].where(crypto["market_cap_usd"] > 0)
crypto["net_exchange_flow"] = crypto["exchange_inflow_usd"] - crypto["exchange_outflow_usd"]
crypto["year"]              = crypto["date"].dt.year
crypto["month"]             = crypto["date"].dt.to_period("M").astype(str)
crypto["is_up_day"] = (crypto["daily_return_pct"] > 0).astype("Int64").where(crypto["daily_return_pct"].notna())

# BTC dominance theo ngay (tu bang market)
tot = market.groupby("date")["market_cap_usd"].sum().rename("total_mcap")
btc = market[market.ticker=="BTC"].set_index("date")["market_cap_usd"].rename("btc_mcap")
dom = pd.concat([tot, btc], axis=1)
dom["btc_dominance_pct"] = dom["btc_mcap"] / dom["total_mcap"] * 100
dom = dom.reset_index()

# ============================== 4. MACRO ==============================
log("4/6 Dung bang vi mo theo ngay")
def rd(p, **k):
    """Lưu số dòng nguồn để minh chứng rubric và kiểm tra dữ liệu đầu vào."""
    frame = pd.read_csv(RAW / "macro" / p, encoding="utf-8-sig", **k)
    raw_counts[f"macro/{p}"] = len(frame)
    return frame

vix = rd("vix_daily.csv"); vix["date"] = pd.to_datetime(vix["DATE"])
vix = vix[["date","CLOSE"]].rename(columns={"CLOSE":"vix"})

brent = rd("brent_daily.csv"); brent["date"] = pd.to_datetime(brent["Date"])
brent = brent[["date","Price"]].rename(columns={"Price":"brent_oil"})

# --- Chi so USD (DXY) tinh tu ty gia hang ngay, trong so chuan ICE ---
fx = rd("fx_daily.csv"); fx["date"] = pd.to_datetime(fx["Date"])
W = {"Euro":.576, "Japan":.136, "United Kingdom":.119,
     "Canada":.091, "Sweden":.042, "Switzerland":.036}
w = fx[fx["Country"].isin(W)].pivot_table(index="date", columns="Country", values="Exchange rate")
w = w.dropna()
dxy = 50.14348112 * np.exp(sum(np.log(w[c]) * W[c] for c in W))
dxy = dxy.rename("dxy").reset_index()

sp = rd("sp500_monthly.csv"); sp["date"] = pd.to_datetime(sp["Date"])
sp = sp[["date","SP500","Long Interest Rate","PE10"]].rename(
        columns={"SP500":"sp500","Long Interest Rate":"us10y_yield","PE10":"sp500_pe10"})
# Nguồn Shiller điền 0 cho cột chưa cập nhật; không coi đó là lãi suất/PE thật.
sp["sp500_pe10"] = sp["sp500_pe10"].where(sp["sp500_pe10"] > 0)
yield_source = RAW / "macro" / "us10y_monthly.csv"
if yield_source.exists():
    y10 = rd("us10y_monthly.csv")
    y10["date"] = pd.to_datetime(y10["Date"])
    y10 = y10[["date", "Rate"]].rename(columns={"Rate": "us10y_source"})
    sp = sp.merge(y10, on="date", how="outer", validate="one_to_one")
    sp["us10y_yield"] = sp["us10y_source"].combine_first(sp["us10y_yield"].where(sp["us10y_yield"] > 0))
    sp = sp.drop(columns="us10y_source")
else:
    sp["us10y_yield"] = sp["us10y_yield"].where(sp["us10y_yield"] > 0)

gold = rd("gold_monthly.csv"); gold["date"] = pd.to_datetime(gold["Date"], format="%Y-%m")
gold = gold.rename(columns={"Price":"gold_usd"})[["date","gold_usd"]]

cpi = rd("cpi_us_monthly.csv"); cpi["date"] = pd.to_datetime(cpi["Date"])
cpi = cpi.rename(columns={"Index":"cpi_index","Inflation":"cpi_mom_pct"}).sort_values("date")
# LUU Y: cot Inflation cua nguon la thang-so-thang (MoM). YoY phai tu tinh tu chi so.
cpi["cpi_yoy_pct"] = cpi["cpi_index"].pct_change(12, fill_method=None) * 100
cpi = cpi[["date","cpi_index","cpi_mom_pct","cpi_yoy_pct"]]

macro = None
for df in [vix, brent, dxy, sp, gold, cpi]:
    macro = df if macro is None else macro.merge(df, on="date", how="outer")
macro = macro.sort_values("date").set_index("date")
macro = macro.resample("D").mean()
_mth = ["sp500","us10y_yield","sp500_pe10","gold_usd","cpi_index","cpi_mom_pct","cpi_yoy_pct"]
macro[_mth] = macro[_mth].ffill(limit=62)
macro[["vix","brent_oil","dxy"]] = macro[["vix","brent_oil","dxy"]].ffill(limit=5)
macro = macro.loc["2013-01-01":]
macro["dxy_ret"]    = macro["dxy"].pct_change(fill_method=None)*100
# Giữ trường tương thích để mô tả; không dùng cửa sổ chồng lấn này để kiểm định tương quan.
macro["sp500_chg_30d"] = macro["sp500"].pct_change(30, fill_method=None)*100
macro["gold_chg_30d"]  = macro["gold_usd"].pct_change(30, fill_method=None)*100
macro["real_rate"]  = macro["us10y_yield"] - macro["cpi_yoy_pct"]
macro["risk_regime"]= np.where(macro["vix"]>25,"Risk-off", np.where(macro["vix"]<15,"Risk-on","Trung tinh"))
macro.loc[macro["vix"].isna(), "risk_regime"] = pd.NA
macro = macro.reset_index()
log(f"    fact_macro_daily  : {len(macro):,} dong x {macro.shape[1]} cot")

# ============================== 5. QUOC GIA ==============================
log("5/6 Dung tang quoc gia (phuc vu ban do)")
# LƯU Ý: mã châu lục của Bắc Mỹ là chuỗi "NA". Nếu để pandas đọc mặc định,
# nó bị hiểu thành giá trị rỗng (NaN) và toàn bộ quốc gia Bắc Mỹ mất châu lục.
# Vì vậy phải tắt danh sách NA mặc định và chỉ coi chuỗi rỗng là thiếu.
cc = pd.read_csv(f"{RAW}/country/country_codes.csv", low_memory=False,
                 keep_default_na=False, na_values=[""], encoding="utf-8-sig")
dim_country = cc[["ISO3166-1-Alpha-3","ISO3166-1-Alpha-2","official_name_en","Region Name",
                  "Sub-region Name","Continent","Capital","ISO4217-currency_alphabetic_code",
                  "Least Developed Countries (LDC)"]].copy()
dim_country.columns = ["iso3","iso2","country_name","region","sub_region","continent",
                       "capital","currency_code","is_ldc"]
dim_country = dim_country.dropna(subset=["iso3"]).drop_duplicates("iso3")
dim_country["is_ldc"] = dim_country["is_ldc"].notna().astype(int)

cpi_c = pd.read_csv(f"{RAW}/country/wb_cpi.csv", encoding="utf-8-sig").rename(
        columns={"Country Code":"iso3","Year":"year","CPI":"inflation_pct"})[["iso3","year","inflation_pct"]]
gdp_c = pd.read_csv(f"{RAW}/country/wb_gdp.csv", encoding="utf-8-sig").rename(
        columns={"Country Code":"iso3","Year":"year","Value":"gdp_usd"})[["iso3","year","gdp_usd"]]
pop_c = pd.read_csv(f"{RAW}/country/wb_population.csv", encoding="utf-8-sig").rename(
        columns={"Country Code":"iso3","Year":"year","Value":"population"})[["iso3","year","population"]]

cpanel = cpi_c.merge(gdp_c, on=["iso3","year"], how="outer").merge(pop_c, on=["iso3","year"], how="outer")
cpanel = cpanel[cpanel["iso3"].isin(set(dim_country["iso3"]))]      # loai nhom tong hop (World, EU...)
cpanel = cpanel[(cpanel["year"] >= 2013) & (cpanel["year"] <= 2024)]
cpanel["gdp_per_capita_usd"] = cpanel["gdp_usd"] / cpanel["population"]
cpanel["log_gdp_per_capita"] = np.log(cpanel["gdp_per_capita_usd"].clip(lower=1))
cpanel["high_inflation"] = (cpanel["inflation_pct"] > 10).astype("Int64").where(cpanel["inflation_pct"].notna())
cpanel["has_gdp"] = cpanel["gdp_usd"].notna().astype(int)   # GDP World Bank chi day du den 2023
cpanel = cpanel.merge(dim_country, on="iso3", how="left").sort_values(["iso3","year"])
log(f"    fact_country_macro: {len(cpanel):,} dong x {cpanel.shape[1]} cot / {cpanel.iso3.nunique()} quoc gia")

# ty gia hang ngay theo quoc gia -> bang fact thu 2 co chieu dia ly
fxd = fx[fx["date"] >= "2013-01-01"].rename(columns={"Country":"country_fx","Exchange rate":"fx_per_usd"})
fxd = fxd[["date","country_fx","fx_per_usd"]]
log(f"    fact_fx_daily     : {len(fxd):,} dong / {fxd.country_fx.nunique()} quoc gia")

# ============================== 6. JOIN + XUAT ==============================
log("6/6 Join va xuat ket qua")
crypto = crypto.merge(macro, on="date", how="left", validate="many_to_one")
crypto = crypto.merge(dom[["date","btc_dominance_pct","total_mcap"]], on="date", how="left", validate="many_to_one")
dim_coin = (market.groupby("ticker")
            .agg(first_date=("date","min"), last_date=("date","max"),
                 n_days=("date","count"), latest_mcap=("market_cap_usd","last"),
                 avg_volume=("volume_usd","mean")).reset_index())
dim_coin["category"] = dim_coin["ticker"].map(CATEGORY).fillna("Khac")
dim_coin["mcap_rank"] = dim_coin["latest_mcap"].rank(ascending=False, method="min")
dim_coin["has_price_history"] = dim_coin["ticker"].isin(crypto["ticker"].unique()).astype(int)
crypto = crypto.merge(dim_coin[["ticker","category","mcap_rank"]], on="ticker", how="left", validate="many_to_one")

num = crypto.select_dtypes("float").columns
crypto[num] = crypto[num].round(6)

tables = {"fact_crypto_daily": crypto, "fact_market_daily": market,
          "fact_macro_daily": macro, "fact_country_macro": cpanel,
          "fact_fx_daily": fxd, "dim_coin": dim_coin, "dim_country": dim_country}

# Kiểm tra grain trước khi ghi: một join lỗi không được âm thầm nhân bản số dòng.
keys = {"fact_crypto_daily": ["ticker", "date"], "fact_market_daily": ["ticker", "date"],
        "fact_macro_daily": ["date"], "fact_country_macro": ["iso3", "year"],
        "fact_fx_daily": ["country_fx", "date"], "dim_coin": ["ticker"], "dim_country": ["iso3"]}
quality = {}
for name, df in tables.items():
    if df[keys[name]].isna().any().any() or df.duplicated(keys[name]).any():
        raise ValueError(f"Khóa thiếu hoặc trùng trong {name}: {keys[name]}")
    if np.isinf(df.select_dtypes("number").to_numpy(dtype=float, na_value=np.nan)).any():
        raise ValueError(f"Giá trị vô hạn trong {name}")
    quality[name] = {"rows": len(df), "columns": len(df.columns), "key": keys[name],
                     "duplicate_keys": 0, "missing_by_column": df.isna().sum().to_dict()}
for file in sorted((RAW / "country").glob("*.csv")):
    raw_counts[f"country/{file.name}"] = len(pd.read_csv(file, low_memory=False))
if sum(raw_counts.values()) < 5000 or len(tables) < 3:
    raise ValueError("Dữ liệu chưa đạt quy mô tối thiểu của rubric")
with open(OUT / "_quality_checks.json", "w", encoding="utf-8") as file:
    json.dump({"raw_rows": sum(raw_counts.values()), "raw_sources": raw_counts,
               "tables": quality,
               "missing_policy": "Loại giá thiếu/không dương; giữ NaN on-chain; macro tháng ffill tối đa 62 ngày, ngày tối đa 5 ngày; target thiếu giữ NA.",
               "outlier_policy": "Đánh dấu |z|>4 và giữ sự kiện thị trường; dashboard dùng z-score trượt."},
              file, ensure_ascii=False, indent=2)
summary = []
for name, df in tables.items():
    p = f"{OUT}/{name}.csv"
    df.to_csv(p, index=False)
    if os.path.getsize(p) > 18*1024*1024:      # qua gioi han commit -> nen gzip
        # Cố định gzip mtime để cùng dữ liệu tạo cùng SHA256, tránh làm model
        # bị đánh dấu lỗi thời chỉ vì thời điểm chạy pipeline khác nhau.
        df.to_csv(p + ".gz", index=False, compression={"method": "gzip", "mtime": 0}); os.remove(p); p += ".gz"
    summary.append((name, len(df), df.shape[1], os.path.basename(p),
                    f"{os.path.getsize(p)/1e6:.1f} MB"))

print("\n" + "="*78)
print("KET QUA - KIEM TRA DIEU KIEN RUBRIC")
print("="*78)
print(f"{'Bang':<20}{'Dong':>12}{'Cot':>6}  {'File':<28}{'Size':>9}")
print("-"*78)
tot_rows = 0
for n, r, c, f, s in summary:
    print(f"{n:<20}{r:>12,}{c:>6}  {f:<28}{s:>9}"); tot_rows += r
print("-"*78)
print(f"{'TONG':<20}{tot_rows:>12,}{'':>6}  {len(summary)} bang")
print(f"\n  >= 5.000 dong ?        {'DAT' if tot_rows>=5000 else 'CHUA'}  ({tot_rows:,})")
print(f"  >= 3 bang ?            {'DAT' if len(summary)>=3 else 'CHUA'}  ({len(summary)} bang)")
print(f"  Co ISO3 cho ban do ?   {'DAT' if 'iso3' in cpanel.columns else 'CHUA'}  ({cpanel.iso3.nunique()} quoc gia)")
print(f"  Co bien Logistic ?     DAT  (is_up_day, high_inflation)")
print("="*78)
with open(OUT / "_summary.json", "w", encoding="utf-8") as file:
    json.dump([{"bang":n,"dong":r,"cot":c,"file":f} for n,r,c,f,_ in summary],
              file, ensure_ascii=False, indent=2)
