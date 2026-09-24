# Chi tiết 7 bảng đã xử lý (`data/processed/`)

Kiểm kê ngày 24/09/2026 từ CSV hiện có và [`scripts/pipeline_tien_xu_ly.py`](../scripts/pipeline_tien_xu_ly.py). Nguồn và cột raw: [CHI_TIET_DATA_RAW.md](CHI_TIET_DATA_RAW.md). Bảy CSV là dữ liệu phân tích; `crypto_macro.db` là bản sao SQLite của chúng; `_summary.json`/`_quality_checks.json` là metadata, không phải bảng dữ liệu độc lập.

## Quy trình chung đã chạy

1. Đọc 63 coin từ `raw/coinmetrics_raw.tar.gz` (bản giải nén cùng nội dung chỉ để xem); chuyển `time` UTC thành `date`, chuẩn hóa ticker, loại ngày không hợp lệ. Giá ưu tiên `PriceUSD`, rồi `ReferenceRateUSD`/`ReferenceRate` nếu chuỗi có >180 giá trị; bỏ giá thiếu/không dương và coin dưới 180 ngày giá hợp lệ. Market vẫn nhận coin có ≥180 dòng và ít nhất vốn hóa hoặc volume.
2. Tạo các chỉ số giá/on-chain; giữ missing thật, đặc biệt cột on-chain, không gán 0. Đánh dấu outlier `abs(zscore)>4` trên lợi suất từng coin nhưng **không xóa** các cú sốc thị trường.
3. Gộp 7 file `raw/macro` theo ngày. Cột nguồn tháng được forward-fill tối đa **62 ngày**, cột nguồn ngày tối đa **5 ngày**, từ 2013. `cpi_yoy_pct` tính trên chỉ số CPI-U Mỹ trước khi điền tiếp. `wb_cpi.csv` của panel quốc gia là **tỷ lệ lạm phát năm**, không phải mức CPI.
4. Full outer join lạm phát/GDP/dân số theo `iso3,year`; lọc mã ISO3 trong `dim_country` và năm 2013–2024, rồi gắn địa lý. Chỉ coi chuỗi rỗng là NA khi đọc country codes để giữ `continent="NA"` = Bắc Mỹ.
5. Join macro và dominance theo `date` (`many_to_one`), phân loại coin theo `ticker` (`many_to_one`); kiểm tra khóa không thiếu/trùng, không có vô hạn, ghi CSV (bảng crypto nén gzip). Float của bảng crypto làm tròn 6 số thập phân. `scripts/make_db.py` dựng SQLite từ CSV, kiểm tra số dòng/khóa và `PRAGMA integrity_check`.

Pipeline đọc **530.018 dòng raw** và tạo **395.581 dòng trên 7 bảng**. Tổng dòng giữa các bảng **không** phải cỡ mẫu thống kê độc lập; nhiều bảng mô tả cùng ngày/coin. Missing chi tiết theo cột nằm trong [`_quality_checks.json`](../data/processed/_quality_checks.json).

| File | Dòng × cột | Grain / khóa | Nội dung |
|---|---:|---|---|
| `fact_crypto_daily.csv.gz` | 123.358 × 47 | `ticker,date` | Giá và chỉ số coin, vĩ mô đã join. |
| `fact_market_daily.csv` | 185.694 × 4 | `ticker,date` | Vốn hóa/volume của 63 coin. |
| `fact_macro_daily.csv` | 5.009 × 16 | `date` | Vĩ mô căn trên lưới ngày. |
| `fact_country_macro.csv` | 2.580 × 17 | `iso3,year` | Panel quốc gia cho bản đồ. |
| `fact_fx_daily.csv` | 78.628 × 3 | `country_fx,date` | Tỷ giá theo tên nước/ngày. |
| `dim_coin.csv` | 63 × 9 | `ticker` | Danh mục và độ phủ coin. |
| `dim_country.csv` | 249 × 9 | `iso3` | Mã và địa lý quốc gia. |

