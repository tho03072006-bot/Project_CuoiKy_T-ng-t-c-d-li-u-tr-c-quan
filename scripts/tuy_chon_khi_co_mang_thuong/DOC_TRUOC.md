# Các script này KHÔNG cần dùng nữa

Dữ liệu của đồ án đã được tải và xử lý xong, nằm trong `data/processed/`.
Pipeline thực tế đã dùng là `scripts/pipeline_tien_xu_ly.py`.

Thư mục này giữ lại bộ script cũ lấy dữ liệu từ **FRED, World Bank API và Kaggle**.
Chúng không chạy được trong môi trường đã dùng để tải dữ liệu (các host đó bị chặn),
nhưng **vẫn chạy tốt trên mạng gia đình / mạng trường**.

Khi nào cần đến chúng:

- Muốn bổ sung **lãi suất điều hành Fed (FEDFUNDS)** — chỉ số duy nhất còn thiếu.
  Chạy `01_fetch_fred.py`.
- Muốn thêm chỉ số World Bank ngoài 3 chỉ số đang có (ví dụ % dân số dùng Internet,
  kiều hối/GDP). Chạy `02_fetch_worldbank.py`.
- Muốn cập nhật giá crypto mới hơn mốc 2026-05-23. Chạy `03_fetch_market_extra.py`.

Trước khi chạy: `pip install -r ../../requirements.txt`
