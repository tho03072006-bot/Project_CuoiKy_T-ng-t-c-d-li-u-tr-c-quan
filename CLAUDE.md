# Đồ án cuối kỳ — Môn Tương tác Dữ liệu Trực quan (IDVI333677)

**Đề tài 09: Phân tích thị trường Cryptocurrency và mối tương quan với các chỉ số
kinh tế vĩ mô.** Nhóm 3 thành viên. Trả lời bằng **tiếng Việt**, giữ thuật ngữ kỹ
thuật tiếng Anh (matplotlib, choropleth, cross-filtering...).

---

## Quy tắc làm việc trong repo này

1. **Không bịa số.** Mọi con số đưa vào biểu đồ, báo cáo hay tiêu đề phải tính từ
   dữ liệu trong `data/processed/`. Nếu cần một con số, hãy viết code tính nó rồi
   in ra, đừng gõ tay.
2. **Chạy thử trước khi báo xong.** Code phải thực sự chạy được. Với biểu đồ, hãy
   render ra file rồi tự mở xem, kiểm tra nhãn chồng nhau và tràn khung.
3. **Đây là đồ án chấm điểm, có phần vấn đáp trừ tối đa 4,0 điểm** nếu sinh viên
   không giải thích được code. Vì vậy mọi hàm phải có comment tiếng Việt ngắn giải
   thích *tại sao* làm vậy, không chỉ *làm gì*.
4. **Nêu hạn chế thay vì giấu.** Giảng viên đánh giá cao nhóm tự chỉ ra giới hạn
   của dữ liệu và phương pháp.

---

## Dữ liệu — ĐÃ HOÀN TẤT, không cần tải lại

7 bảng trong `data/processed/`, tổng **395.581 dòng**. Có sẵn `crypto_macro.db`
(SQLite, đã đánh index trên `(ticker,date)`, `(date)`, `(iso3,year)`).

File `.csv.gz` đọc trực tiếp bằng `pd.read_csv()`, không cần giải nén.

### `fact_crypto_daily.csv.gz` — 123.358 dòng, 47 cột, 39 coin, 2010→2026-05-23
Bảng fact chính, **đã join sẵn chỉ số vĩ mô theo `date`**.

- Khoá: `date`, `ticker`
- Thị trường: `price_usd`, `market_cap_usd`, `volume_usd`, `supply`
- On-chain: `active_addresses`, `tx_count`, `transfer_count`, `hashrate`, `mvrv`,
  `exchange_inflow_usd`, `exchange_outflow_usd`
- Tính toán: `log_return`, `daily_return_pct`, `ma7`, `ma30`, `ma90`,
  `volatility_30d`, `drawdown_pct`, `volume_ma30`, `turnover_ratio`,
  `net_exchange_flow`, `btc_dominance_pct`, `total_mcap`, `year`, `month`
- Ngoại lai: `zscore_return`, `is_outlier`
- **Biến mục tiêu Logistic:** `is_up_day`
- Vĩ mô đã join: `vix`, `dxy`, `sp500`, `gold_usd`, `brent_oil`, `us10y_yield`,
  `sp500_pe10`, `cpi_index`, `cpi_mom_pct`, `cpi_yoy_pct`, `dxy_ret`,
  `sp500_chg_30d`, `gold_chg_30d`, `real_rate`, `risk_regime`
- Thuộc tính coin: `category`, `mcap_rank`

### `fact_market_daily.csv` — 185.694 dòng, 63 coin
`date, ticker, market_cap_usd, volume_usd`. Nhiều coin hơn bảng trên vì có những
coin chỉ công bố vốn hoá/khối lượng mà không có giá. Dùng cho treemap thị phần.

### `fact_macro_daily.csv` — 5.009 dòng, 2013→2026-09
16 cột vĩ mô theo ngày (xem danh sách ở trên).

### `fact_country_macro.csv` — 2.580 dòng, 215 quốc gia × 2013–2024
**Bảng cấp dữ liệu cho BẢN ĐỒ.**
`iso3, year, inflation_pct, gdp_usd, population, gdp_per_capita_usd,
log_gdp_per_capita, high_inflation, has_gdp, iso2, country_name, region,
sub_region, continent, capital, currency_code, is_ldc`