## 1. `fact_crypto_daily.csv.gz` — 123.358 × 47

Nguồn Coin Metrics + `fact_macro_daily` + dominance tính từ `fact_market_daily` + `dim_coin`. Một coin/ngày trong khoảng **18/07/2010–23/05/2026**; chỉ **39 coin** có lịch sử giá. Đọc trực tiếp bằng `pd.read_csv("data/processed/fact_crypto_daily.csv.gz", parse_dates=["date"])`.

| Cột | Ý nghĩa, đơn vị và cách tạo |
|---|---|
| `date`, `ticker` | Ngày UTC đã chuẩn hóa và mã coin viết hoa; khóa kép. |
| `price_usd` | Giá USD dương, Coin Metrics `PriceUSD` hoặc giá tham chiếu dự phòng đủ dài; giá thiếu/≤0 đã loại. |
| `market_cap_usd` | Vốn hóa USD; `CapMrktCurUSD` ưu tiên nếu có >100 giá trị, khác thì `CapMrktEstUSD`; có thể thiếu. |
| `volume_usd` | Khối lượng spot báo cáo 1 ngày, USD (`volume_reported_spot_usd_1d`). |
| `active_addresses` | `AdrActCnt`: số địa chỉ hoạt động ngày. |
| `tx_count` | `TxCnt`: số giao dịch. |
| `transfer_count` | `TxTfrCnt`: số lượt chuyển tài sản. |
| `hashrate` | `HashRate`: công suất băm khi nguồn có; thiếu với nhiều coin không PoW. |
| `supply` | `SplyCur`: lượng cung hiện hành, đơn vị coin. |
| `mvrv` | `CapMVRVCur`: tỷ lệ Market Value/Realized Value. |
| `exchange_inflow_usd`, `exchange_outflow_usd` | `FlowInExUSD`/`FlowOutExUSD`: dòng tài sản vào/ra sàn quy USD, thiếu có hệ thống ở nhiều coin. |
| `log_return` | `ln(price_t) − ln(price_t−1)` theo coin; thiếu dòng đầu. |
| `zscore_return` | Z-score của `log_return` theo mean/std **toàn kỳ từng coin**, làm tròn 3 số; chỉ dùng mô tả, không dùng trực tiếp cho dự báo thời điểm quá khứ. |
| `is_outlier` | 1 nếu `abs(zscore gốc)>4`, còn lại 0; chỉ đánh dấu, không xóa. |
| `daily_return_pct` | `(price_t/price_t−1−1)×100`, phần trăm; thiếu dòng đầu. |
| `ma7`, `ma30`, `ma90` | Trung bình trượt giá qua 7/30/90 **quan sát** của coin; USD, đầu chuỗi chưa đủ cửa sổ là missing. |
| `volatility_30d` | Std trượt 30 `log_return` × `sqrt(365)` × 100; % năm hóa. |
| `drawdown_pct` | `(price_t / max(price_đầu..t) − 1)×100`; phần trăm sụt từ đỉnh đến lúc đó. |
| `volume_ma30` | Trung bình trượt 30 quan sát volume, USD. |
| `turnover_ratio` | `volume_usd/market_cap_usd` nếu vốn hóa >0; tỷ lệ, không phải %. |
| `net_exchange_flow` | Inflow trừ outflow, USD; missing nếu một đầu vào thiếu. |
| `year`, `month` | Năm và tháng `YYYY-MM` lấy từ `date`. |
| `is_up_day` | Nhãn 1 nếu `daily_return_pct>0`, 0 nếu không tăng, **missing nếu return thiếu**; target Logistic. |
| `vix`, `brent_oil`, `dxy`, `sp500`, `us10y_yield`, `sp500_pe10`, `gold_usd`, `cpi_index`, `cpi_mom_pct`, `cpi_yoy_pct`, `dxy_ret`, `sp500_chg_30d`, `gold_chg_30d`, `real_rate`, `risk_regime` | 15 cột copy từ `fact_macro_daily` bằng `date`; xem mục 3 để biết tần suất/đơn vị. |
| `btc_dominance_pct` | `mcap_BTC / tổng mcap của coin có trong fact_market_daily cùng ngày ×100`; không phải dominance toàn thị trường thế giới. |
| `total_mcap` | Tổng vốn hóa USD của coin có số liệu trong bảng market ngày đó. |
| `category` | Nhóm coin do project ánh xạ thủ công trong pipeline, từ `dim_coin`. |
| `mcap_rank` | Xếp hạng **tĩnh** theo vốn hóa cuối cùng có số liệu của `dim_coin`, không phải hạng từng ngày. |

