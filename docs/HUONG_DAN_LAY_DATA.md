# Hướng dẫn dữ liệu hiện tại

Dữ liệu đã có trong `data/raw/` và `data/processed/`. Không cần tài khoản Kaggle, FRED hay CoinGecko để tái lập **bản hiện tại**. Xem danh sách file và nguồn trong [BAN_GIAO_DU_LIEU.md](BAN_GIAO_DU_LIEU.md).

Từ thư mục gốc `Project_CuoiKy`, nếu cần kiểm tra/tái lập dữ liệu từ bản raw đã lưu:

```powershell
.\.venv\Scripts\python.exe scripts\pipeline_tien_xu_ly.py
.\.venv\Scripts\python.exe scripts\make_db.py
.\.venv\Scripts\python.exe tests\verify_project.py
```

Pipeline đọc trực tiếp `data/raw/coinmetrics_raw.tar.gz`, không cần giải nén. Lệnh đầu ghi lại các bảng trong `data/processed/`; chỉ chạy khi nhóm muốn tái lập, không cần chạy để bắt đầu làm EDA/dashboard. `data/processed/_quality_checks.json` ghi số dòng nguồn và kết quả kiểm tra khóa. Nếu phải tải dữ liệu mới trong tương lai, các script ở `scripts/tuy_chon_khi_co_mang_thuong/` là nhánh **tùy chọn**, nguồn đầu vào và cấu trúc có thể khác, cần kiểm tra trước khi ghép vào bản nộp.
