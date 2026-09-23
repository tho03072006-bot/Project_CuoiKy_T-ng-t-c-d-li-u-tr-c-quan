"""
03 - Bu 2 cot ma dataset Kaggle KHONG co: volume va market cap.
  - Volume + so lenh khop: Binance public data (khong can key, lich su day du)
  - Metadata coin + market cap hien tai: CoinGecko /coins/markets (1 lan goi)
Ket qua: data/interim/fact_volume_daily.csv  va  data/interim/dim_coin.csv
"""
import time
import pandas as pd
from _common import INTERIM, get, log

# Dung mirror du lieu cong khai cua Binance: on dinh hon, khong chan theo vung
BINANCE = "https://data-api.binance.vision/api/v3/klines"

# Top coin co cap USDT tren Binance. Them/bot tuy nhom.
SYMBOLS = ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "AVAX",
           "MATIC", "LINK", "LTC", "TRX", "ATOM", "UNI", "XLM", "ETC", "FIL",
           "NEAR", "ALGO", "AAVE", "SAND", "MANA", "AXS", "EGLD", "FTM",
           "CHZ", "GALA", "CRV", "COMP"]

START_MS = int(pd.Timestamp("2017-08-01").timestamp() * 1000)  # Binance mo tu 2017

def fetch_klines(symbol):
    """Lay toan bo nen ngay cua 1 cap. Binance tra toi da 1000 nen/lan."""
    out, start = [], START_MS
    while True:
        data = get(BINANCE, params={"symbol": f"{symbol}USDT", "interval": "1d",
                                    "startTime": start, "limit": 1000})
        if not data:
            break
        out.extend(data)
        if len(data) < 1000:
            break
        start = data[-1][0] + 86_400_000   # tiep tu nen ke tiep
        time.sleep(0.3)                    # ton trong rate limit
    return out

frames = []
for sym in SYMBOLS:
    try:
        log(f"Binance {sym}USDT")
        kl = fetch_klines(sym)
        if not kl:
            log(f"  bo qua {sym} (khong co du lieu)")
            continue
        df = pd.DataFrame(kl, columns=[
            "open_time", "o", "h", "l", "c", "volume", "close_time",
            "quote_volume", "trade_count", "tb_base", "tb_quote", "ignore"])
        df["date"] = pd.to_datetime(df["open_time"], unit="ms").dt.normalize()
        df["ticker"] = sym
        for col in ["volume", "quote_volume", "trade_count"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        frames.append(df[["date", "ticker", "volume", "quote_volume", "trade_count"]])
    except Exception as e:
        log(f"  LOI {sym}: {e}")

vol = pd.concat(frames, ignore_index=True).drop_duplicates(["date", "ticker"])
vol.to_csv(INTERIM / "fact_volume_daily.csv", index=False)
log(f"XONG volume -> {len(vol):,} dong, {vol['ticker'].nunique()} coin")

# --- Metadata coin tu CoinGecko (dim_coin) ---
log("CoinGecko /coins/markets")
rows = []
for page in (1, 2):
    js = get("https://api.coingecko.com/api/v3/coins/markets",
             params={"vs_currency": "usd", "order": "market_cap_desc",
                     "per_page": 250, "page": page, "sparkline": "false"})
    rows.extend(js)
    time.sleep(8)      # free tier: ~10-30 request/phut

dim = pd.DataFrame(rows)[[
    "id", "symbol", "name", "market_cap", "market_cap_rank", "total_volume",
    "circulating_supply", "total_supply", "max_supply",
    "ath", "ath_date", "atl", "atl_date"]]
dim["ticker"] = dim["symbol"].str.upper()
dim.to_csv(INTERIM / "dim_coin.csv", index=False)
log(f"XONG dim_coin -> {len(dim):,} coin")