## 2. `fact_market_daily.csv` — 185.694 × 4

Nguồn 63 CSV Coin Metrics. Một coin/ngày **18/07/2010–23/05/2026**, gồm **24 coin không đủ chuỗi giá** cho bảng crypto. Ép vốn hóa/volume sang số; bỏ dòng nếu cả hai thiếu, chỉ giữ coin có ≥180 dòng, loại trùng `ticker,date` và sắp theo coin/ngày. Dùng cho treemap và tính dominance.

| Cột | Ý nghĩa |
|---|---|
| `date` | Ngày UTC, khóa cùng ticker. |
| `ticker` | Mã coin viết hoa, khóa cùng ngày. |
| `market_cap_usd` | Vốn hóa USD (`CapMrktCurUSD` ưu tiên nếu đủ, `CapMrktEstUSD` dự phòng); có thể thiếu nếu volume còn. |
| `volume_usd` | Khối lượng spot USD 1 ngày; có thể thiếu nếu vốn hóa còn. |

## 3. `fact_macro_daily.csv` — 5.009 × 16

Nguồn 7 file `raw/macro/`. Một ngày **01/01/2013–18/09/2026**. Full outer join ngày nguồn, resample ngày, rồi điền tiếp có giới hạn; không nội suy tuyến tính. Lưới ngày thuận tiện cho dashboard/join, **không làm chuỗi tháng thành quan sát ngày độc lập**.

| Cột | Gốc / ý nghĩa |
|---|---|
| `date` | Ngày, khóa duy nhất. |
| `vix` | `vix_daily.CLOSE`, mức chỉ số sợ hãi; nguồn ngày, ffill ≤5 ngày. |
| `brent_oil` | `brent_daily.Price`, dầu Brent USD/thùng; nguồn ngày, ffill ≤5 ngày. |
| `dxy` | Chỉ số USD **nội bộ tự tính**, không phải DXY chính thức: `50.14348112 × exp(sum(w_i×ln(rate_i)))` từ Euro 57,6%, Nhật 13,6%, Anh 11,9%, Canada 9,1%, Thụy Điển 4,2%, Thụy Sĩ 3,6%; cần đủ 6 tỷ giá, ffill ≤5 ngày. Script hiện dùng giá trị nguồn chưa đảo chiều niêm yết hỗn hợp, vì vậy **không so mức/trend của cột này với DXY ICE hoặc dùng làm bằng chứng độc lập cho quan hệ USD–crypto** trước khi sửa và kiểm định. |
| `sp500` | `sp500_monthly.SP500`, mức chỉ số, nguồn tháng, ffill ≤62 ngày. |
| `us10y_yield` | `us10y_monthly.Rate` ưu tiên; dự phòng `sp500_monthly.Long Interest Rate` >0, %, nguồn tháng, ffill ≤62 ngày. |
| `sp500_pe10` | `sp500_monthly.PE10` khi >0; P/E Shiller, nguồn tháng, ffill ≤62 ngày. |
| `gold_usd` | `gold_monthly.Price`, USD/ounce, nguồn tháng, ffill ≤62 ngày. |
| `cpi_index` | `cpi_us_monthly.Index`, mức CPI-U Mỹ (1982–84=100), nguồn tháng, ffill ≤62 ngày. |
| `cpi_mom_pct` | `cpi_us_monthly.Inflation`, % thay đổi tháng/trước do nguồn cung cấp, ffill ≤62 ngày. |
| `cpi_yoy_pct` | `Index.pct_change(12)×100`, % cùng tháng năm trước; tính **trước** ffill. |
| `dxy_ret` | `dxy.pct_change()×100` trên bảng ngày. |
| `sp500_chg_30d` | `sp500.pct_change(30)×100` trên bảng ngày đã ffill; cửa sổ chồng lấn, chỉ mô tả. |
| `gold_chg_30d` | `gold_usd.pct_change(30)×100` trên bảng ngày đã ffill; cửa sổ chồng lấn. |
| `real_rate` | `us10y_yield − cpi_yoy_pct`, chênh lệch điểm %, đại diện đơn giản cho lãi suất thực. |
| `risk_regime` | `Risk-off` nếu VIX>25, `Risk-on` nếu VIX<15, `Trung tinh` nếu 15–25; missing khi VIX thiếu. |

