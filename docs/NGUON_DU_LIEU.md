# Nguồn dữ liệu và minh chứng

Rubric yêu cầu "nêu rõ nguồn, phải dẫn link/minh chứng cụ thể". Đây là file đó.
Toàn bộ dữ liệu lấy ngày **21/09/2026**, không có dòng nào do sinh viên tự bịa.

Chi tiết **từng file raw**, số dòng, khoảng thời gian và cột gốc: [CHI_TIET_DATA_RAW.md](CHI_TIET_DATA_RAW.md). Tài liệu này ghi link kho nguồn, nhưng bản tải ban đầu không giữ SHA/URL từng file ở thời điểm tải; không nên xem link hiện tại là bằng chứng bản trực tuyến hôm nay trùng từng byte với snapshot trong repo.

## Bảng nguồn

| # | Nguồn | Link gốc | Dùng cho | Giấy phép |
|---|---|---|---|---|
| 1 | **Coin Metrics Community Data** | https://github.com/coinmetrics/data — thư mục `csv/` | Giá, vốn hóa, khối lượng, dữ liệu on-chain của 63 đồng coin | CC BY-NC 4.0 theo README nguồn; bản Community miễn phí |
| 2 | CBOE VIX (Core Datasets) | https://github.com/datasets/finance-vix | Chỉ số VIX theo ngày | Public Domain (PDDL) |
| 3 | Tỷ giá hối đoái (Core Datasets) | https://github.com/datasets/exchange-rates | Tính chỉ số USD (DXY) + bảng tỷ giá quốc gia | PDDL |
| 4 | S&P 500 (Core Datasets) | https://github.com/datasets/s-and-p-500 | S&P 500, P/E Shiller; cột lãi suất có placeholder 0 từ 10/2023 | PDDL |
| 4a | Lợi suất trái phiếu Mỹ 10 năm | https://github.com/datasets/bond-yields-us-10y | Bảng `raw/macro/us10y_monthly.csv`, nguồn chính cho `us10y_yield` | PDDL |
| 5 | Giá vàng (Core Datasets) | https://github.com/datasets/gold-prices | Giá vàng theo tháng | PDDL |
| 6 | Dầu Brent (Core Datasets) | https://github.com/datasets/oil-prices | Giá dầu theo ngày | PDDL |
| 7 | CPI Mỹ (Core Datasets) | https://github.com/datasets/cpi-us | Chỉ số giá tiêu dùng Mỹ | PDDL |
| 8 | **World Bank — lạm phát giá tiêu dùng hằng năm** | https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG | `wb_cpi.CPI` là tỷ lệ lạm phát hằng năm (%), không phải mức chỉ số CPI. URL bản tải/mirror cụ thể chưa được ghi lại. | CC BY 4.0 theo trang chỉ tiêu World Bank |
| 9 | **World Bank — GDP** | https://github.com/datasets/gdp | GDP theo quốc gia | CC‑BY‑4.0 |
| 10 | **World Bank — Dân số** | https://github.com/datasets/population | Dân số theo quốc gia | CC‑BY‑4.0 |
| 11 | Danh mục mã quốc gia ISO | https://github.com/datasets/country-codes | ISO3, châu lục, khu vực, thủ đô, tiền tệ | PDDL |

Nguồn 8–10 là các chỉ tiêu World Bank; nguồn 11 là bảng mã quốc gia tổng hợp từ nhiều nguồn, không phải một chỉ tiêu World Bank. Tệp `wb_cpi.csv` **không phải** bản sao của [datasets/cpi](https://github.com/datasets/cpi): kho đó chứa mức chỉ số CPI (2005=100), còn bản local chứa lạm phát hằng năm, khớp chỉ tiêu `FP.CPI.TOTL.ZG`. Lịch sử tải không giữ URL/SHA của riêng tệp này, nên không thể khẳng định mirror cụ thể đã dùng. Những liên kết GitHub còn lại là liên kết kho dữ liệu, không chứng minh cùng revision với bản local.

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

**1. Dữ liệu crypto trong snapshot dừng ở 2026‑05‑23 sau lọc.** Bản raw nhiều coin có dòng đến 24/05/2026, nhưng ngày cuối này không đủ giá hợp lệ để giữ. Snapshot crypto này cũ hơn ngày kiểm kê; không suy ra một độ trễ cố định của kho trực tuyến. Chuỗi vĩ mô trong repo cập nhật đến tháng 9/2026.
Khi phân tích tương quan phải cắt cả hai về cùng khoảng để tránh lệch.

**2. Chỉ 39/63 coin có lịch sử giá.** Gói Community của Coin Metrics chỉ công bố
giá cho nhóm coin cấp 1. Các coin còn lại (SOL, AVAX, ATOM, SHIB, NEAR, FIL...)
chỉ có vốn hóa và khối lượng — đó là lý do có bảng `fact_market_daily` riêng.
Nói rõ điều này thay vì để giảng viên tự phát hiện BTC dominance được tính trên
63 coin còn biểu đồ giá chỉ có 39 coin.

**3. Một số chuỗi vĩ mô là dữ liệu tháng.** S&P 500, vàng, lợi suất 10 năm, CPI
đều theo tháng, đã forward-fill sang ngày. Không được tính tương quan lợi suất
ngày với chúng. Xem ghi chú trong từ điển dữ liệu.

**4. `dxy` là chỉ số nội bộ tự tính, không phải DXY chính thức.** Nguồn tỷ giá
trộn hai chiều niêm yết (USD/tiền và tiền/USD), trong khi script hiện dùng tỷ
giá nguyên dạng. Không dựa vào phép so một mốc ngày để xác nhận toàn chuỗi hoặc
kết luận quan hệ USD–crypto. Cần chuẩn hóa chiều tỷ giá, kiểm định cả chuỗi với
nguồn DXY độc lập trước khi sử dụng biến này cho nhận định chính.

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
