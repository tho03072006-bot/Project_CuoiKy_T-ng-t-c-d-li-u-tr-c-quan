# Checklist bàn giao cho 2 thành viên — Đề tài 09

**Mốc chung:** `main` tại commit `44a6b88` (23/09/2026). Hai thành viên tạo nhánh riêng từ `main` và mở pull request trước khi gộp. Đây là checklist hoàn thiện **sản phẩm và phân tích**, chưa làm báo cáo IEEE hay quay video.

## Hiện trạng đã có, không làm lại từ đầu

- [x] Dữ liệu raw có nguồn; pipeline Python tạo 7 bảng xử lý (395.581 dòng), có join, missing, outlier và calculated fields; SQLite dựng lại được và qua integrity check.
- [x] `eda/` có script Matplotlib/Seaborn và 10 hình tĩnh.
- [x] `dashboard/` có 5 trang Streamlit + Plotly, mã cho 9 kiểu biểu đồ gồm choropleth, bộ lọc và các tương tác chọn điểm/drill-down.
- [x] `models/` có Linear và Logistic, kết quả đánh giá ngoài mẫu và trang hiển thị dự báo.
- [x] Bộ kiểm thử hiện tại: 5 kiểm tra dự án, 8 kiểm tra tương tác và 8 kiểm tra mô hình đều đạt ở lần bàn giao.

Những dấu `[x]` trên xác nhận **đã có hiện vật và kiểm thử tự động**; chưa thay cho kiểm tra bằng mắt, thao tác trong trình duyệt và rà soát lập luận khoa học. `CLAUDE.md` còn bảng tiến độ cũ nói dashboard chưa làm; không dùng bảng đó để báo trạng thái hiện tại.

## Thắng — Dữ liệu, EDA, mô hình và insight

Nhánh gợi ý: `feature/thang-analysis`. Chủ yếu sửa `data/`, `scripts/`, `eda/`, `models/` và tài liệu nguồn dữ liệu; phối hợp với Tài khi cần sửa câu chữ trên dashboard.

- [ ] **Kiểm tra khả năng tái lập.** Từ dữ liệu raw chạy lại `scripts/pipeline_tien_xu_ly.py` và `scripts/make_db.py`; so 7 bảng, khóa không trùng, tổng dòng, khoảng thời gian, missing có chủ đích, và `PRAGMA integrity_check`. Chạy `tests/verify_project.py`. Chỉ commit output mới nếu số liệu thực sự thay đổi.
- [ ] **Rà soát 10 hình EDA.** Mở từng PNG để kiểm tra trục, đơn vị, tiêu đề, chú giải, nhãn và khả năng đọc; chọn tối thiểu 3–5 hình thể hiện phân phối và mối quan hệ chính theo rubric. Sửa script/hình nếu phát hiện lỗi, không chép số từ hình vào code.
- [ ] **Kiểm chứng lại các phát biểu định lượng.** Tính lại từ `data/processed/`: số quan sát, giai đoạn, tương quan BTC–vĩ mô và p-value; cân nhắc vấn đề thử nhiều giả thuyết. Không gọi tương quan là quan hệ nhân quả. Chỉ so các tháng lịch hoàn tất và khoảng thời gian chung; ghi rõ DXY là chỉ số tự tính, các chuỗi vĩ mô tháng được điền sang ngày.
- [ ] **Thẩm định mô hình dự báo.** Chạy `models/du_bao.py` và `models/test_du_bao.py`; kiểm tra chia train/test theo thời gian, đặc trưng có sẵn tại thời điểm dự báo, baseline, khoảng tin cậy và số liệu trên trang dự báo. Logistic hiện có AUC xấp xỉ 0,51 nên phải trình bày là tín hiệu yếu, không khẳng định dự báo đáng tin cậy hay lợi nhuận giao dịch.
- [ ] **Chốt 3–4 insight có bằng chứng.** Mỗi insight cần chỉ rõ biểu đồ/bảng, mốc thời gian, số mẫu và một giới hạn. Gửi số liệu đã kiểm chứng cho Tài để hiện đúng trên dashboard; đây là nội dung sản phẩm, chưa viết báo cáo IEEE.
- [ ] **Cập nhật ghi chú kỹ thuật lỗi thời.** Đối chiếu `docs/NGUON_DU_LIEU.md`, `docs/TU_DIEN_DU_LIEU.md`, `eda/BAO_CAO_EDA.md` và bảng tiến độ trong `CLAUDE.md` với kết quả cuối, sửa các câu/số liệu sai. Giữ link nguồn và cách tái lập rõ để cả nhóm vấn đáp được.

