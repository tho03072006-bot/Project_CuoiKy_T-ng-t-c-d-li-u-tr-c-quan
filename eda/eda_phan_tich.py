# -*- coding: utf-8 -*-
"""
KHÁM PHÁ DỮ LIỆU (EDA) — Đề tài 09: Thị trường Crypto & chỉ số vĩ mô
Tương ứng mục 1.4 của barem (0.75 điểm): "Dùng Matplotlib/Seaborn vẽ ít nhất 3-5
biểu đồ tĩnh để phân tích PHÂN PHỐI dữ liệu trước khi đưa lên Dashboard".

Xuất ra: eda/hinh/H01..H10.png  +  eda/ket_qua_thong_ke.json
Chạy:    python eda_phan_tich.py
"""
import json, os, sys
import numpy as np
import pandas as pd
import matplotlib
# Xuất PNG không cần cửa sổ GUI/Tcl; chạy được cả khi kiểm thử tự động.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eda_style import (apply_style, tidy, caption, tieu_de_2_dong, SURFACE, INK,
                       INK_SOFT, GRID, C1_BLUE, C2_ORANGE, C3_AQUA, C4_YELLOW,
                       C8_RED, SEQ_BLUE, DIVERGING)

apply_style()

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, "..", "data", "processed"))
FIG  = os.path.join(HERE, "hinh"); os.makedirs(FIG, exist_ok=True)
NGUON = ("Nguồn: Coin Metrics Community Data; World Bank; CBOE; Core Datasets. "
         "Truy cập 21/09/2026.")
KQ = {}

def save(fig, ten):
    """Xuất hình và giải phóng bộ nhớ để chạy đủ 10 hình trong cùng một lượt."""
    fig.savefig(os.path.join(FIG, ten), dpi=150, bbox_inches="tight")
    plt.close(fig); print(f"    -> {ten}")

print("[*] Nạp dữ liệu")
crypto  = pd.read_csv(f"{PROC}/fact_crypto_daily.csv.gz", parse_dates=["date"])
macro   = pd.read_csv(f"{PROC}/fact_macro_daily.csv",     parse_dates=["date"])
market  = pd.read_csv(f"{PROC}/fact_market_daily.csv",    parse_dates=["date"])
# "NA" là mã châu lục của Bắc Mỹ, không phải giá trị thiếu — phải tắt NA mặc định
country = pd.read_csv(f"{PROC}/fact_country_macro.csv",
                      keep_default_na=False, na_values=[""])
dcoin   = pd.read_csv(f"{PROC}/dim_coin.csv", parse_dates=["first_date", "last_date"])
btc = crypto[crypto.ticker == "BTC"].set_index("date").sort_index()
eth = crypto[crypto.ticker == "ETH"].set_index("date").sort_index()

# ══════════════════════════════════════════════════════════════════════
# H01 — ĐỘ PHỦ DỮ LIỆU THEO THỜI GIAN
# 39 đồng coin có lịch sử dài ngắn rất khác nhau → giải thích vì sao phải
# chọn mốc cắt mẫu chung khi so sánh giữa các coin.
# ══════════════════════════════════════════════════════════════════════
print("[*] H01 Độ phủ dữ liệu")
# Độ phủ GIÁ lấy từ bảng giá, vì dim_coin đo độ phủ vốn hóa/volume có thể dài hơn.
d = (crypto.groupby("ticker").agg(first_date=("date", "min"), last_date=("date", "max"),
                                  n_days=("date", "size")).reset_index().sort_values("first_date"))
fig, ax = plt.subplots(figsize=(9.5, 8.8))
y = np.arange(len(d))
ax.barh(y, (d.last_date - d.first_date).dt.days, left=d.first_date,
        height=0.62, color=C1_BLUE, alpha=0.8, zorder=3)
for tk, col in [("BTC", C2_ORANGE), ("ETH", C4_YELLOW)]:   # chỉ tô đậm 2 coin trọng tâm
    i = list(d.ticker).index(tk)
    ax.barh(i, (d.last_date.iloc[i] - d.first_date.iloc[i]).days,
            left=d.first_date.iloc[i], height=0.62, color=col, zorder=4)
