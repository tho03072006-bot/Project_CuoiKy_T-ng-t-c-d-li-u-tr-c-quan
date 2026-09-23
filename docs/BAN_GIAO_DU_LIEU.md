# Bàn giao dữ liệu — Đề tài 09

**Trạng thái ngày 23/09/2026:** bộ dữ liệu thô và 7 bảng đã xử lý có sẵn. Không cần tải lại để tiếp tục EDA, dashboard hoặc mô hình. Đây là ghi chú kỹ thuật dữ liệu, không phải báo cáo khoa học/IEEE.

## Bài toán và yêu cầu áp dụng

Đề tài 09 trong `DanhSachDeTai_IDV_fn.pdf`: phân tích thị trường cryptocurrency và quan hệ với chỉ số kinh tế vĩ mô. `RUBRIC IDV CUỐI KỲ.pdf` yêu cầu dữ liệu thực tế có nguồn, tối thiểu 5.000 dòng, nhiều bảng (barem nêu ≥3 bảng), script tiền xử lý có xử lý missing/outlier, join và trường tính toán. Phần sau cần 3–5 biểu đồ EDA tĩnh, dashboard ≥8 loại biểu đồ gồm bản đồ và một mô hình Linear/Logistic.

## Nguồn và tệp thô

| Tệp trong `data/raw/` | Nguồn đã ghi nhận | Nội dung |
|---|---|---|
| `coinmetrics_raw.tar.gz` | Coin Metrics Community, https://github.com/coinmetrics/data | 63 CSV theo coin, 189.355 dòng nguồn; giá, vốn hóa, khối lượng và chỉ số on-chain theo ngày. Pipeline đọc trực tiếp archive. |
| `macro/vix_daily.csv` | https://github.com/datasets/finance-vix | VIX theo ngày. |
| `macro/fx_daily.csv` | https://github.com/datasets/exchange-rates | Tỷ giá, dùng tạo chỉ số USD tổng hợp và bảng FX. |
| `macro/sp500_monthly.csv` | https://github.com/datasets/s-and-p-500 | S&P 500 và P/E Shiller theo tháng. Cột lãi suất nguồn này có số 0 placeholder từ 10/2023 nên không dùng làm nguồn chính. |
| `macro/us10y_monthly.csv` | https://github.com/datasets/bond-yields-us-10y | Lợi suất trái phiếu Mỹ 10 năm theo tháng, từ Federal Reserve H.15. |
| `macro/gold_monthly.csv` | https://github.com/datasets/gold-prices | Giá vàng theo tháng. |
| `macro/brent_daily.csv` | https://github.com/datasets/oil-prices | Giá dầu Brent theo ngày. |
| `macro/cpi_us_monthly.csv` | https://github.com/datasets/cpi-us | CPI Mỹ theo tháng; CPI YoY được tính từ chỉ số. |
| `country/wb_cpi.csv`, `wb_gdp.csv`, `wb_population.csv` | Bản sao World Bank: https://github.com/datasets/cpi, https://github.com/datasets/gdp, https://github.com/datasets/population | Panel lạm phát, GDP, dân số theo quốc gia/năm. |
| `country/country_codes.csv` | https://github.com/datasets/country-codes | Mã ISO3, tên nước, khu vực/châu lục cho bản đồ. |

Tổng số dòng đọc từ các tệp nguồn: **530.018**, chi tiết từng nguồn ở `data/processed/_quality_checks.json`. Các tệp nguồn là bản chụp đã có trong project, không được tự thay bằng dữ liệu live nếu chưa tính lại toàn bộ bảng/hình/mô hình.

## Bảng để các thành viên sử dụng

| Tệp trong `data/processed/` | Dòng × cột | Khóa duy nhất | Cách dùng |
|---|---:|---|---|
| `fact_crypto_daily.csv.gz` | 123.358 × 47 | `ticker,date` | Giá 39 coin; on-chain, lợi suất, volatility, drawdown, nhãn Logistic; đã nối macro theo `date`. |
| `fact_market_daily.csv` | 185.694 × 4 | `ticker,date` | Vốn hóa/khối lượng của 63 coin, kể cả 24 coin không có chuỗi giá. |
| `fact_macro_daily.csv` | 5.009 × 16 | `date` | VIX, S&P 500, USD tổng hợp, vàng, dầu, CPI, US10Y và trường dẫn xuất. |
| `fact_country_macro.csv` | 2.580 × 17 | `iso3,year` | 215 nước × 2013–2024; lạm phát/GDP/dân số, dữ liệu choropleth. |
| `fact_fx_daily.csv` | 78.628 × 3 | `country_fx,date` | Tỷ giá theo ngày. |
| `dim_coin.csv` | 63 × 9 | `ticker` | Danh mục/nhóm coin; cờ `has_price_history`. |
| `dim_country.csv` | 249 × 9 | `iso3` | Tên và thuộc tính địa lý. |

