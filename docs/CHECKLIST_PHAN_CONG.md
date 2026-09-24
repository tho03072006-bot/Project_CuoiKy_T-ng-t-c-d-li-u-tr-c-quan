# Phân công theo yêu cầu rubric — Đề tài 09

**Cập nhật 24/09/2026.** Đối chiếu trực tiếp `RUBRIC IDV CUỐI KỲ.pdf`, mã và dữ liệu ở `main`. Chủ đề: *Phân tích thị trường tiền điện tử và mối tương quan với các chỉ số kinh tế vĩ mô*. Người dùng phụ trách **yêu cầu bắt buộc 1**; **Thắng phụ trách yêu cầu 2**; **Tài phụ trách yêu cầu 3**. Hai người tiếp tục phối hợp hoàn thiện insight và dự báo vì rubric còn chấm riêng các phần đó. **Cả ba chỉ viết báo cáo sau khi sản phẩm, số liệu và kiểm thử đã chốt.** Video demo làm sau khi dashboard hoàn tất.

## Tình trạng đối chiếu rubric

| Yêu cầu | Người phụ trách | Đã có trong repo | Chưa thể đánh dấu hoàn tất |
|---|---|---|---|
| **1. Bài toán và dataset**: nguồn có link, ≥5.000 dòng, nhiều bảng để join | **Bạn** | Đề tài 09 đã chọn; bản raw 530.018 dòng, 7 bảng processed 395.581 dòng; nguồn và từ điển cột đã ghi tại `docs/NGUON_DU_LIEU.md`, `docs/CHI_TIET_DATA_RAW.md`, `docs/CHI_TIET_7_BANG_PROCESSED.md`. | Xem lại diễn đạt mục tiêu/câu hỏi phân tích và bằng chứng nguồn trước khi khóa dữ liệu. URL/SHA tải chính xác của một số snapshot gốc không được lưu; tài liệu đã ghi rõ giới hạn này. |
| **2. Pipeline Python/R, làm sạch, calculated fields, EDA tĩnh** | **Thắng** | Python 3.11 + Pandas/NumPy tạo 7 bảng; 10 hình Matplotlib/Seaborn; missing, ngoại lai, trường tính toán và khóa nối đã có trong mã. | Tái lập từ raw, kiểm tra bằng mắt 3–5 hình tốt nhất; rà soát giả định tỷ giá/DXY và kiểm chứng lại số liệu, tương quan, insight. |
| **3. Dashboard dùng công cụ được phép, filter, drill-down, ≥8 kiểu biểu đồ có map** | **Tài** | Streamlit + Plotly, 5 trang dashboard; mã hiện có 9 kiểu biểu đồ (line, bar, box, treemap, area, scatter, heatmap, histogram, choropleth). | Chạy từ clone mới và thao tác thật trong trình duyệt: đủ kiểu hiển thị, lọc nhiều cấp, hover, drill-down, cross-filter, ca không có dữ liệu và bố cục. |

Dấu “đã có” chỉ xác nhận hiện vật/mã, **không phải** chứng nhận thao tác thực tế hoặc kết luận học thuật đã đúng. Ngày 24/09, `tests/verify_project.py` đạt **5/5**, `tests/verify_interactions.py` đạt **8/8**, `models/test_du_bao.py` đạt **8/8**. Các kiểm thử này không thay thế kiểm tra click/hover trực tiếp trên Plotly hay rà soát hình EDA bằng mắt.

## Bạn — yêu cầu 1: bài toán và dataset

- [x] Chọn đề tài 09 và tập dữ liệu thực tế có nguồn được rubric cho phép; số dòng vượt 5.000, nhiều bảng và khóa join rõ.
- [x] Bàn giao bản raw, 7 bảng processed, link nguồn, ý nghĩa cột và các bước đã xử lý. Xem [danh mục raw](CHI_TIET_DATA_RAW.md), [7 bảng processed](CHI_TIET_7_BANG_PROCESSED.md) và [nguồn dữ liệu](NGUON_DU_LIEU.md).
- [ ] Chốt 2–3 câu hỏi phân tích cụ thể với Thắng/Tài để EDA và dashboard trả lời cùng một bài toán; chọn khoảng thời gian chung và chỉ tiêu vĩ mô chính. Đừng dùng `dxy` tự tính làm bằng chứng chính trước khi Thắng sửa/kiểm định chiều tỷ giá.
- [ ] Xem lại link/minh chứng nguồn và xác nhận bản dữ liệu bàn giao trên `main`; không cần tải thêm chỉ để tăng số bảng. Nếu thay snapshot, phải báo Thắng/Tài chạy lại toàn bộ pipeline, hình và dashboard.

**Hoàn tất yêu cầu 1 khi:** bài toán, nguồn, số dòng, cấu trúc nhiều bảng và từ điển dữ liệu nhất quán, có thể giải thích trong vấn đáp. Bạn không nhận việc xây pipeline/EDA hoặc dashboard của hai thành viên còn lại.

## Thắng — yêu cầu 2: pipeline, EDA và kiểm chứng số liệu

Nhánh làm việc: `feature/thang-analysis`. Phạm vi chính: `scripts/`, `data/`, `eda/`, tài liệu xử lý; phối hợp `models/` cho phần dự báo riêng của barem.

