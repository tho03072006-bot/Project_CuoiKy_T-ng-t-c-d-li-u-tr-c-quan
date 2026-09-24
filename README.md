# Project_Interactive Data Visualization

Đề tài 09: phân tích thị trường tiền điện tử và mối tương quan với các chỉ số kinh tế vĩ mô. Repository này là bản bàn giao hiện trạng để các thành viên trong nhóm tiếp tục làm việc.

## Bắt đầu

1. Cài Python 3.11, chạy `setup.bat` để tạo `.venv` và cài `requirements.txt`.
2. Chạy `run_dashboard.bat` để xem dashboard Streamlit với dữ liệu đã có.
3. Khi cần tái lập từ dữ liệu gốc, chạy `run_all.bat`. Lệnh này lần lượt chạy tiền xử lý, dựng SQLite, EDA, mô hình và kiểm tra. Có thể chạy riêng `python scripts/pipeline_tien_xu_ly.py` và `python scripts/make_db.py`.

## Tìm tệp theo công việc

| Vị trí | Nội dung |
|---|---|
| `data/raw/` | Bản chụp dữ liệu nguồn; xem nguồn và phạm vi trong `docs/NGUON_DU_LIEU.md`. |
| `data/processed/` | Bảy bảng CSV đã tiền xử lý, SQLite tương ứng, tóm tắt và kiểm tra chất lượng. |
| `docs/BAN_GIAO_DU_LIEU.md` | Bàn giao dữ liệu, khóa nối, giới hạn và cách sử dụng từng bảng. |
| `docs/CHI_TIET_DATA_RAW.md` | Nguồn, schema và ý nghĩa cột của từng file raw, kèm danh mục 63 CSV Coin Metrics. |
| `docs/CHI_TIET_7_BANG_PROCESSED.md` | Đủ 7 bảng xử lý, ý nghĩa cột, khóa và từng bước làm sạch/biến đổi. |
| `docs/TU_DIEN_DU_LIEU.md` | Từ điển cột. |
| `scripts/` | Pipeline tiền xử lý và dựng cơ sở dữ liệu; thư mục `tuy_chon_khi_co_mang_thuong/` chỉ dùng khi cần tải bổ sung. |
| `eda/` | Script, hình và thống kê khám phá. |
| `dashboard/` | Ứng dụng Streamlit. |
| `models/` | Script, mô hình và kết quả đánh giá. |
| `tests/` | Kiểm tra dữ liệu, SQLite và dashboard. |

Trước khi viết kết luận, hãy đối chiếu các con số trong `eda/BAO_CAO_EDA.md` và `CLAUDE.md` với bảng dữ liệu hiện tại. Một số số liệu ghi sẵn có thể thuộc lần tính trước; `data/processed/` và các script là nguồn đối chiếu chính.

Các thư mục `.venv/`, `.idea/`, `tmp/` và tệp SQLite journal là tệp cục bộ/tạm nên không được đưa lên Git. Bản `crypto_macro.db` trong repo được dựng lại từ bảy bảng CSV và đã qua `PRAGMA integrity_check`.