**Tổng 395.581 dòng ở 7 bảng.** `crypto_macro.db` là bản SQLite của chính 7 bảng; `_summary.json` lưu số dòng/cột, `_quality_checks.json` lưu khóa, số thiếu và đếm nguồn. `crypto_macro.db-journal` 0 byte là tệp phụ của SQLite, không phải nguồn dữ liệu.

## Luồng xử lý và cách đọc đúng

`data/raw/` → `scripts/pipeline_tien_xu_ly.py` → 7 bảng CSV → `scripts/make_db.py` → SQLite. Script loại giá thiếu/không dương; để missing có ý nghĩa ở on-chain, đánh dấu ngoại lai `|z|>4` nhưng không xóa các cú sốc thị trường; chuẩn hóa ngày và ticker; nối theo `date`, `ticker`, `iso3,year` với kiểm tra khóa không trùng; tạo log-return, MA7/30/90, volatility 30 ngày, drawdown, dominance, CPI YoY, lãi suất thực và các nhãn phân loại. QA đã kiểm tra 0 khóa trùng, đủ 7 bảng và SQLite `integrity_check=ok`.

```python
import pandas as pd
from pathlib import Path
p = Path("data/processed")
crypto = pd.read_csv(p / "fact_crypto_daily.csv.gz", parse_dates=["date"])
macro = pd.read_csv(p / "fact_macro_daily.csv", parse_dates=["date"])
country = pd.read_csv(p / "fact_country_macro.csv",
                      keep_default_na=False, na_values=[""])
```

**Lưu ý quan trọng:** `continent="NA"` là Bắc Mỹ, không phải missing. 39/63 coin có lịch sử giá, nên kiểm tra `has_price_history` trước biểu đồ giá. Crypto dừng **23/05/2026**, macro tới **18/09/2026**; chỉ so sánh trên thời gian chung. Một số chuỗi macro là dữ liệu **tháng** được điền tiếp sang ngày, vì vậy cần tổng hợp về tháng lịch hoàn tất trước khi tính tương quan với lợi suất crypto. Tháng 05/2026 chỉ có 23 ngày crypto nên không coi là tháng hoàn tất. `dxy` trong bảng là chỉ số USD **tự tính**, không phải bản chính thức. Missing trong `is_up_day`/`high_inflation` giữ là missing thay vì gán 0. Dữ liệu macro không có lịch công bố/vintage, cần thận trọng nếu dùng để dự báo thời điểm quá khứ.

## Tệp khác trong project

`docs/NGUON_DU_LIEU.md` có link nguồn; `docs/TU_DIEN_DU_LIEU.md` là từ điển cột. `eda/` có script, 10 hình PNG và kết quả thống kê; `dashboard/` có ứng dụng Streamlit; `models/` có script và kết quả dự báo; `tests/` có kiểm thử. Các tệp này hiện có nhưng **không cần dùng để nhận bàn giao dữ liệu**. Số liệu ghi sẵn trong `CLAUDE.md` và `eda/BAO_CAO_EDA.md` có thể thuộc lần tính trước; nhóm cần ưu tiên bảng xử lý và tính lại khi viết báo cáo. `scripts/tuy_chon_khi_co_mang_thuong/` là hướng tải bổ sung tùy chọn, **không thuộc nhánh tái lập offline hiện tại**. `.venv/`, `.idea/`, `tmp/` là môi trường, cấu hình và tệp tạm; không phải nguồn dữ liệu. Hai PDF gốc là đề tài và rubric. `setup.bat`, `run_all.bat`, `run_dashboard.bat`, `requirements.txt` là tệp cài/chạy dự án.

## Căn cứ phù hợp rubric và việc bàn giao

- Nguồn thực tế có link và tệp raw đi kèm; 530.018 dòng nguồn vượt ngưỡng 5.000.
- Bảy bảng xử lý vượt ngưỡng 3 bảng, có khóa join rõ ràng và được kiểm tra không trùng.
- Pipeline Python tái lập từ raw offline, xử lý missing/outlier và tạo nhiều trường tính toán; QA JSON và SQLite giúp đối chứng.
- ISO3 và bảng quốc gia/năm đủ điều kiện dữ liệu để làm bản đồ; dữ liệu giá, vĩ mô và nhãn có đầu vào cho phân tích và dự báo.

Dataset đạt **điều kiện đầu vào và phần dữ liệu/tiền xử lý**; điểm EDA, dashboard, insight, dự báo, báo cáo và demo còn phụ thuộc cách nhóm triển khai và trình bày. Khi chia việc, nên giao EDA dùng `data/processed/` + `eda/`, dashboard dùng `data/processed/` + `dashboard/`, mô hình dùng bảng tháng hoàn tất + `models/`. Thành viên viết báo cáo dựa trên số liệu tính lại từ bản xử lý và trích nguồn từ `docs/NGUON_DU_LIEU.md`.