### `fact_fx_daily.csv` — 78.628 dòng
`date, country_fx, fx_per_usd` — tỷ giá 22 nền kinh tế.

### `dim_coin.csv` (63) · `dim_country.csv` (249)
`dim_coin`: `ticker, first_date, last_date, n_days, latest_mcap, avg_volume,
category, mcap_rank, has_price_history`

---

## BẪY DỮ LIỆU — đọc kỹ, đã mất công phát hiện

**1. Cột `continent` có giá trị `"NA"` nghĩa là Bắc Mỹ, KHÔNG phải giá trị thiếu.**
Luôn đọc hai bảng quốc gia bằng:
```python
pd.read_csv(path, keep_default_na=False, na_values=[""])
```
Quên dòng này thì 22 quốc gia Bắc Mỹ biến mất khỏi bản đồ và không có cảnh báo nào.

**2. KHÔNG tính tương quan lợi suất ngày với biến vĩ mô.** `sp500`, `gold_usd`,
`us10y_yield`, `cpi_*` là dữ liệu **tháng** đã forward-fill sang ngày. Phải gộp về
tháng bằng `.resample("ME").last()` rồi mới `.pct_change()`.
Cửa sổ 30 ngày trượt cũng sai: quan sát chồng lấn 29/30 làm hệ số và mức ý nghĩa
bị thổi phồng — cùng dữ liệu này cho r = 0,37 thay vì 0,22 đúng.

**3. `is_outlier` dùng z-score toàn kỳ nên lệch:** 49/54 ngày ngoại lai của BTC rơi
vào 2010–2014. FTX (09/11/2022, −14,9%, z = −3,49) và Trung Quốc cấm đào
(19/05/2021, −12,0%, z = −2,78) đều bị bỏ sót. Khi cần phát hiện ngoại lai cho
giai đoạn gần, hãy tính z-score theo cửa sổ trượt 365 ngày.

**4. Vốn hoá trải 6 bậc độ lớn** → mọi biểu đồ vốn hoá phải có thang log.

**5. Lạm phát có ca cực đoan** (Lebanon 221% năm 2023) → bản đồ phải cắt ngưỡng
hoặc dùng thang phân vị, nếu không cả thế giới chung một màu nhạt.

**6. Dữ liệu crypto dừng 2026-05-23**, vĩ mô đến 2026-09. Cắt về cùng khoảng khi so sánh.

**7. Chỉ 39/63 coin có lịch sử giá.** Lọc `has_price_history == 1` khi cần giá.

---

## Kết quả đã kiểm chứng — dùng lại, đừng tính lại sai

Trên **100 quan sát tháng độc lập, 2018–2026**:

| Quan hệ với BTC | r | p | Kết luận |
|---|---|---|---|
| ETH | +0,773 | <0,001 | có ý nghĩa |
| S&P 500 | +0,215 | 0,031 | **có ý nghĩa** (R² chỉ 0,046) |
| Lạm phát Mỹ | −0,222 | 0,026 | **có ý nghĩa** |
| Lãi suất thực | +0,139 | 0,167 | không |
| Chỉ số USD | −0,102 | 0,311 | không |
| Vàng | −0,060 | 0,555 | không |
| VIX | −0,040 | 0,689 | không |

Phân phối log-return: BTC skew −0,75, kurtosis 21,45, Jarque–Bera 111.528,
p < 0,001 → **bác bỏ phân phối chuẩn**. Không dùng độ lệch chuẩn để đo rủi ro.

Thị phần BTC: 46% (2022) → 63% (2025–2026).
Biến động BTC trung vị: 88% (2013) → 42% (2026).

---

## Cấu trúc thư mục

```
Project_CuoiKy/
├── CLAUDE.md                 file này
├── data/processed/           7 bảng + crypto_macro.db
├── data/raw/                 dữ liệu thô
├── docs/                     README_DATA, TU_DIEN_DU_LIEU, NGUON_DU_LIEU
├── eda/                      eda_phan_tich.py, eda_style.py, BAO_CAO_EDA.md, hinh/H01..H10.png
└── scripts/                  pipeline_tien_xu_ly.py, make_db.py
```

