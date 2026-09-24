# Từ điển dữ liệu (Data Dictionary)

Rubric mục 1 yêu cầu "nêu rõ nguồn và từ điển dữ liệu" — đây là file đó.
Tất cả file nằm trong `data/processed/`.

**Bản giải thích đầy đủ, đã đối chiếu 47 cột của bảng crypto và tất cả 7 bảng với pipeline ngày 24/09/2026:** [CHI_TIET_7_BANG_PROCESSED.md](CHI_TIET_7_BANG_PROCESSED.md). Trang hiện tại là bản tra nhanh; khi có khác biệt, ưu tiên bản chi tiết và script.

---

## 1. `fact_crypto_daily.csv.gz` — 123.358 dòng × 47 cột

Bảng fact chính. Mỗi dòng = 1 đồng coin trong 1 ngày, đã join sẵn chỉ số vĩ mô.
File nén gzip, `pandas.read_csv()` đọc trực tiếp không cần giải nén.

### Khóa & định danh
| Cột | Kiểu | Mô tả |
|---|---|---|
| `date` | date | Ngày giao dịch (UTC), khóa chính cùng `ticker` |
| `ticker` | text | Mã coin viết hoa (BTC, ETH...) |
| `category` | text | Nhóm coin: Layer 1, DeFi, Stablecoin, Meme... |
| `mcap_rank` | int | Hạng vốn hóa tại thời điểm tải |
| `year`, `month` | int/text | Trường phái sinh để lọc và nhóm |

### Dữ liệu thị trường (gốc)
| Cột | Đơn vị | Mô tả |
|---|---|---|
| `price_usd` | USD | Giá tham chiếu cuối ngày |
| `market_cap_usd` | USD | Vốn hóa lưu hành |
| `volume_usd` | USD | Khối lượng giao dịch spot 24h |
| `supply` | coin | Lượng cung đang lưu hành |

### Dữ liệu on-chain (gốc) — điểm khác biệt so với dataset Kaggle
| Cột | Mô tả |
|---|---|
| `active_addresses` | Số địa chỉ hoạt động trong ngày |
| `tx_count` | Số giao dịch |
| `transfer_count` | Số lượt chuyển token |
| `hashrate` | Hashrate mạng (chỉ coin PoW) |
| `mvrv` | Tỷ lệ Market Value / Realized Value |
| `exchange_inflow_usd` | Dòng tiền vào sàn |
| `exchange_outflow_usd` | Dòng tiền ra khỏi sàn |

### Trường tính toán (Calculated fields — rubric 0.75đ)
| Cột | Công thức | Ý nghĩa |
|---|---|---|
| `log_return` | `ln(P_t) − ln(P_t−1)` | Log-return, dùng cho thống kê |
| `daily_return_pct` | `(P_t/P_t−1 − 1)×100` | Lợi suất ngày (%) |
| `ma7`, `ma30`, `ma90` | trung bình trượt | Đường xu hướng |
| `volatility_30d` | `std(log_return, 30) × √365 × 100` | Biến động năm hóa (%) |
| `drawdown_pct` | `(P_t / max(P_0..t) − 1) × 100` | Mức sụt so với đỉnh |
| `volume_ma30` | trung bình trượt 30 ngày | Khối lượng làm mượt |
| `turnover_ratio` | `volume / market_cap` | Tốc độ quay vòng vốn |
| `net_exchange_flow` | `inflow − outflow` | Dòng tiền ròng vào sàn |
| `zscore_return` | z-score của `log_return` theo từng coin | Dùng phát hiện outlier |
| `is_outlier` | `1` nếu `|z| > 4` | **Đánh dấu, KHÔNG xóa** |
| `is_up_day` | `1` nếu `daily_return_pct > 0`, `0` nếu không tăng, để thiếu khi chưa có lợi suất | **Biến mục tiêu Logistic Regression** |
| `btc_dominance_pct` | `mcap(BTC) / Σmcap × 100` | Thị phần Bitcoin |

### Chỉ số vĩ mô đã join theo `date`
Xem mục 3 bên dưới.

---

## 2. `fact_market_daily.csv` — 185.694 dòng × 4 cột

Vốn hóa và khối lượng của **63 coin** (nhiều hơn bảng trên, vì có những coin
Coin Metrics chỉ công bố vốn hóa/khối lượng mà không công bố giá ở gói miễn phí).
Dùng cho treemap thị phần và biểu đồ khối lượng.

`date` · `ticker` · `market_cap_usd` · `volume_usd`

---

## 3. `fact_macro_daily.csv` — 5.009 dòng × 16 cột (2013‑01‑01 → nay)