**Thắng hoàn thành khi:** các hình và số liệu trùng với dữ liệu hiện tại, mô hình tái lập được, các kết luận không vượt quá bằng chứng, kiểm thử dữ liệu/mô hình đạt.

## Tài — Dashboard, tương tác và tích hợp

Nhánh gợi ý: `feature/tai-dashboard`. Chủ yếu sửa `dashboard/`, `tests/verify_interactions.py`, tệp chạy ứng dụng; nhận insight đã kiểm chứng từ Thắng.

- [ ] **Chạy thử như người dùng mới.** Clone repo vào thư mục mới, chạy `setup.bat` rồi `run_dashboard.bat`. Mở đủ 5 trang; kiểm tra trang tải xong, không lỗi, không cần file nằm ngoài repo và hướng dẫn trong `README.md` đúng.
- [ ] **Kiểm tra hình thức và yêu cầu 8 loại biểu đồ.** Đếm theo *kiểu khác nhau*, không theo số hình: line, bar, box, treemap, area, scatter, heatmap, histogram, choropleth đã có trong mã. Xác nhận cả 9 kiểu thực sự hiển thị với dữ liệu hợp lệ; chỉnh màu, thang đo, đơn vị, legend, tooltip và bố cục. Vốn hóa cần thang phù hợp vì lệch lớn; bản đồ lạm phát cần màu không bị cực trị lấn át.
- [ ] **Thử tương tác thật trong trình duyệt.** Đổi khoảng ngày, nhóm coin, coin, ngưỡng vốn hóa rồi chọn/xóa chọn trên bar và scatter; xác nhận biểu đồ liên quan đổi đúng (cross-filtering). Kiểm tra drill-down từ toàn cầu → châu lục → quốc gia và đường quay lại; đối chiếu tooltip với dữ liệu gốc. Kiểm thử tự động hiện chưa mô phỏng click/hover Plotly thật.
- [ ] **Thử các ca biên.** Không có coin/không có dữ liệu trong khoảng chọn, một ngày duy nhất, tháng crypto cuối chưa trọn, quốc gia thiếu GDP/lạm phát, đổi năm liên tiếp, mã châu lục `NA` = Bắc Mỹ. App phải giải thích trạng thái trống thay vì lỗi hoặc vẽ sai.
- [ ] **Kiểm tra trang dự báo và storytelling.** Đường dự báo/giá trị thật/đường cơ sở và kết quả phân lớp phải có nhãn, mốc train/test, đơn vị, mức bất định. Tích hợp 3–4 insight đã được Thắng xác nhận vào đúng ngữ cảnh của dashboard; nêu hạn chế mô hình yếu, không quảng bá khả năng dự báo quá mức.
- [ ] **Ổn định ứng dụng.** Chạy `tests/verify_project.py` và `tests/verify_interactions.py`; sửa lỗi phát hiện khi thao tác thật, thêm kiểm thử hồi quy cho lỗi mới, kiểm tra tốc độ tải và bộ nhớ trên máy khác. Cập nhật `README.md` nếu cách chạy thay đổi.

**Tài hoàn thành khi:** mọi trang chạy trên bản clone mới, ≥8 kiểu biểu đồ và bản đồ hiện đúng, lọc/drill-down/tooltip/cross-filter hoạt động thực tế, kiểm thử đạt và không có số liệu chưa được xác minh.

## Điểm gộp chung trước khi chuyển sang báo cáo và video

- [ ] Thắng và Tài review chéo pull request của nhau: Thắng kiểm tra số liệu/diễn giải trên dashboard; Tài kiểm tra EDA và dự báo đã tích hợp đúng.
- [ ] Gộp về `main`, chạy `run_all.bat` và cả ba bộ kiểm thử trên bản đã gộp; kiểm tra lại dashboard bằng trình duyệt. Cố định commit dùng cho báo cáo/demo.
- [ ] Sau khi các mục trên hoàn tất, nhóm mới viết báo cáo ≥40 trang theo cấu trúc/IEEE của rubric và quay video demo backup. Hai việc này **chưa giao trong checklist hiện tại**.