ax.set_yticks(y); ax.set_yticklabels(d.ticker, fontsize=7.5)
ax.set_ylim(-1, len(d)); ax.invert_yaxis(); ax.set_xlabel("Năm")
tieu_de_2_dong(ax, "H01. Độ phủ dữ liệu giá theo từng đồng coin",
    f"{len(d)} đồng coin, lịch sử trải từ {d.first_date.min().year} đến {d.last_date.max().year}. Coin có ít nhất "
    f"{int(d.n_days.min()):,} ngày, nhiều nhất {int(d.n_days.max()):,} ngày — "
    "chênh lệch này buộc phải chọn mốc cắt mẫu chung khi so sánh.", rong=88, dy=1.012)
tidy(ax, grid_axis="x")
caption(fig, NGUON + "  BTC tô cam, ETH tô vàng để dễ đối chiếu.")
save(fig, "H01_do_phu_du_lieu.png")
KQ["do_phu"] = {"so_coin": int(len(d)), "so_ngay_it_nhat": int(d.n_days.min()),
                "so_ngay_nhieu_nhat": int(d.n_days.max())}

# ══════════════════════════════════════════════════════════════════════
# H02 — TỶ LỆ THIẾU DỮ LIỆU THEO CỘT
# ══════════════════════════════════════════════════════════════════════
print("[*] H02 Tỷ lệ thiếu dữ liệu")
cols = {"price_usd": "Giá USD", "market_cap_usd": "Vốn hoá", "volume_usd": "Khối lượng",
        "supply": "Lượng cung", "active_addresses": "Địa chỉ hoạt động",
        "tx_count": "Số giao dịch", "hashrate": "Hashrate", "mvrv": "MVRV",
        "exchange_inflow_usd": "Dòng tiền vào sàn", "vix": "VIX", "dxy": "Chỉ số USD",
        "cpi_yoy_pct": "Lạm phát Mỹ", "sp500": "S&P 500", "gold_usd": "Giá vàng",
        "btc_dominance_pct": "Thị phần BTC"}
miss = (crypto[list(cols)].isna().mean() * 100).rename(cols).sort_values()
fig, ax = plt.subplots(figsize=(8.6, 5.8))
ax.barh(miss.index, miss.values, color=C1_BLUE, height=0.62, zorder=3)
for i, v in enumerate(miss.values):
    ax.text(v + 1.2, i, f"{v:.1f}%", va="center", fontsize=8.5, color=INK_SOFT)
ax.set_xlim(0, max(miss.values) * 1.25)
ax.set_xlabel("Tỷ lệ giá trị thiếu (%)")
tieu_de_2_dong(ax, "H02. Tỷ lệ thiếu dữ liệu theo từng cột",
    "Cột giá và khối lượng gần như đầy đủ. Các cột on-chain thiếu nhiều vì không "
    "phải blockchain nào cũng công bố — đây là thiếu có hệ thống, không phải lỗi.",
    rong=84, dy=1.02)
tidy(ax, grid_axis="x"); caption(fig, NGUON)
save(fig, "H02_ty_le_thieu.png")
KQ["missing"] = {k: round(float(v), 2) for k, v in miss.items()}

# ══════════════════════════════════════════════════════════════════════
# H03 — PHÂN PHỐI LOG-RETURN: ĐUÔI DÀY
# Biểu đồ quan trọng nhất của phần EDA: chứng minh lợi suất crypto KHÔNG
# tuân theo phân phối chuẩn → không được dùng mean/std một cách ngây thơ.
# ══════════════════════════════════════════════════════════════════════
print("[*] H03 Phân phối log-return")
fig, ax = plt.subplots(figsize=(9, 5.4))
for s, ten, col in [(btc.log_return.dropna(), "BTC", C1_BLUE),
                    (eth.log_return.dropna(), "ETH", C2_ORANGE)]:
    ax.hist(s * 100, bins=140, range=(-25, 25), density=True,
            color=col, alpha=0.45, label=ten, zorder=3)
x = np.linspace(-25, 25, 400); b = btc.log_return.dropna() * 100
ax.plot(x, stats.norm.pdf(x, b.mean(), b.std()), color=INK, lw=1.5,
        ls=(0, (5, 2.5)), label="Phân phối chuẩn tương ứng", zorder=5)