| Cột | Tần suất gốc | Mô tả |
|---|---|---|
| `date` | ngày | Khóa join với bảng crypto |
| `vix` | **ngày** | Chỉ số sợ hãi CBOE |
| `brent_oil` | **ngày** | Dầu Brent (USD/thùng) |
| `dxy` | **ngày** | Chỉ số USD — xem ghi chú bên dưới |
| `sp500` | tháng | Chỉ số S&P 500 |
| `us10y_yield` | tháng | Lợi suất trái phiếu Mỹ 10 năm (%) |
| `sp500_pe10` | tháng | P/E Shiller |
| `gold_usd` | tháng | Giá vàng (USD/oz) |
| `cpi_index` | tháng | Chỉ số CPI Mỹ |
| `cpi_mom_pct` | tháng | Lạm phát tháng so với tháng (%) |
| `cpi_yoy_pct` | tháng | **Lạm phát năm (%) — tự tính từ `cpi_index`** |
| `dxy_ret` | ngày | % thay đổi DXY theo ngày |
| `sp500_chg_30d` | — | % thay đổi S&P 500 trong 30 ngày |
| `gold_chg_30d` | — | % thay đổi vàng trong 30 ngày |
| `real_rate` | — | `us10y_yield − cpi_yoy_pct` — lãi suất thực |
| `risk_regime` | — | `Risk-off` (VIX>25) / `Trung tính` / `Risk-on` (VIX<15) |

**Ghi chú `dxy`:** nguồn không phát hành chỉ số DXY trực tiếp, nên bảng này tự
tính một chỉ số USD nội bộ từ tỷ giá hàng ngày theo công thức đang có trong script:
`DXY = 50,14348112 × Π (tỷ giá ngoại tệ/USD)^trọng số` với trọng số
EUR 57,6% · JPY 13,6% · GBP 11,9% · CAD 9,1% · SEK 4,2% · CHF 3,6%.
Nguồn tỷ giá trộn chiều USD/tiền và tiền/USD; script chưa chuẩn hóa chiều niêm yết. **Không xem đây là series DXY ICE đã kiểm chứng** hay dùng nó làm bằng chứng chính cho tương quan USD–crypto trước khi sửa và so chuỗi với nguồn độc lập.

**Ghi chú quan trọng về tần suất:** các cột tần suất tháng đã được forward-fill
sang ngày để join được với giá crypto. Hệ quả: đường của chúng có dạng bậc thang,
và **không được tính tương quan lợi suất ngày với các cột này** — phải dùng
gộp dữ liệu crypto và biến vĩ mô về cùng tháng lịch hoàn tất. Các trường
`sp500_chg_30d`, `gold_chg_30d` có cửa sổ chồng lấn, chỉ để mô tả, không dùng
kiểm định tương quan. Đây là điểm
phải nói rõ trong báo cáo, cũng là câu hỏi phản biện hay gặp nhất.

---

## 4. `fact_country_macro.csv` — 2.580 dòng × 17 cột (215 quốc gia × 2013‑2024)

Bảng panel quốc gia — **đây là bảng cấp dữ liệu cho Bản đồ**.

| Cột | Mô tả |
|---|---|
| `iso3` | **Mã ISO‑3 — khóa vẽ choropleth** |
| `year` | Năm |
| `inflation_pct` | Lạm phát CPI (%/năm) — World Bank |
| `gdp_usd` | GDP danh nghĩa (USD) |
| `population` | Dân số |
| `gdp_per_capita_usd` | `gdp_usd / population` |
| `log_gdp_per_capita` | `ln(GDP/người)` — dùng trong hồi quy |
| `high_inflation` | `1` nếu lạm phát > 10%, để thiếu nếu lạm phát thiếu — **biến mục tiêu Logistic** |
| `has_gdp` | `1` nếu năm đó có số GDP (GDP chỉ đầy đủ đến **2023**) |
| `country_name`, `region`, `sub_region`, `continent`, `capital`, `currency_code`, `iso2`, `is_ldc` | Thuộc tính quốc gia |

> Khi vẽ bản đồ nên mặc định chọn **năm 2023** — năm gần nhất có đủ GDP cho 184 quốc gia.

---

## 5. `fact_fx_daily.csv` — 78.628 dòng × 3 cột

Tỷ giá nội tệ/USD hàng ngày của 22 nền kinh tế từ 2013.
`date` · `country_fx` · `fx_per_usd`. Tên `fx_per_usd` không đúng với mọi quốc gia: nguồn trộn USD/tiền và tiền/USD, pipeline chưa đảo chiều. Nếu muốn kiểm định giả thuyết về mất giá tiền tệ, cần ánh xạ tên nước sang ISO3, chuẩn hóa chiều tỷ giá và kiểm tra độ phủ trước.

---

## 6. `dim_coin.csv` — 63 dòng × 9 cột

`ticker` · `first_date` · `last_date` · `n_days` · `latest_mcap` · `avg_volume`
· `category` · `mcap_rank` · `has_price_history`

## 7. `dim_country.csv` — 249 dòng × 9 cột

`iso3` · `iso2` · `country_name` · `region` · `sub_region` · `continent`
· `capital` · `currency_code` · `is_ldc`

---

## Sơ đồ quan hệ (star schema)

```
                    dim_coin ──┐
                               │ ticker
  fact_market_daily ───────────┤
                               │
  fact_macro_daily ─── date ───┼─── fact_crypto_daily   (bảng fact chính)
                               │
                    dim_country ──┐
                                  │ iso3
  fact_country_macro ─────────────┤
                                  │ (country_fx ~ country_name)
  fact_fx_daily ──────────────────┘
```
