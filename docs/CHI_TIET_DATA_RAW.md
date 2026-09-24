# Danh mục chi tiết dữ liệu thô (`data/raw/`)

**Bản kiểm kê:** 24/09/2026, đọc trực tiếp các tệp trong repo. Đây là bản chụp offline; số dòng và mốc cuối của tệp là của bản chụp, không khẳng định nguồn trực tuyến dừng ở đó. Link dưới đây chỉ tới kho nguồn, vì bản tải ban đầu không lưu commit SHA/URL từng tệp; không thể xác nhận chính xác revision thượng nguồn chỉ bằng bản chụp. Xem thêm [danh sách nguồn](NGUON_DU_LIEU.md) và [quy trình biến đổi](TU_DIEN_DU_LIEU.md).

Trong `data/raw/`, các thư mục `country_kaggle/`, `crypto_kaggle/`, `market/`, `worldbank/` hiện **không có tệp dữ liệu**; chúng là chỗ dự phòng của cấu trúc project, không phải nguồn đầu vào của 7 bảng processed.

## 1. Coin Metrics: archive và 63 CSV theo coin

**Nguồn:** [Coin Metrics Community Data, thư mục `csv/`](https://github.com/coinmetrics/data/tree/master/csv), bản tải miễn phí dùng cho dữ liệu ngày của từng tài sản. `data/raw/coinmetrics_raw.tar.gz` có **63 CSV / 189.355 dòng**. Thư mục `data/raw/coinmetrics_raw/coinmetrics/` là **63 bản giải nén giống hệt từng member trong archive** (đã đối chiếu SHA-256 nội dung); không cộng hai bản thành 378.710 dòng. Pipeline mặc định đọc archive; nó chỉ đọc `data/raw/coinmetrics/*.csv` nếu thư mục thay thế đó tồn tại. Các tệp trong `coinmetrics_raw/coinmetrics/` hiện là bản để xem thủ công, không phải đầu vào trực tiếp của script.

**Grain:** một coin một ngày theo `time`; các coin có tập cột khác nhau. Trong 63 file có tổng cộng 33 tên cột khác nhau. `PriceUSD` có lịch sử đủ dài ở 39 coin; nhiều file còn `ReferenceRateUSD`/`ReferenceRate` nhưng chỉ vài dòng cuối nên **không đủ lịch sử giá** cho `fact_crypto_daily`. File `MATIC` chỉ có 3 cột và dừng 12/11/2025. Ngày cuối raw thường là 24/05/2026, còn bảng giá sau lọc dừng 23/05/2026.

### Ý nghĩa 33 cột có thể xuất hiện trong Coin Metrics

| Cột raw | Ý nghĩa / cách dùng trong project |
|---|---|
| `time` | Ngày quan sát theo UTC; chuẩn hóa thành `date`. |
| `PriceUSD` | Giá tài sản bằng USD; nguồn giá ưu tiên nếu có trên 180 giá trị. |
| `ReferenceRateUSD`, `ReferenceRate` | Giá tham chiếu thay thế nếu chuỗi đủ dài; không coi vài giá trị cuối là lịch sử đầy đủ. |
| `ReferenceRateBTC`, `ReferenceRateETH`, `ReferenceRateEUR` | Giá tham chiếu quy theo BTC/ETH/EUR; không dùng trong 7 bảng. |
| `PriceBTC` | Giá tài sản quy theo BTC; không dùng. |
| `CapMrktCurUSD` | Vốn hóa lưu hành bằng USD; ưu tiên nếu có trên 100 giá trị. |
| `CapMrktEstUSD` | Vốn hóa ước tính bằng USD; nguồn dự phòng. |
| `volume_reported_spot_usd_1d` | Khối lượng spot được báo cáo trong 1 ngày, USD. |
| `SplyCur` | Lượng cung hiện hành của coin. |
| `SplyExNtv`, `SplyExUSD`, `SplyExpFut10yr` | Các chỉ tiêu lượng cung loại trừ/ước tính tương lai của nguồn; không dùng trong 7 bảng. |
| `AdrActCnt`, `AdrBalCnt` | Số địa chỉ hoạt động / số địa chỉ có số dư; pipeline chỉ lấy `AdrActCnt`. |
| `TxCnt`, `TxTfrCnt` | Số giao dịch / số lượt chuyển token; đều giữ khi có. |
| `HashRate`, `BlkCnt` | Hashrate / số block của mạng; pipeline chỉ lấy hashrate. |
| `CapMVRVCur` | Tỷ lệ Market Value / Realized Value (MVRV). |
| `FlowInExNtv`, `FlowOutExNtv` | Dòng tài sản vào/ra sàn theo đơn vị coin; không dùng. |
| `FlowInExUSD`, `FlowOutExUSD` | Dòng tài sản vào/ra sàn quy USD; giữ trong bảng giá khi có. |
| `FeeTotNtv` | Tổng phí giao dịch theo coin gốc; không dùng. |
| `IssTotNtv`, `IssTotUSD` | Lượng phát hành mới theo coin gốc / USD; không dùng. |
| `ROI30d`, `ROI1yr` | Chỉ tiêu tỷ suất sinh lời 30 ngày / 1 năm do nguồn cấp; pipeline tự tính return từ giá thay vì dùng trực tiếp. |
| `AssetCompletionTime`, `AssetEODCompletionTime` | Thời điểm nguồn hoàn tất dữ liệu tài sản/cuối ngày; hiện chưa dùng để xác định lịch công bố. |

Một số tên cột Coin Metrics là nhãn do nhà cung cấp định nghĩa; để giải thích chính xác phương pháp tính của các metric chuyên sâu, đối chiếu [tài liệu Coin Metrics](https://docs.coinmetrics.io/) trước khi viết báo cáo. Các ô trống on-chain là thiếu dữ liệu nguồn, không phải giá trị 0.

### Kiểm kê từng CSV Coin Metrics

`Cột` là số trường có trong file raw; `Giá` = cờ `has_price_history` sau lọc của pipeline (`có`/`không`), **không** đơn thuần là sự hiện diện của cột giá. Toàn bộ các dòng sau đến từ cùng nguồn Coin Metrics ở trên.

| File trong `coinmetrics_raw/coinmetrics/` | Dòng | Từ ngày | Đến ngày | Cột | Giá |
|---|---:|---|---|---:|---|
| `1inch.csv` | 1,979 | 2020-12-23 | 2026-05-24 | 23 | có |
| `aave.csv` | 2,069 | 2020-09-24 | 2026-05-24 | 23 | có |
| `ada.csv` | 3,166 | 2017-09-23 | 2026-05-24 | 25 | có |
| `algo.csv` | 2,540 | 2019-06-11 | 2026-05-24 | 25 | có |
| `ankr.csv` | 2,627 | 2019-03-16 | 2026-05-24 | 8 | không |
| `apt.csv` | 1,448 | 2022-06-07 | 2026-05-24 | 8 | không |
| `atom.csv` | 2,589 | 2019-04-23 | 2026-05-24 | 8 | không |
| `avax.csv` | 2,130 | 2020-07-25 | 2026-05-24 | 8 | không |
| `axs.csv` | 2,028 | 2020-11-04 | 2026-05-24 | 8 | không |
| `bat.csv` | 3,283 | 2017-05-29 | 2026-05-24 | 23 | có |
| `bch.csv` | 3,223 | 2017-07-28 | 2026-05-24 | 27 | có |
| `bnb.csv` | 3,246 | 2017-07-05 | 2026-05-24 | 23 | có |
| `btc.csv` | 6,351 | 2009-01-03 | 2026-05-24 | 32 | có |
| `chz.csv` | 2,452 | 2019-09-07 | 2026-05-24 | 8 | không |
| `comp.csv` | 2,273 | 2020-03-04 | 2026-05-24 | 23 | có |
| `crv.csv` | 2,112 | 2020-08-12 | 2026-05-24 | 23 | có |
| `dash.csv` | 4,509 | 2014-01-19 | 2026-05-24 | 26 | có |
| `doge.csv` | 4,551 | 2013-12-08 | 2026-05-24 | 27 | có |
| `dot.csv` | 2,462 | 2019-08-28 | 2026-05-24 | 23 | có |
| `egld.csv` | 2,090 | 2020-09-03 | 2026-05-24 | 8 | không |
| `enj.csv` | 3,126 | 2017-11-02 | 2026-05-24 | 8 | không |
| `eos.csv` | 3,252 | 2017-06-29 | 2026-05-24 | 18 | có |
| `etc.csv` | 3,596 | 2016-07-20 | 2026-05-24 | 27 | có |
| `eth.csv` | 3,952 | 2015-07-30 | 2026-05-24 | 32 | có |
| `fil.csv` | 2,048 | 2020-10-15 | 2026-05-24 | 8 | không |
| `ftm.csv` | 2,580 | 2019-05-02 | 2026-05-24 | 8 | không |
| `gala.csv` | 1,747 | 2021-08-12 | 2026-05-24 | 8 | không |
| `grt.csv` | 1,985 | 2020-12-17 | 2026-05-24 | 8 | không |
| `hbar.csv` | 2,441 | 2019-09-18 | 2026-05-24 | 8 | không |
| `icp.csv` | 1,845 | 2021-05-06 | 2026-05-24 | 25 | có |
| `knc.csv` | 3,177 | 2017-09-12 | 2026-05-24 | 23 | có |
| `link.csv` | 3,173 | 2017-09-16 | 2026-05-24 | 23 | có |
| `lrc.csv` | 3,187 | 2017-09-02 | 2026-05-24 | 8 | không |
| `ltc.csv` | 5,344 | 2011-10-07 | 2026-05-24 | 27 | có |
| `mana.csv` | 3,233 | 2017-07-18 | 2026-05-24 | 23 | có |
| `matic.csv` | 2,392 | 2019-04-27 | 2025-11-12 | 3 | không |
| `mkr.csv` | 3,709 | 2016-03-28 | 2026-05-23 | 18 | có |
| `near.csv` | 2,049 | 2020-10-14 | 2026-05-24 | 8 | không |
| `neo.csv` | 3,601 | 2016-07-15 | 2026-05-24 | 25 | có |
| `omg.csv` | 3,246 | 2017-07-05 | 2026-05-24 | 23 | có |
| `qtum.csv` | 3,223 | 2017-07-28 | 2026-05-24 | 8 | không |
| `ren.csv` | 3,067 | 2017-12-31 | 2026-05-24 | 23 | có |
| `rep.csv` | 3,809 | 2015-10-14 | 2026-05-24 | 23 | có |
| `sand.csv` | 2,110 | 2020-08-14 | 2026-05-24 | 8 | không |
| `shib.csv` | 2,124 | 2020-07-31 | 2026-05-24 | 8 | không |
| `snx.csv` | 2,997 | 2018-03-11 | 2026-05-24 | 23 | có |
| `sol.csv` | 2,235 | 2020-04-11 | 2026-05-24 | 8 | không |
| `storj.csv` | 3,152 | 2017-10-07 | 2026-05-24 | 8 | không |
| `sushi.csv` | 2,098 | 2020-08-26 | 2026-05-24 | 23 | có |
| `theta.csv` | 3,050 | 2018-01-17 | 2026-05-24 | 8 | không |
| `trx.csv` | 3,152 | 2017-10-07 | 2026-05-24 | 18 | có |
| `uni.csv` | 2,079 | 2020-09-14 | 2026-05-24 | 23 | có |
| `usdc.csv` | 2,852 | 2018-08-03 | 2026-05-24 | 23 | có |
| `usdt.csv` | 4,531 | 2013-12-28 | 2026-05-24 | 23 | có |
| `vet.csv` | 2,872 | 2018-07-14 | 2026-05-24 | 8 | không |
| `waves.csv` | 3,477 | 2016-11-16 | 2026-05-24 | 8 | không |
| `xlm.csv` | 4,304 | 2014-08-12 | 2026-05-24 | 26 | có |
| `xmr.csv` | 4,420 | 2014-04-18 | 2026-05-24 | 24 | có |
| `xrp.csv` | 4,892 | 2013-01-01 | 2026-05-24 | 24 | có |
| `xtz.csv` | 3,257 | 2017-06-24 | 2026-05-24 | 26 | có |
| `yfi.csv` | 2,138 | 2020-07-17 | 2026-05-24 | 23 | có |
| `zec.csv` | 3,496 | 2016-10-28 | 2026-05-24 | 27 | có |
| `zrx.csv` | 3,209 | 2017-08-11 | 2026-05-24 | 23 | có |

## 2. Các file vĩ mô (`data/raw/macro/`)

| File | Nguồn kho / nguồn gốc dữ liệu | Dòng; khoảng thời gian raw | Grain, ý nghĩa và cột gốc | Đưa vào bảng xử lý |
|---|---|---|---|---|
| `vix_daily.csv` | [datasets/finance-vix](https://github.com/datasets/finance-vix), từ CBOE | 9.276; 02/01/1990–18/09/2026 | Một ngày giao dịch; `DATE` ngày, `OPEN` mở, `HIGH` cao, `LOW` thấp, `CLOSE` đóng của chỉ số biến động kỳ vọng VIX. | `DATE` + `CLOSE` → `fact_macro_daily.date`, `vix`; các OHLC khác không dùng. |
| `brent_daily.csv` | [datasets/oil-prices](https://github.com/datasets/oil-prices), chuỗi dầu Brent | 9.087; 20/05/1987–15/09/2026 | Một ngày; `Date` ngày, `Price` giá dầu Brent USD/thùng. | `brent_oil`. |
| `fx_daily.csv` | [datasets/exchange-rates](https://github.com/datasets/exchange-rates), bản tổng hợp từ Fed/FRED | 273.261; 04/01/1971–11/09/2026 | Một nước/đồng tiền một ngày; `Date` ngày, `Country` tên nền kinh tế, `Exchange rate` tỷ giá do nguồn cấp. Có 11.114 ô tỷ giá trống trong bản raw. **Hướng niêm yết không đồng nhất:** theo README nguồn, Australia, Euro, Ireland, New Zealand, United Kingdom được báo là USD/đơn vị tiền; phần còn lại chủ yếu tiền/USD. | Sáu nước/tiền tệ được pivot để tính chỉ số USD nội bộ `dxy`; các dòng từ 2013 được giữ ở `fact_fx_daily`. Script chưa chuẩn hóa chiều tỷ giá nên `dxy` không phải DXY chính thức. |
| `sp500_monthly.csv` | [datasets/s-and-p-500](https://github.com/datasets/s-and-p-500), dữ liệu lịch sử Robert Shiller | 1.868; 01/1871–08/2026 | Một tháng; `Date` mốc tháng; `SP500` mức chỉ số; `Dividend` cổ tức; `Earnings` lợi nhuận; `Consumer Price Index` CPI nguồn Shiller; `Long Interest Rate` lãi suất dài hạn; `Real Price`, `Real Dividend`, `Real Earnings` giá trị thực đã điều chỉnh; `PE10` P/E Shiller 10 năm. | Dùng `SP500`, `PE10`; cột lãi suất là dự phòng, nguồn `us10y_monthly.csv` ưu tiên. Các cột còn lại không dùng. `PE10 <= 0` coi là thiếu. |
| `us10y_monthly.csv` | [datasets/bond-yields-us-10y](https://github.com/datasets/bond-yields-us-10y), Fed H.15 | 880; 04/1953–07/2026 | Một tháng; `Date` tháng, `Rate` lợi suất danh nghĩa trái phiếu kho bạc Mỹ 10 năm (%). | Nguồn chính `us10y_yield`; nếu tháng thiếu mới dùng `Long Interest Rate > 0` ở S&P. |
| `gold_monthly.csv` | [datasets/gold-prices](https://github.com/datasets/gold-prices) | 2.324; 01/1833–08/2026 | Một tháng; `Date` dạng `YYYY-MM`, `Price` giá vàng USD/ounce. | `gold_usd`. |
| `cpi_us_monthly.csv` | [datasets/cpi-us](https://github.com/datasets/cpi-us), từ BLS CPI-U | 1.362; 01/1913–07/2026 | Một tháng; `Date` ngày đầu tháng, `Index` mức chỉ số CPI-U (1982–84=100), `Inflation` phần trăm thay đổi **so với tháng trước**; dòng đầu thiếu `Inflation` vì chưa có tháng trước. | `cpi_index`, `cpi_mom_pct`; `cpi_yoy_pct` được tính mới từ `Index` so với 12 tháng trước. |

**Tần suất:** pipeline gộp các chuỗi vĩ mô theo ngày từ 2013. Cột gốc tháng được điền tiếp tối đa 62 ngày; cột gốc ngày tối đa 5 ngày. Điền tiếp là để hiển thị/join, **không biến số liệu tháng thành quan sát ngày độc lập**; tương quan với crypto cần dùng tháng lịch hoàn tất và thời gian chung.

## 3. Các file quốc gia (`data/raw/country/`)

| File | Nguồn | Dòng; giai đoạn raw | Grain và cột | Đưa vào bảng xử lý |
|---|---|---|---|---|
| `wb_cpi.csv` | [World Bank WDI, FP.CPI.TOTL.ZG](https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG); đường dẫn bản tải/mirror cụ thể chưa được lưu | 11.182; 1960–2024 | Một `Country Code` × `Year`; `Country` tên nước; `CPI` là **lạm phát giá tiêu dùng hằng năm (%)**, không phải mức chỉ số CPI. Đối chiếu: USA 2022 = 8,0028%, USA 2024 = 2,9495%; năm 2005 không đồng loạt bằng 100. | Đổi `CPI` → `inflation_pct`. Không nhầm với `datasets/cpi`, vì kho đó chứa **mức chỉ số CPI** (2005=100) và không khớp tệp này. |
| `wb_gdp.csv` | [datasets/gdp](https://github.com/datasets/gdp), World Bank | 13.979; 1960–2023 | Một `Country Code` × `Year`; `Country Name` tên nước; `Value` GDP danh nghĩa USD. | Đổi `Value` → `gdp_usd`. |
| `wb_population.csv` | [datasets/population](https://github.com/datasets/population), World Bank | 17.195; 1960–2024 | Một `Country Code` × `Year`; `Country Name` tên nước; `Value` tổng dân số (người). | Đổi `Value` → `population`. |
| `country_codes.csv` | [datasets/country-codes](https://github.com/datasets/country-codes) | 249; bảng tham chiếu, không có trục thời gian | 56 cột mã quốc gia, phân vùng và tên gọi; một dòng một mã ISO3. | Chỉ giữ 9 thuộc tính trong `dim_country` và join vào `fact_country_macro`. |

### 56 cột của `country_codes.csv`

Đây là bảng tra cứu rất rộng; project **chỉ dùng 9 cột in đậm**. Mọi cột khác vẫn nằm trong raw để có thể kiểm tra, nhưng không đi vào 7 bảng processed.

| Nhóm | Cột raw | Ý nghĩa |
|---|---|---|
| Định danh | `FIFA`, `IOC`, `ITU`, `WMO`, `MARC`, `FIPS`, `GAUL`, `DS`, `EDGAR` | Mã quốc gia/lãnh thổ theo các hệ thống FIFA, Olympic, viễn thông, khí tượng, thư viện, thống kê/địa lý khác nhau; không dùng làm khóa nối. |
| ISO | **`ISO3166-1-Alpha-3`**, **`ISO3166-1-Alpha-2`**, `ISO3166-1-numeric` | Mã ISO quốc gia 3 ký tự (khóa join/bản đồ), 2 ký tự và dạng số. |
| Tiền tệ | **`ISO4217-currency_alphabetic_code`**, `ISO4217-currency_numeric_code`, `ISO4217-currency_name`, `ISO4217-currency_country_name`, `ISO4217-currency_minor_unit` | Mã tiền tệ chữ, mã số, tên tiền, tên nước theo tiền tệ và số chữ số đơn vị nhỏ. |
| Vùng địa lý | **`Region Name`**, **`Sub-region Name`**, **`Continent`**, `Region Code`, `Sub-region Code`, `Intermediate Region Code`, `Intermediate Region Name`, `Global Code`, `Global Name`, `M49` | Tên/mã khu vực, tiểu vùng, châu lục, vùng trung gian và mã phân loại thống kê UN. `Continent="NA"` nghĩa là Bắc Mỹ. |
| Tên nước | **`official_name_en`**, `official_name_fr`, `official_name_es`, `official_name_ar`, `official_name_cn`, `official_name_ru`, `CLDR display name` | Tên chính thức theo các ngôn ngữ và tên hiển thị CLDR. |
| Tên UN | `UNTERM English Short`, `UNTERM English Formal`, `UNTERM French Short`, `UNTERM French Formal`, `UNTERM Spanish Short`, `UNTERM Spanish Formal`, `UNTERM Arabic Short`, `UNTERM Arabic Formal`, `UNTERM Chinese Short`, `UNTERM Chinese Formal`, `UNTERM Russian Short`, `UNTERM Russian Formal` | Tên ngắn/chính thức của nước trong UNTERM theo ngôn ngữ tương ứng. |
| Hành chính | **`Capital`**, `Dial`, `TLD`, `Languages`, `Geoname ID`, `wikidata_id` | Thủ đô, mã điện thoại, miền internet, ngôn ngữ, ID GeoNames và liên kết Wikidata. |
| Phân loại | **`Least Developed Countries (LDC)`**, `Small Island Developing States (SIDS)`, `Land Locked Developing Countries (LLDC)`, `is_independent` | Cờ phân loại phát triển/địa lý và trạng thái độc lập. Pipeline chuyển riêng LDC thành `is_ldc` 0/1. |

`country_codes.csv` có nhiều trường không áp dụng cho mọi lãnh thổ nên missing là bình thường. `wb_*` còn chứa một số mã nhóm/tổng hợp World Bank; pipeline chỉ giữ ISO3 có trong `dim_country`, rồi cắt năm 2013–2024. Các bảng quốc gia không có khóa ngày để join trực tiếp với `fact_crypto_daily`; nếu cần so sánh, phải xác định cách ghép năm/quốc gia riêng và tránh suy ra quan hệ nhân quả.