ax.set_xlabel("Log-return theo ngày (%)"); ax.set_ylabel("Mật độ")
ax.set_xlim(-25, 25)
tieu_de_2_dong(ax, "H03. Lợi suất ngày có đuôi dày hơn phân phối chuẩn",
    "Đỉnh nhọn hơn và hai đuôi dày hơn đường đứt nét: những ngày biến động cực "
    "đoan xảy ra thường xuyên hơn nhiều so với mô hình chuẩn dự báo.",
    rong=82, dy=1.02)
ax.legend(loc="upper right"); tidy(ax); caption(fig, NGUON)
save(fig, "H03_phan_phoi_log_return.png")
for ten, s in [("BTC", btc.log_return.dropna()), ("ETH", eth.log_return.dropna())]:
    jb, p = stats.jarque_bera(s)
    KQ.setdefault("phan_phoi", {})[ten] = {
        "do_lech_skew": round(float(stats.skew(s)), 3),
        "do_nhon_kurtosis": round(float(stats.kurtosis(s)), 2),
        "jarque_bera": round(float(jb), 1), "p_value": float(p),
        "ket_luan": "Bác bỏ giả thuyết phân phối chuẩn" if p < 0.05 else "Không bác bỏ"}

# ══════════════════════════════════════════════════════════════════════
# H04 — QQ PLOT: kiểm định trực quan tính chuẩn
# ══════════════════════════════════════════════════════════════════════
print("[*] H04 QQ plot")
fig, ax = plt.subplots(figsize=(6.8, 5.8))
(osm, osr), (slope, inter, r) = stats.probplot(btc.log_return.dropna(), dist="norm")
ax.scatter(osm, osr * 100, s=7, color=C1_BLUE, alpha=0.5, zorder=3, edgecolors="none")
ax.plot(osm, (slope * osm + inter) * 100, color=C8_RED, lw=1.6, zorder=4,
        label="Đường kỳ vọng nếu phân phối chuẩn")
ax.set_xlabel("Phân vị lý thuyết (phân phối chuẩn)")
ax.set_ylabel("Phân vị thực tế của BTC (%)")
tieu_de_2_dong(ax, "H04. Biểu đồ QQ — lợi suất BTC so với phân phối chuẩn",
    "Hai đầu cong hẳn ra khỏi đường đỏ: các ngày cực đoan mạnh hơn nhiều so với "
    "mô hình chuẩn. Log-return vẫn có đuôi dày; cần xem thêm phân vị và drawdown khi đánh giá rủi ro.",
    rong=72, dy=1.02)
ax.legend(loc="upper left"); tidy(ax, grid_axis="both"); caption(fig, NGUON)
save(fig, "H04_qq_plot.png")

# ══════════════════════════════════════════════════════════════════════
# H05 — BIẾN ĐỘNG 30 NGÀY THEO NĂM (box plot)
# ══════════════════════════════════════════════════════════════════════
print("[*] H05 Biến động theo năm")
v = btc[["volatility_30d"]].dropna().copy(); v["nam"] = v.index.year
v = v[v.nam.between(2013, 2026)]
fig, ax = plt.subplots(figsize=(9.6, 5.2))
sns.boxplot(data=v, x="nam", y="volatility_30d", ax=ax, color=C1_BLUE, width=0.62,
            linewidth=1.0, fliersize=2, boxprops=dict(alpha=0.72), zorder=3)
med = v.groupby("nam")["volatility_30d"].median()
ax.set_xlabel("Năm"); ax.set_ylabel("Biến động 30 ngày, năm hoá (%)")
tieu_de_2_dong(ax, "H05. Biến động của Bitcoin giảm dần qua các năm",
    f"Trung vị giảm từ {med.iloc[0]:.0f}% năm {med.index[0]} xuống "
    f"{med.iloc[-1]:.0f}% năm {med.index[-1]}. Biến động không ổn định theo thời "
    "gian, nên mọi thống kê tính trên toàn bộ mẫu đều che mất sự khác biệt này.",
    rong=90, dy=1.02)
tidy(ax); caption(fig, NGUON + f" Năm {btc.index.max().year} chỉ có dữ liệu đến {btc.index.max():%d/%m}.")
save(fig, "H05_bien_dong_theo_nam.png")
KQ["bien_dong_trung_vi_theo_nam"] = {int(k): round(float(x), 1) for k, x in med.items()}

