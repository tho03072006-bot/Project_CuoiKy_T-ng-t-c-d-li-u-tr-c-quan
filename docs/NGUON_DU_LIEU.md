# Nguồn dữ liệu và minh chứng

Rubric yêu cầu "nêu rõ nguồn, phải dẫn link/minh chứng cụ thể". Đây là file đó.
Toàn bộ dữ liệu lấy ngày **21/09/2026**, không có dòng nào do sinh viên tự bịa.

## Bảng nguồn

| # | Nguồn | Link gốc | Dùng cho | Giấy phép |
|---|---|---|---|---|
| 1 | **Coin Metrics Community Data** | https://github.com/coinmetrics/data — thư mục `csv/` | Giá, vốn hóa, khối lượng, dữ liệu on-chain của 63 đồng coin | Miễn phí, gói Community |
| 2 | CBOE VIX (Core Datasets) | https://github.com/datasets/finance-vix | Chỉ số VIX theo ngày | Public Domain (PDDL) |
| 3 | Tỷ giá hối đoái (Core Datasets) | https://github.com/datasets/exchange-rates | Tính chỉ số USD (DXY) + bảng tỷ giá quốc gia | PDDL |
| 4 | S&P 500 (Core Datasets) | https://github.com/datasets/s-and-p-500 | S&P 500, P/E Shiller; cột lãi suất có placeholder 0 từ 10/2023 | PDDL |
| 4a | Lợi suất trái phiếu Mỹ 10 năm | https://github.com/datasets/bond-yields-us-10y | Bảng `raw/macro/us10y_monthly.csv`, nguồn chính cho `us10y_yield` | PDDL |
| 5 | Giá vàng (Core Datasets) | https://github.com/datasets/gold-prices | Giá vàng theo tháng | PDDL |
| 6 | Dầu Brent (Core Datasets) | https://github.com/datasets/oil-prices | Giá dầu theo ngày | PDDL |
| 7 | CPI Mỹ (Core Datasets) | https://github.com/datasets/cpi-us | Chỉ số giá tiêu dùng Mỹ | PDDL |
| 8 | **World Bank — CPI** | https://github.com/datasets/cpi | Lạm phát theo quốc gia | CC‑BY‑4.0 (World Bank) |
| 9 | **World Bank — GDP** | https://github.com/datasets/gdp | GDP theo quốc gia | CC‑BY‑4.0 |
| 10 | **World Bank — Dân số** | https://github.com/datasets/population | Dân số theo quốc gia | CC‑BY‑4.0 |
| 11 | Danh mục mã quốc gia ISO | https://github.com/datasets/country-codes | ISO3, châu lục, khu vực, thủ đô, tiền tệ | PDDL |

Nguồn 8–11 chính là dữ liệu World Bank — đúng một trong các nguồn rubric cho phép.
Bản trên GitHub là bản sao được cập nhật tự động từ World Bank Open Data, dùng vì
truy cập trực tiếp `api.worldbank.org` bị chặn trong mạng thực hiện.

## Trích dẫn IEEE cho báo cáo

```
[1] Coin Metrics, "Free Coin Metrics data archives," GitHub repository, 2026.
    [Online]. Available: https://github.com/coinmetrics/data. [Accessed: 21-Sep-2026].
[2] World Bank, "World Development Indicators: Consumer price index, GDP,
    Population," Open Knowledge Foundation Core Datasets mirror, 2026. [Online].
    Available: https://github.com/datasets. [Accessed: 21-Sep-2026].
[3] Chicago Board Options Exchange, "CBOE Volatility Index (VIX) daily data,"
    Core Datasets, 2026. [Online]. Available:
    https://github.com/datasets/finance-vix. [Accessed: 21-Sep-2026].
[4] Intercontinental Exchange, "U.S. Dollar Index methodology," ICE, 2026.
```

## Hạn chế của dữ liệu — phải nêu trong báo cáo

Phần này quan trọng khi vấn đáp. Giảng viên đánh giá cao nhóm tự chỉ ra được
giới hạn của dữ liệu mình dùng, hơn là nhóm giả vờ dữ liệu hoàn hảo.

**1. Dữ liệu crypto dừng ở 2026‑05‑23.** Kho lưu trữ miễn phí của Coin Metrics
chậm hơn thời gian thực khoảng 4 tháng. Chuỗi vĩ mô thì cập nhật đến tháng 9/2026.
Khi phân tích tương quan phải cắt cả hai về cùng khoảng để tránh lệch.

**2. Chỉ 39/63 coin có lịch sử giá.** Gói Community của Coin Metrics chỉ công bố
giá cho nhóm coin cấp 1. Các coin còn lại (SOL, AVAX, ATOM, SHIB, NEAR, FIL...)
chỉ có vốn hóa và khối lượng — đó là lý do có bảng `fact_market_daily` riêng.
Nói rõ điều này thay vì để giảng viên tự phát hiện BTC dominance được tính trên
63 coin còn biểu đồ giá chỉ có 39 coin.

**3. Một số chuỗi vĩ mô là dữ liệu tháng.** S&P 500, vàng, lợi suất 10 năm, CPI
đều theo tháng, đã forward-fill sang ngày. Không được tính tương quan lợi suất
ngày với chúng. Xem ghi chú trong từ điển dữ liệu.

**4. `dxy` là chỉ số tự tính, không phải DXY chính thức.** Công thức và kiểm
chứng đã ghi trong từ điển dữ liệu. Sai số so với DXY thực tế dưới 0,1% ở mốc
kiểm tra 2022‑09‑27.

**5. GDP World Bank chỉ đầy đủ đến 2023.** Bản đồ nên mặc định năm 2023.
Lạm phát có đến 2024 nhưng chỉ 125 quốc gia.

**6. Thiếu lãi suất điều hành Fed (Fed Funds Rate).** Không có bản sao trên
GitHub và `fred.stlouisfed.org` bị chặn. Đang dùng lợi suất trái phiếu 10 năm
thay thế. Khi nhóm chạy ở mạng thường, tải bổ sung bằng:
`https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS`

## Tái lập kết quả

```
python scripts/pipeline_tien_xu_ly.py  # từ thư mục gốc project
python scripts/make_db.py             # dựng SQLite từ các CSV
```

Dữ liệu thô nằm trong `data/raw/`. File `coinmetrics_raw.tar.gz` chứa 63 file CSV
gốc — `pipeline_tien_xu_ly.py` đọc trực tiếp từ archive, không cần giải nén.