## 4. `fact_country_macro.csv` — 2.580 × 17

Nguồn `wb_cpi.csv`, `wb_gdp.csv`, `wb_population.csv`, `country_codes.csv`. Một ISO3/năm, **215 nước × 2013–2024**. Full outer join 3 chuỗi bằng `iso3,year`; lọc mã ISO3 hợp lệ để loại nhóm tổng hợp World Bank và cắt năm 2013–2024; left join thuộc tính quốc gia. Missing GDP/lạm phát/dân số được giữ, không gán 0.

| Cột | Ý nghĩa / cách tạo |
|---|---|
| `iso3`, `year` | Mã nước ISO3 và năm, khóa kép. |
| `inflation_pct` | `wb_cpi.CPI`: **tỷ lệ lạm phát giá tiêu dùng hằng năm (%)**, không phải mức CPI. |
| `gdp_usd` | `wb_gdp.Value`: GDP danh nghĩa USD. |
| `population` | `wb_population.Value`: tổng dân số, người. |
| `gdp_per_capita_usd` | `gdp_usd/population`, USD/người khi đủ đầu vào. |
| `log_gdp_per_capita` | `ln(max(gdp_per_capita_usd,1))`; giữ missing khi GDP/người thiếu. |
| `high_inflation` | 1 nếu `inflation_pct>10`, 0 nếu không, **missing** nếu lạm phát thiếu. |
| `has_gdp` | 1 nếu GDP không thiếu, khác 0. |
| `iso2`, `country_name`, `region`, `sub_region`, `continent`, `capital`, `currency_code`, `is_ldc` | Thuộc tính từ `dim_country`; xem mục 7. |

`iso3` dùng cho choropleth, `year` cho bộ lọc năm. `continent="NA"` là Bắc Mỹ, không phải missing. Các năm mới có độ phủ GDP thấp hơn; kiểm tra `has_gdp` và số quốc gia có dữ liệu trước khi so sánh bản đồ qua thời gian.

## 5. `fact_fx_daily.csv` — 78.628 × 3

Nguồn `raw/macro/fx_daily.csv`, chỉ đổi tên cột và lọc ngày từ 01/01/2013 đến 11/09/2026. Một `country_fx,date` trong **22 nền kinh tế**; tỷ giá thiếu vẫn có thể còn. Bảng **chưa join** ISO3: tên `Country` của nguồn không phải mã quốc gia. Muốn so với panel cần ánh xạ tên→ISO3 được kiểm chứng riêng.