# ══════════════════════════════════════════════════════════════════════
# H06 — PHÂN PHỐI VỐN HOÁ THEO NHÓM COIN (thang log)
# Nhóm coin là biến ĐỊNH DANH không có thứ tự → dùng MỘT màu cho tất cả,
# không tô đậm theo giá trị (đó là lỗi "value-ramp trên biến định danh").
# ══════════════════════════════════════════════════════════════════════
print("[*] H06 Vốn hoá theo nhóm")
TEN_NHOM = {"Layer 1": "Layer 1", "DeFi": "DeFi", "Stablecoin": "Stablecoin",
            "Payment": "Thanh toán", "Meme": "Meme", "Privacy": "Riêng tư",
            "Layer 2": "Layer 2", "Gaming": "Game", "Metaverse": "Metaverse",
            "Storage": "Lưu trữ", "Oracle": "Oracle", "Utility": "Tiện ích",
            "Infrastructure": "Hạ tầng", "Khac": "Khác"}
m = market.merge(dcoin[["ticker", "category"]], on="ticker", how="left")
m = m[(m.date >= "2024-01-01") & (m.market_cap_usd > 0)].copy()
m["nhom"] = m.category.map(TEN_NHOM).fillna("Khác")
thu_tu = m.groupby("nhom")["market_cap_usd"].median().sort_values(ascending=False).index
fig, ax = plt.subplots(figsize=(9, 5.6))
sns.boxplot(data=m, y="nhom", x="market_cap_usd", order=thu_tu, ax=ax, color=C1_BLUE,
            width=0.6, linewidth=1.0, fliersize=1.5, boxprops=dict(alpha=0.72), zorder=3)
ax.set_xscale("log"); ax.set_xlabel("Vốn hoá (USD, thang log)"); ax.set_ylabel("")
lo, hi = m.market_cap_usd.min(), m.market_cap_usd.max()
so_bac = np.log10(hi / lo)
tieu_de_2_dong(ax, "H06. Vốn hoá thị trường lệch rất mạnh giữa các nhóm coin",
    f"Trục log trải dài {so_bac:.0f} bậc độ lớn, từ {lo/1e6:.1f} triệu đến "
    f"{hi/1e12:.2f} nghìn tỷ USD. Đây là lý do mọi biểu đồ vốn hoá trên dashboard "
    "đều phải dùng thang log — thang tuyến tính sẽ bóp toàn bộ nhóm nhỏ về 0.",
    rong=86, dy=1.025)
tidy(ax, grid_axis="x"); caption(fig, NGUON + " Dữ liệu từ 01/2024.")
save(fig, "H06_von_hoa_theo_nhom.png")

# ══════════════════════════════════════════════════════════════════════
# BẢNG THÁNG — nền tảng cho H07 và H08
#
# QUYẾT ĐỊNH QUAN TRỌNG: không dùng cửa sổ 30 ngày trượt theo từng ngày.
# Cửa sổ trượt làm các quan sát chồng lấn nhau tới 29/30, khiến hệ số tương
# quan và mức ý nghĩa bị THỔI PHỒNG. Ví dụ cụ thể trong chính dữ liệu này:
# BTC ↔ S&P 500 cho r = 0.37 nếu dùng cửa sổ trượt, nhưng chỉ còn r = 0.22
# khi dùng quan sát tháng độc lập. Con số 0.22 mới là con số đúng.
# Ngoài ra S&P 500, vàng, CPI, lợi suất 10 năm vốn là dữ liệu THÁNG.
# ══════════════════════════════════════════════════════════════════════
print("[*] Dựng bảng tháng (quan sát độc lập)")
thang = pd.DataFrame({
    "BTC":   btc.price_usd.resample("ME").last(),
    "ETH":   eth.price_usd.reindex(btc.index).resample("ME").last(),
    "sp500": btc.sp500.resample("ME").last(),
    "gold":  btc.gold_usd.resample("ME").last(),
    "VIX":   btc.vix.resample("ME").mean(),
    "dxy":   btc.dxy.resample("ME").last(),
    "cpi":   btc.cpi_yoy_pct.resample("ME").last(),
    "y10":   btc.us10y_yield.resample("ME").last(),
    "real":  btc.real_rate.resample("ME").last(),
    "brent": btc.brent_oil.resample("ME").last(),
})
# Không coi tháng cuối mới có 23 ngày là tháng đầy đủ; returns tính trước cắt mốc 2018.
last_complete_month = btc.index.max().to_period("M")
if btc.index.max().normalize() < last_complete_month.end_time.normalize():
    last_complete_month -= 1