- [ ] Chạy lại `scripts/pipeline_tien_xu_ly.py` và `scripts/make_db.py` từ raw. Kiểm tra 7 bảng, khóa `ticker,date` / `iso3,year` / `date`, số dòng, missing hợp lý, ngoại lai được đánh dấu, SQLite `integrity_check` và `tests/verify_project.py`. Chỉ commit output nếu thực sự đổi số liệu.
- [ ] Giải thích và đối chiếu join/merge: Pandas `concat` 63 CSV coin; outer merge macro theo `date`; outer merge World Bank theo `iso3,year`; left join metadata, macro và dominance. NumPy tính các chỉ số; SQLite chỉ lưu kết quả. Xem [tài liệu pipeline](CHI_TIET_7_BANG_PROCESSED.md#công-cụ-thực-hiện-joinmerge).
- [ ] Rà soát xử lý missing/outlier và trường tính toán: giá thiếu/không dương bị loại, dữ liệu on-chain thiếu được giữ, ngoại lai lợi suất chỉ đánh dấu; kiểm tra công thức return, volatility, dominance, CPI YoY, real rate. **Ưu tiên sửa hoặc loại biến `dxy` khỏi kết luận chính** vì nguồn FX trộn chiều niêm yết mà mã chưa chuẩn hóa.
- [ ] Mở từng hình trong `eda/hinh/`; chọn tối thiểu 3–5 hình tĩnh thực sự hữu ích, sửa nhãn, đơn vị, trục, cỡ chữ, chú giải nếu cần. Kiểm tra giá trị từ bảng processed, không dùng con số cũ chưa tính lại.
- [ ] Tính lại tương quan trên các **tháng lịch hoàn tất và thời gian chung**, ghi cỡ mẫu, phân biệt tương quan với nhân quả. Chốt 3–4 insight có biểu đồ/số liệu/giới hạn rõ và gửi Tài tích hợp.
- [ ] Nếu giữ phần dự báo theo barem đầy đủ, thẩm định Linear/Logistic ngoài mẫu, baseline, thời điểm xuất hiện feature và mức bất định; tín hiệu Logistic hiện yếu (AUC khoảng 0,51), không diễn giải như khả năng giao dịch chắc chắn. Chạy `models/test_du_bao.py`.

**Hoàn tất yêu cầu 2 khi:** pipeline tái lập được, số liệu và EDA khớp bản đã xử lý, hạn chế dữ liệu được xử lý/ghi rõ, kết luận có bằng chứng và kiểm thử dữ liệu/mô hình đạt.

## Tài — yêu cầu 3: dashboard và tích hợp

Nhánh làm việc: `feature/tai-dashboard`. Phạm vi chính: `dashboard/`, `tests/verify_interactions.py`, script chạy app và hướng dẫn sử dụng.

- [ ] Clone `main` vào thư mục sạch, chạy `setup.bat` rồi `run_dashboard.bat`; mở đủ 5 trang. Kiểm tra không cần file ngoài repo và hướng dẫn `README.md` đúng.
- [ ] Kiểm tra **9 kiểu khác nhau đang có trong mã** đều render với dữ liệu hợp lệ; rubric yêu cầu ít nhất 8, bắt buộc có bản đồ. Rà soát bố cục, màu, thang đo, đơn vị, tiêu đề, legend, tooltip; không đếm 8 hình cùng một kiểu là đạt.
- [ ] Trong trình duyệt, thử lọc nhiều cấp, chọn/xóa điểm để cross-filter, hover và drill-down bản đồ toàn cầu → châu lục → quốc gia rồi quay lại. Đối chiếu số trong tooltip với bảng processed. Kiểm thử tự động hiện không chứng minh toàn bộ thao tác chuột Plotly chạy đúng.
- [ ] Thử khoảng ngày không có dữ liệu, một ngày duy nhất, tháng cuối crypto chưa đủ, quốc gia thiếu GDP/lạm phát, đổi năm bản đồ và `continent="NA"` = Bắc Mỹ. Trạng thái trống phải được giải thích rõ, không vẽ sai hay báo lỗi.
- [ ] Nhận insight đã kiểm chứng từ Thắng để viết caption/storytelling trên dashboard. Hiển thị dự báo Linear/Logistic và giới hạn của mô hình đúng với kết quả đã kiểm tra; không đưa số liệu tự ước lượng vào giao diện.
- [ ] Chạy `tests/verify_project.py`, `tests/verify_interactions.py`; thêm kiểm thử hồi quy cho lỗi mới, kiểm tra tốc độ trên bản clone và cập nhật hướng dẫn nếu cách chạy đổi.

**Hoàn tất yêu cầu 3 khi:** dashboard chạy từ bản clone mới; ≥8 loại biểu đồ có map; filter, drill-down, tooltip, cross-filter hoạt động thực tế; insight/dự báo đúng nguồn và kiểm thử đạt.

## Cổng chốt sản phẩm, rồi mới viết báo cáo

- [ ] Thắng và Tài mở pull request từ nhánh riêng; Thắng rà soát số liệu trên dashboard, Tài kiểm tra hình/insight đã tích hợp. Bạn duyệt phần bài toán, nguồn và tính nhất quán với đề tài 09.
- [ ] Gộp về `main`, chạy `run_all.bat`, cả ba bộ kiểm thử và thử trực tiếp dashboard trên bản đã gộp. Nếu rubric đầy đủ yêu cầu mô hình dự báo/insight, xác nhận cả **kết quả mô hình và biểu đồ dự báo** đã có trước khi khóa commit.
- [ ] **Sau khi mọi mục trên hoàn tất**, cả ba cùng viết báo cáo tối thiểu 40 trang theo cấu trúc/IEEE của rubric: bạn phụ trách phần bài toán/dataset/nguồn; Thắng phần pipeline/EDA/insight/mô hình; Tài phần dashboard/tương tác/cài đặt. Cả ba cùng rà soát số liệu, kết luận và tài liệu tham khảo; sau đó quay video demo backup.

Trong buổi bảo vệ, **cả ba cần hiểu pipeline và logic dashboard**, không chỉ phần mình làm; rubric nêu vấn đáp có thể làm giảm điểm nếu thành viên không giải thích được mã hoặc phép tính.