`eda/eda_style.py` chứa **bảng màu đã qua kiểm định** (khoảng cách màu cho người mù
màu ΔE ≥ 8). Tái sử dụng bảng màu này cho dashboard để toàn bộ đồ án nhất quán:

```
Định danh: #2a78d6 xanh · #eb6834 cam · #1baf7a ngọc · #eda100 vàng · #e34948 đỏ
Liên tục (sequential): #cde2fb → #86b6ef → #3987e5 → #256abf → #0d366b  (MỘT màu)
Phân cực (diverging):  #e34948 ← #f0efec (xám) → #2a78d6
Nền #fcfcfb · Chữ chính #0b0b0b · Chữ phụ #52514e · Lưới #e8e7e3
```

**Ba lỗi biểu đồ bị trừ điểm, tuyệt đối tránh:** trục kép (hai thang y trên một
hình), thang rainbow cho dữ liệu liên tục, và tô đậm theo giá trị trên biến định
danh. Lưới phải liền nét và mờ, không dùng nét đứt.

---

## Tiến độ theo barem (10 điểm)

**Cập nhật 24/09/2026:** bảng này chỉ ghi hiện vật đã có, không tự chấm điểm. Phân công và tiêu chí nghiệm thu mới nhất nằm ở [`docs/CHECKLIST_PHAN_CONG.md`](docs/CHECKLIST_PHAN_CONG.md). Bạn phụ trách yêu cầu bắt buộc 1 (bài toán/dataset), Thắng yêu cầu 2 (pipeline/EDA), Tài yêu cầu 3 (dashboard); cả ba viết báo cáo **sau khi** sản phẩm được kiểm tra và chốt.

| Mục | Điểm | Trạng thái |
|---|---|---|
| 1. Thu thập & Tiền xử lý | 2,5 | Có dữ liệu raw, 7 bảng, pipeline và 10 hình EDA; còn kiểm tra tái lập, hình và các giả định (đặc biệt DXY). |
| 2. Dashboard | 3,5 | Có 5 trang Streamlit + Plotly, mã cho 9 kiểu biểu đồ; còn kiểm tra thao tác thật và UI trên bản clone mới. |
| 3. Insight & Dự báo | 2,0 | Có mã và kết quả mô hình; còn kiểm chứng insight, giới hạn mô hình và hiển thị sau tích hợp. |
| 4. Báo cáo & Demo | 2,0 | Chưa viết báo cáo cuối kỳ hoặc quay video; cả nhóm thực hiện sau khi chốt sản phẩm. |

### Yêu cầu bắt buộc của mục 2 (3,5 đ)
- Công cụ: **Streamlit + Plotly** (nhóm đã chốt)
- Giao diện, bố cục, legend rõ ràng — 0,5
- **≥ 8 loại biểu đồ khác nhau** — 1,0
- **≥ 1 Bản đồ (choropleth)** — 0,5
- Filter nhiều cấp, drill-down, tooltip, **cross-filtering** — 1,5

### Yêu cầu bắt buộc của mục 3 (2,0 đ)
- Storytelling rút insight, không chỉ show biểu đồ — 1,0
- Mô hình **Hồi quy tuyến tính hoặc Logistic** — 0,5
- **Tích hợp kết quả dự báo lên dashboard** — 0,5

### Yêu cầu bắt buộc của mục 4 (2,0 đ)
- Báo cáo **≥ 40 trang**, chuẩn IEEE, 7 phần: (1) giới thiệu & mô tả dữ liệu,
  (2) tiền xử lý & EDA, (3) thiết kế dashboard, (4) khai phá insight,
  (5) mô hình dự báo, (6) hướng dẫn cài đặt + link video, (7) kết luận & tài liệu
  tham khảo — 1,0
- Ứng dụng chạy mượt + **video demo backup bắt buộc** — 1,0

---

## Môi trường

Windows, Python 3.11. Chạy `setup.bat` để tạo môi trường và cài `requirements.txt`; chạy `run_dashboard.bat` để mở ứng dụng. `run_all.bat` tái lập pipeline, EDA, mô hình và kiểm tra.