thang = thang.loc[thang.index.to_period("M") <= last_complete_month]
for k in ["BTC", "ETH", "sp500", "gold"]:
    thang[k + "_pct"] = thang[k].pct_change(fill_method=None) * 100
thang = thang.loc["2018":]
TEN = {"BTC_pct": "BTC", "ETH_pct": "ETH", "sp500_pct": "S&P 500", "gold_pct": "Vàng",
       "VIX": "VIX", "dxy": "Chỉ số USD", "cpi": "Lạm phát Mỹ",
       "y10": "Lợi suất 10 năm", "real": "Lãi suất thực", "brent": "Dầu Brent"}
mt = thang[list(TEN)].dropna().rename(columns=TEN)
print(f"    {len(mt)} quan sát tháng, từ {mt.index[0]:%m/%Y} đến {mt.index[-1]:%m/%Y}")

# ══════════════════════════════════════════════════════════════════════
# H07 — MA TRẬN TƯƠNG QUAN (có đánh dấu ý nghĩa thống kê)
# ══════════════════════════════════════════════════════════════════════
print("[*] H07 Ma trận tương quan")
corr = mt.corr()
pval = pd.DataFrame(np.ones_like(corr), index=corr.index, columns=corr.columns)
for a in mt.columns:
    for b_ in mt.columns:
        if a != b_:
            pval.loc[a, b_] = stats.pearsonr(mt[a], mt[b_])[1]
# p là mức tương thích với H0 dưới giả định kiểm định; không chứng minh nhân quả.
nhan = corr.round(2).astype(str) + np.where(pval < 0.05, "*", "")
np.fill_diagonal(nhan.values, "1.00")

fig, ax = plt.subplots(figsize=(8.8, 7.4))
sns.heatmap(corr, ax=ax, cmap=DIVERGING, vmin=-1, vmax=1, center=0,
            annot=nhan.values, fmt="", annot_kws={"size": 8}, linewidths=2,
            linecolor=SURFACE, cbar_kws={"label": "Hệ số tương quan Pearson",
                                        "shrink": 0.72})
tieu_de_2_dong(ax, "H07. Tương quan giữa crypto và các biến vĩ mô",
    f"{len(mt)} tháng hoàn chỉnh, {mt.index.min():%m/%Y}–{mt.index.max():%m/%Y}. "
    "Dấu *: p < 0,05 trước hiệu chỉnh nhiều kiểm định. Các tháng không chồng lấn "
    "nhưng vẫn có thể tự tương quan; đây là phân tích khám phá, không suy luận nhân quả.", rong=88, dy=1.015)
plt.setp(ax.get_xticklabels(), rotation=42, ha="right")
plt.setp(ax.get_yticklabels(), rotation=0)
caption(fig, NGUON + " Tháng không chồng lấn; p-value chỉ có tính tham khảo.")
save(fig, "H07_ma_tran_tuong_quan.png")
KQ["tuong_quan_thang_BTC"] = {k: {"r": round(float(corr.loc["BTC", k]), 3),
                                  "p": round(float(pval.loc["BTC", k]), 4),
                                  "co_y_nghia": bool(pval.loc["BTC", k] < 0.05)}
                              for k in corr.columns if k != "BTC"}
KQ["so_quan_sat_thang"] = int(len(mt))
KQ["cua_so_thang"] = {"tu": str(mt.index.min().date()), "den": str(mt.index.max().date()),
                         "chi_thang_hoan_chinh": True, "p_value_chua_hieu_chinh_da_kiem_dinh": True}