| Cột | Ý nghĩa |
|---|---|
| `date` | Ngày, khóa cùng `country_fx`. |
| `country_fx` | Tên nước/nền kinh tế đúng như nguồn tỷ giá. |
| `fx_per_usd` | Giá trị `Exchange rate` nguyên từ nguồn. **Tên cột không đúng với mọi nước:** nguồn trộn USD/tiền và tiền/USD; pipeline chỉ đổi tên, chưa đảo chiều hay chuẩn hóa. Không so mức/tính biến động xuyên nước trước khi chuẩn hóa chiều báo giá. |

## 6. `dim_coin.csv` — 63 × 9

Tổng hợp `fact_market_daily`, cộng ánh xạ nhóm coin `CATEGORY` thủ công trong script và cờ có/không có trong `fact_crypto_daily`. Một ticker một dòng.

| Cột | Ý nghĩa / cách tạo |
|---|---|
| `ticker` | Mã coin, khóa duy nhất. |
| `first_date`, `last_date` | Ngày đầu/cuối xuất hiện **trong bảng market sau lọc**, không phải ngày ra mắt coin. |
| `n_days` | Số ngày/dòng market của coin. |
| `latest_mcap` | Vốn hóa USD cuối cùng **có giá trị** của chuỗi market; các coin có thể khác ngày quan sát. |
| `avg_volume` | Trung bình `volume_usd` qua các ngày có số liệu. |
| `category` | Nhóm coin ánh xạ thủ công theo ticker; `Khac` nếu không có trong bảng ánh xạ. |
| `mcap_rank` | Rank giảm dần của `latest_mcap` (`method="min"`); **không phải hạng từng ngày**. |
| `has_price_history` | 1 nếu coin nằm trong bảng crypto sau điều kiện ≥180 ngày giá hợp lệ, 0 nếu chỉ có market. |

## 7. `dim_country.csv` — 249 × 9

Nguồn 9/56 cột của `raw/country/country_codes.csv`. Bỏ ISO3 thiếu/trùng; một ISO3 một dòng. Khi đọc chỉ chuỗi rỗng là NA để giữ `Continent="NA"`.

| Cột | Ý nghĩa / cột raw |
|---|---|
| `iso3` | Mã ISO 3166-1 alpha-3, khóa/bản đồ; `ISO3166-1-Alpha-3`. |
| `iso2` | Mã ISO alpha-2; `ISO3166-1-Alpha-2`. |
| `country_name` | Tên nước tiếng Anh; `official_name_en`. |
| `region` | Khu vực; `Region Name`. |
| `sub_region` | Tiểu vùng; `Sub-region Name`. |
| `continent` | Mã châu lục; `Continent`, trong đó `NA` = Bắc Mỹ. |
| `capital` | Thủ đô; `Capital`. |
| `currency_code` | Mã tiền tệ ISO 4217; `ISO4217-currency_alphabetic_code`. |
| `is_ldc` | 1 nếu `Least Developed Countries (LDC)` có giá trị, 0 nếu rỗng. |

## Nối bảng và giới hạn suy luận

- `fact_crypto_daily.ticker` và `fact_market_daily.ticker` → `dim_coin.ticker`; `fact_crypto_daily.date` → `fact_macro_daily.date`. Bảng crypto **đã chứa** macro/dominance, không join lại để cộng số dòng hay vốn hóa.
- `fact_country_macro.iso3` → `dim_country.iso3`; fact quốc gia **đã có** thuộc tính geo. `fact_fx_daily.country_fx` là tên, **không nối trực tiếp** ISO3.
- Crypto dừng 23/05/2026 còn macro đến 18/09/2026. Tính tương quan trên thời gian chung và **tháng lịch hoàn tất**; báo `n` mẫu. Các giá trị tháng ffill không phải quan sát ngày độc lập. Không gọi tương quan là nhân quả.
- `zscore_return` dùng trung bình/độ lệch chuẩn toàn kỳ nên không dùng như feature dự báo quá khứ. Dữ liệu macro không ghi lịch công bố/vintage; không khẳng định biến có sẵn đúng thời điểm lịch sử nếu chưa đối chiếu.
