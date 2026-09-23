"""
02 - Tai chi so vi mo theo QUOC GIA tu World Bank API (khong can key).
Day la tang du lieu phuc vu BAN DO (yeu cau bat buoc cua rubric).
Ket qua: data/interim/dim_country_wb.csv  va  data/interim/fact_country_macro.csv
"""
import pandas as pd
from _common import RAW, INTERIM, get, log

YEARS = "2013:2025"

INDICATORS = {
    "FP.CPI.TOTL.ZG":        "inflation_pct",        # Lam phat CPI (%/nam)
    "NY.GDP.PCAP.CD":        "gdp_per_capita_usd",   # GDP binh quan dau nguoi
    "IT.NET.USER.ZS":        "internet_users_pct",   # % dan so dung Internet
    "BX.TRF.PWKR.DT.GD.ZS":  "remittance_gdp_pct",   # Kieu hoi / GDP
    "FM.LBL.BMNY.GD.ZS":     "broad_money_gdp_pct",  # Cung tien rong / GDP
    "PA.NUS.FCRF":           "fx_rate_per_usd",      # Ty gia noi te/USD
    "NY.GDP.MKTP.KD.ZG":     "gdp_growth_pct",       # Tang truong GDP
    "SL.UEM.TOTL.ZS":        "unemployment_pct",     # That nghiep
}

# --- 1. Danh muc quoc gia (co lat/long -> dung cho bubble map) ---
log("Tai danh muc quoc gia World Bank")
js = get("https://api.worldbank.org/v2/country",
         params={"format": "json", "per_page": 400})
rows = []
for c in js[1]:
    # region.id == 'NA' nghia la dong nay la nhom tong hop (World, EU...), bo di
    if c["region"]["id"] == "NA":
        continue
    rows.append({
        "iso3": c["id"],
        "iso2": c["iso2Code"],
        "country_name": c["name"],
        "region": c["region"]["value"],
        "income_level": c["incomeLevel"]["value"],
        "capital_city": c["capitalCity"],
        "longitude": pd.to_numeric(c["longitude"], errors="coerce"),
        "latitude": pd.to_numeric(c["latitude"], errors="coerce"),
    })
dim = pd.DataFrame(rows)
dim.to_csv(INTERIM / "dim_country_wb.csv", index=False)
log(f"  -> {len(dim)} quoc gia thuc (da loai cac nhom tong hop)")

valid_iso3 = set(dim["iso3"])

# --- 2. Cac chi so theo quoc gia x nam ---
panel = None
for code, name in INDICATORS.items():
    log(f"Tai World Bank {code} ({name})")
    js = get(f"https://api.worldbank.org/v2/country/all/indicator/{code}",
             params={"format": "json", "date": YEARS, "per_page": 20000})
    if len(js) < 2 or js[1] is None:
        log(f"  CANH BAO: khong co du lieu cho {code}")
        continue
    df = pd.DataFrame([{
        "iso3": r["countryiso3code"],
        "year": int(r["date"]),
        name: r["value"],
    } for r in js[1] if r["countryiso3code"] in valid_iso3])
    df = df.dropna(subset=["iso3"]).drop_duplicates(["iso3", "year"])
    panel = df if panel is None else panel.merge(df, on=["iso3", "year"], how="outer")

panel = panel.sort_values(["iso3", "year"])
panel.to_csv(INTERIM / "fact_country_macro.csv", index=False)
log(f"XONG -> fact_country_macro.csv ({len(panel):,} dong x {panel.shape[1]} cot)")