# ══════════════════════════════════════════════════════════════════════
# H08 — QUAN HỆ BTC ↔ S&P 500
# Chuẩn bị trực tiếp cho mô hình Hồi quy tuyến tính ở phần sau.
# Chỉ dùng 3 màu — ba slot đầu đã kiểm định ở chế độ all-pairs.
# ══════════════════════════════════════════════════════════════════════
print("[*] H08 Quan hệ BTC - S&P 500")
s = mt[["BTC", "S&P 500", "VIX"]].copy()
s["che_do"] = np.where(s.VIX > 25, "Risk-off", np.where(s.VIX < 15, "Risk-on", "Trung tính"))
sl, ic, r, p, se = stats.linregress(s["S&P 500"], s["BTC"])
fig, ax = plt.subplots(figsize=(8.4, 6.4))
for ten, col in [("Risk-off", C8_RED), ("Trung tính", C1_BLUE), ("Risk-on", C3_AQUA)]:
    q = s[s.che_do == ten]
    chu = {"Risk-off": "Risk-off (VIX > 25)", "Trung tính": "Trung tính",
           "Risk-on": "Risk-on (VIX < 15)"}[ten]
    ax.scatter(q["S&P 500"], q["BTC"], s=46, alpha=0.8, color=col,
               label=f"{chu} — {len(q)} tháng", edgecolors=SURFACE,
               linewidths=1.3, zorder=3)
xs = np.linspace(s["S&P 500"].min(), s["S&P 500"].max(), 50)
ax.plot(xs, sl * xs + ic, color=INK, lw=1.8, zorder=5,
        label=f"Hồi quy: hệ số {sl:.2f} · r = {r:.2f} · p = {p:.3f}")
ax.axhline(0, color=GRID, lw=0.8, zorder=1); ax.axvline(0, color=GRID, lw=0.8, zorder=1)
ax.set_xlabel("Biến động S&P 500 trong tháng (%)")
ax.set_ylabel("Biến động BTC trong tháng (%)")
tieu_de_2_dong(ax, "H08. Bitcoin đi cùng chiều với chứng khoán Mỹ",
    f"Hệ số hồi quy cùng tháng = {sl:.2f}; r = {r:.2f}, p = {p:.3f}. "
    f"Mô hình khớp {r**2*100:.1f}% phương sai lợi suất BTC trong mẫu. "
    "Quan hệ đồng thời không chứng minh nhân quả và không phải dự báo ngoài mẫu.", rong=82, dy=1.015)
ax.legend(loc="upper left"); tidy(ax, grid_axis="both")
caption(fig, NGUON + " Mỗi điểm là một tháng hoàn chỉnh, không chồng lấn.")
save(fig, "H08_btc_vs_sp500.png")
KQ["hoi_quy_BTC_SP500"] = {"he_so_goc": round(float(sl), 3), "r": round(float(r), 3),
                           "r_binh_phuong": round(float(r**2), 3), "p_value": float(p),
                           "so_quan_sat_thang": int(len(s))}

# ══════════════════════════════════════════════════════════════════════
# H09 — PHÂN PHỐI LẠM PHÁT THEO CHÂU LỤC (tầng quốc gia)
# Chuẩn bị cho yêu cầu BẢN ĐỒ của rubric.
# ══════════════════════════════════════════════════════════════════════
print("[*] H09 Lạm phát theo châu lục")
TEN_CL = {"AF": "Châu Phi", "AS": "Châu Á", "EU": "Châu Âu", "NA": "Bắc Mỹ",
          "SA": "Nam Mỹ", "OC": "Châu Đại Dương", "AN": "Nam Cực"}
c = country[(country.year == 2023) & country.inflation_pct.notna()].copy()
c["chau_luc"] = c.continent.map(TEN_CL); c = c.dropna(subset=["chau_luc"])
# Cố định jitter để hình tái lập được giữa hai lần chạy cùng dữ liệu.
np.random.seed(42)
thu_tu = c.groupby("chau_luc")["inflation_pct"].median().sort_values(ascending=False).index
fig, ax = plt.subplots(figsize=(9, 5.4))
sns.boxplot(data=c, x="chau_luc", y="inflation_pct", order=thu_tu, ax=ax, color=C1_BLUE,
            width=0.56, linewidth=1.0, fliersize=0, boxprops=dict(alpha=0.65), zorder=3)
sns.stripplot(data=c, x="chau_luc", y="inflation_pct", order=thu_tu, ax=ax,
              color=INK_SOFT, size=3, alpha=0.45, jitter=0.22, zorder=4)
ax.axhline(10, color=C8_RED, lw=1.4, zorder=5)
ax.text(len(thu_tu) - 0.45, 11.2, "Ngưỡng lạm phát cao 10%", ha="right",
        fontsize=8.5, color=C8_RED)
ax.set_xlabel(""); ax.set_ylabel("Lạm phát CPI năm 2023 (%)"); ax.set_ylim(-5, 60)
# Kết luận phải rút TỪ dữ liệu, không khẳng định theo cảm tính
tk = c.groupby("chau_luc").agg(n=("iso3", "count"), vuot=("high_inflation", "sum"),
                               tv=("inflation_pct", "median"))
tk["ty_le"] = tk.vuot / tk.n * 100
cao_nhat = tk.ty_le.idxmax(); tv_thap = tk.tv.idxmin()
ca_cuc_doan = c.loc[c.inflation_pct.idxmax()]
tieu_de_2_dong(ax, "H09. Lạm phát 2023 phân tán rất khác nhau giữa các châu lục",
    f"{int(c.high_inflation.sum())}/{len(c)} quốc gia vượt ngưỡng 10%. "
    f"{cao_nhat} có tỷ lệ vượt ngưỡng cao nhất ({tk.loc[cao_nhat,'ty_le']:.0f}%), "
    f"còn {tv_thap} có trung vị thấp nhất nhưng chứa ca cực đoan nhất — "
    f"{ca_cuc_doan.country_name} {ca_cuc_doan.inflation_pct:.0f}%. Chính sự phân tán "
    "theo không gian này làm cho bản đồ có giá trị kể chuyện.", rong=92, dy=1.02)
tidy(ax)
clipped = int((~c.inflation_pct.between(-5, 60)).sum())
caption(fig, f"Nguồn: World Bank (World Development Indicators). Mỗi chấm là một quốc gia; {clipped} giá trị ngoài khung −5 đến 60%.")
save(fig, "H09_lam_phat_theo_chau_luc.png")
KQ["lam_phat_2023"] = {"so_quoc_gia": int(len(c)),
                       "so_lam_phat_cao": int(c.high_inflation.sum()),
                       "trung_vi_toan_cau": round(float(c.inflation_pct.median()), 2),
                       "theo_chau_luc": {k: {"so_nuoc": int(r.n), "vuot_10pct": int(r.vuot),
                                             "trung_vi": round(float(r.tv), 2)}
                                         for k, r in tk.iterrows()}}

# ══════════════════════════════════════════════════════════════════════
# H10 — NGÀY NGOẠI LAI: PHÁT HIỆN VỀ CHÍNH PHƯƠNG PHÁP PHÁT HIỆN
#
# Kết quả thực tế đi ngược trực giác: 49/54 ngày ngoại lai của BTC rơi vào
# 2010–2014. Sụp đổ FTX (11/2022, −16,8%) KHÔNG bị đánh dấu, vì z-score tính
# trên toàn bộ lịch sử bị chi phối bởi giai đoạn đầu khi BTC còn cực kỳ thanh
# khoản kém. Đây là một hạn chế phải nêu, không phải điều để giấu đi.
# KHÔNG dùng trục kép — VIX vẽ ở khung dưới riêng, chung trục thời gian.
# ══════════════════════════════════════════════════════════════════════
print("[*] H10 Ngày ngoại lai")
o = btc[btc.is_outlier == 1]
# Kiểm chứng: các sự kiện lớn có bị ngưỡng |z| > 4 bắt được không?
# Số liệu lấy thẳng từ dữ liệu, không gõ tay — để báo cáo không bao giờ lệch.
SU_KIEN = {"2020-03-12": "Sập COVID",
           "2021-05-19": "Trung Quốc cấm đào",
           "2022-06-13": "Khủng hoảng Celsius/Terra",
           "2022-11-09": "Sụp đổ FTX"}
bang_su_kien = []
for ngay, ten in SU_KIEN.items():
    if pd.Timestamp(ngay) in btc.index:
        r = btc.loc[ngay]
        bang_su_kien.append({"ngay": ngay, "su_kien": ten,
                             "giam_pct": round(float(r.daily_return_pct), 2),
                             "z_score": round(float(r.zscore_return), 2),
                             "bi_danh_dau": bool(r.is_outlier)})
KQ["kiem_chung_su_kien"] = bang_su_kien
print("    Kiểm chứng sự kiện:")
for e in bang_su_kien:
    print(f"      {e['ngay']} {e['su_kien']:26} {e['giam_pct']:>7.2f}%  "
          f"z={e['z_score']:>6.2f}  {'ĐÁNH DẤU' if e['bi_danh_dau'] else 'bỏ sót'}")
ftx = next(e for e in bang_su_kien if e["su_kien"] == "Sụp đổ FTX")

truoc = o[o.index < "2015-01-01"]
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.5, 7.6), sharex=True,
                               gridspec_kw={"height_ratios": [2.3, 1]})
ax1.plot(btc.index, btc.price_usd, color=C1_BLUE, lw=1.2, zorder=3, label="Giá BTC")
ax1.scatter(o.index, o.price_usd, s=26, color=C8_RED, zorder=5,
            label=f"Ngày ngoại lai |z| > 4 — {len(o)} ngày",
            edgecolors=SURFACE, linewidths=1.0)
ax1.axvline(pd.Timestamp("2015-01-01"), color=INK_SOFT, lw=1.0, zorder=2)
ax1.text(pd.Timestamp("2015-06-01"), 0.9,
         f"{len(truoc)}/{len(o)} ngày ngoại lai\nnằm bên trái mốc này",
         fontsize=8.5, color=INK_SOFT, va="top")
# Chỉ chú thích MỘT điểm - ngày sập COVID, đã kiểm chứng
covid = o.loc["2020-03-12"]
ax1.annotate(f"12/03/2020 · {covid.daily_return_pct:.1f}%\nsập COVID", xy=(pd.Timestamp("2020-03-12"),
             covid.price_usd), xytext=(pd.Timestamp("2021-04-01"), 1400),
             fontsize=8.5, color=INK_SOFT,
             arrowprops=dict(arrowstyle="-", color=INK_SOFT, lw=0.9))
ax1.set_yscale("log"); ax1.set_ylabel("Giá BTC (USD, thang log)")
ax1.legend(loc="upper left")
tieu_de_2_dong(ax1, "H10. Ngưỡng z-score cố định bỏ sót các cú sập gần đây",
    f"{len(truoc)}/{len(o)} ngày ngoại lai rơi vào 2010–2014, khi BTC còn thanh "
    f"khoản rất kém. Ngày sụp đổ FTX 09/11/2022 giảm "
    f"{abs(ftx['giam_pct']):.1f}".replace(".", ",") + "% nhưng chỉ đạt z = "
    + f"{ftx['z_score']:.1f}".replace(".", ",") +
    " nên bị bỏ sót — độ lệch chuẩn toàn kỳ "
    "bị giai đoạn đầu kéo lên. Dashboard nên dùng z-score theo cửa sổ trượt.",
    rong=96, dy=1.03)
tidy(ax1)
ax2.plot(btc.index, btc.vix, color=C2_ORANGE, lw=1.0, zorder=3, label="VIX")
ax2.axhline(25, color=GRID, lw=1.0, zorder=2)
ax2.text(btc.index[60], 27.5, "Ngưỡng Risk-off (VIX = 25)", fontsize=8, color=INK_SOFT)
ax2.set_ylabel("VIX"); ax2.set_xlabel("Năm"); ax2.legend(loc="upper left"); tidy(ax2)
caption(fig, NGUON + " Hai khung dùng chung trục thời gian — không dùng trục kép.")
save(fig, "H10_gia_va_ngoai_lai.png")
KQ["ngoai_lai"] = {"tong_so_ngay_BTC": int(len(o)),
                   "so_ngay_truoc_2015": int(len(truoc)),
                   "ty_le_truoc_2015_pct": round(len(truoc) / len(o) * 100, 1),
                   "ngay_giam_manh_nhat": str(o.daily_return_pct.idxmin().date()),
                   "muc_giam_manh_nhat_pct": round(float(o.daily_return_pct.min()), 2)}

with open(os.path.join(HERE, "ket_qua_thong_ke.json"), "w", encoding="utf-8") as f:
    json.dump(KQ, f, ensure_ascii=False, indent=2)
print("\n[*] XONG — 10 hình trong eda/hinh/ + ket_qua_thong_ke.json")
