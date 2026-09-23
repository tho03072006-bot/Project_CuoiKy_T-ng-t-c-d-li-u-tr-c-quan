# Báo cáo Khám phá dữ liệu (EDA)

**Đề tài 09 — Phân tích thị trường Cryptocurrency và mối tương quan với các chỉ số kinh tế vĩ mô**

Tương ứng mục 1.4 của barem (0,75 điểm). Toàn bộ 10 biểu đồ được sinh bằng
`eda_phan_tich.py` (matplotlib + seaborn), chạy lại được từ đầu.

---

## 1. Phương pháp

Dữ liệu đầu vào: 7 bảng trong `data/processed/`, tổng 395.581 dòng.
Phân tích tập trung vào BTC và ETH (hai đồng có lịch sử dài nhất và đầy đủ nhất),
đối chiếu với 15 chỉ số vĩ mô và panel 215 quốc gia.

Ba nguyên tắc áp dụng xuyên suốt:

**Một, dùng log-return thay vì lợi suất thường.** Lợi suất thường không cộng dồn
được theo thời gian và bị lệch khi giá dao động mạnh — với tài sản biến động
80–100%/năm như crypto thì sai lệch này không bỏ qua được.

**Hai, dùng quan sát tháng độc lập khi so với biến vĩ mô.** S&P 500, vàng, CPI và
lợi suất trái phiếu đều là dữ liệu tháng. Nếu lấy cửa sổ 30 ngày trượt theo từng
ngày thì các quan sát chồng lấn nhau tới 29/30, làm hệ số tương quan và mức ý
nghĩa bị thổi phồng. Chi tiết ở mục 4.

**Ba, giữ lại giá trị ngoại lai và đánh dấu, không xoá.** Crypto sập 30% trong một
ngày là sự kiện thị trường có thật. Xoá đi là xoá mất đúng phần cần phân tích.

---

## 2. Mười biểu đồ

| Hình | Nội dung | Phát hiện |
|---|---|---|
| H01 | Độ phủ dữ liệu theo coin | Lịch sử chênh nhau từ 1.839 đến 5.789 ngày — buộc phải chọn mốc cắt mẫu chung |
| H02 | Tỷ lệ thiếu theo cột | Giá và khối lượng gần như đầy đủ; cột on-chain thiếu có hệ thống |
| H03 | Phân phối log-return | Đuôi dày hơn hẳn phân phối chuẩn |
| H04 | Biểu đồ QQ | Xác nhận lại H03 bằng phân vị |
| H05 | Biến động 30 ngày theo năm | Trung vị giảm từ 88% (2013) xuống 42% (2026) |
| H06 | Vốn hoá theo nhóm coin | Trải 6 bậc độ lớn → mọi biểu đồ vốn hoá phải dùng thang log |
| H07 | Ma trận tương quan | Chỉ 2 quan hệ vĩ mô có ý nghĩa thống kê |
| H08 | BTC ↔ S&P 500 | Hệ số 1,10 · r = 0,22 · p = 0,031 |
| H09 | Lạm phát theo châu lục | 36/170 quốc gia vượt 10%; châu Phi 31% — cơ sở cho bản đồ |
| H10 | Ngày ngoại lai | 49/54 rơi vào 2010–2014 — ngưỡng cố định bỏ sót cú sập gần đây |

---

## 3. Phân phối lợi suất không phải phân phối chuẩn

Đây là phát hiện nền tảng, chi phối mọi phân tích sau đó.

| Chỉ số | BTC | ETH | Ý nghĩa |
|---|---|---|---|
| Độ lệch (skew) | −0,75 | −0,14 | BTC lệch trái: cú sập mạnh hơn cú tăng |
| Độ nhọn (kurtosis) | 21,45 | 8,42 | Phân phối chuẩn có giá trị 0 |
| Jarque–Bera | 111.528 | 11.643 | |
| p-value | < 0,001 | < 0,001 | Bác bỏ giả thuyết phân phối chuẩn |

Độ nhọn 21,45 nghĩa là những ngày biến động cực đoan xuất hiện thường xuyên hơn
rất nhiều so với mô hình chuẩn dự báo. Hệ quả thực tế: **không được dùng độ lệch
chuẩn một cách ngây thơ để đo rủi ro** — nó sẽ đánh giá thấp nghiêm trọng khả năng
xảy ra một cú sập lớn. Trên dashboard, thay vì hiển thị "độ lệch chuẩn", nhóm nên
hiển thị mức sụt tối đa (drawdown) và phân vị.

---

## 4. Chỉ hai quan hệ vĩ mô có ý nghĩa thống kê

Tính trên 100 quan sát tháng độc lập, giai đoạn 2018–2026:

| Biến | r | p-value | Kết luận |
|---|---|---|---|
| ETH | +0,773 | < 0,001 | Có ý nghĩa — crypto đi theo nhau |
| **S&P 500** | **+0,215** | **0,031** | **Có ý nghĩa** |
| **Lạm phát Mỹ** | **−0,222** | **0,026** | **Có ý nghĩa** |
| Lãi suất thực | +0,139 | 0,167 | Không có ý nghĩa |
| Chỉ số USD | −0,102 | 0,311 | Không có ý nghĩa |
| Vàng | −0,060 | 0,555 | Không có ý nghĩa |
| VIX | −0,040 | 0,689 | Không có ý nghĩa |

Hai kết luận rút ra:

**Bitcoin hành xử như tài sản rủi ro, không phải tài sản trú ẩn.** Nó đi cùng chiều
với chứng khoán Mỹ (+0,215) và không có quan hệ nào đáng kể với vàng (−0,060).
Luận điểm "Bitcoin là vàng kỹ thuật số" không được dữ liệu ủng hộ.

**Nhưng quan hệ đó yếu.** Hệ số xác định R² chỉ 0,046 — S&P 500 giải thích được
chưa tới 5% biến động của BTC. Phần lớn còn lại đến từ yếu tố nội tại của thị
trường crypto. Đây là điều phải nói thẳng trong báo cáo, vì nếu nhóm trình bày
+0,215 như một quan hệ mạnh thì sẽ bị phản biện ngay.

### Một sai lầm phương pháp đã tránh được

Nếu dùng cửa sổ 30 ngày trượt theo từng ngày, cùng dữ liệu này cho **r = 0,367**
thay vì 0,215 — cao hơn 70%. Nguyên nhân: hai quan sát liền kề chia sẻ 29/30 dữ
liệu, nên số quan sát "độc lập" thực tế nhỏ hơn nhiều so với con số danh nghĩa,
làm cả hệ số lẫn mức ý nghĩa bị thổi phồng.

Đây gần như chắc chắn là một câu hỏi phản biện. Nhóm nên chủ động nêu ra trước.

---

## 5. Ngưỡng phát hiện ngoại lai có vấn đề — và đó là một phát hiện

Quy tắc đang dùng là |z-score| > 4 tính trên toàn bộ lịch sử của từng coin. Kết quả
với BTC: 54 ngày bị đánh dấu, nhưng **49/54 (90,7%) rơi vào giai đoạn 2010–2014**.

Ngày giảm mạnh nhất được ghi nhận là 11/04/2013 (−48,6%). Đối chiếu bốn sự kiện lớn
của thị trường — số liệu lấy thẳng từ dữ liệu, không gõ tay:

| Ngày | Sự kiện | Mức giảm | z-score | Ngưỡng \|z\| > 4 |
|---|---|---|---|---|
| 12/03/2020 | Sập COVID | −37,5% | −10,08 | Bắt được |
| 13/06/2022 | Khủng hoảng Celsius / Terra | −16,8% | −3,98 | **Bỏ sót** (sát ngưỡng) |
| 09/11/2022 | Sụp đổ FTX | −14,9% | −3,49 | **Bỏ sót** |
| 19/05/2021 | Trung Quốc cấm đào | −12,0% | −2,78 | **Bỏ sót** |

Ba trong bốn sự kiện định hình thị trường crypto hiện đại đều lọt lưới. Ngày Celsius
còn thiếu đúng 0,02 độ lệch chuẩn để được đánh dấu — một ngưỡng mà kết quả nhạy cảm
đến vậy thì tự nó đã là dấu hiệu cần xem lại phương pháp.

Lý do: giai đoạn 2010–2014 BTC còn cực kỳ thanh khoản kém, biến động hàng ngày
±25% là bình thường. Độ lệch chuẩn tính trên toàn kỳ bị giai đoạn đó kéo lên rất
cao, nên các cú sập của thời kỳ sau — dù nghiêm trọng về mặt thị trường — vẫn nằm
trong ngưỡng 4 độ lệch chuẩn.

**Khuyến nghị cho dashboard:** dùng z-score theo cửa sổ trượt (ví dụ 365 ngày) thay
vì toàn kỳ, để ngưỡng tự điều chỉnh theo chế độ biến động của từng giai đoạn. Cột
`is_outlier` hiện tại vẫn giữ nguyên để so sánh hai phương pháp — bản thân sự khác
biệt giữa chúng là một insight đáng đưa lên dashboard.

---

## 5b. Một lỗi dữ liệu do EDA phát hiện

Khi vẽ H09, biểu đồ chỉ hiện **5 châu lục** thay vì 6 — toàn bộ Bắc Mỹ biến mất,
và số quốc gia có dữ liệu tụt từ 170 xuống 148.

Nguyên nhân: mã châu lục của Bắc Mỹ trong chuẩn ISO là chuỗi `"NA"`. Pandas mặc
định coi `"NA"` là ký hiệu giá trị thiếu, nên đã biến 22 quốc gia Bắc Mỹ thành ô
trống. Lỗi này im lặng hoàn toàn — không có cảnh báo nào, pipeline chạy xong vẫn
báo thành công.

Cách sửa, đã áp dụng trong `pipeline_tien_xu_ly.py`:

```python
cc = pd.read_csv("country_codes.csv", keep_default_na=False, na_values=[""])
```

Sau khi sửa, đủ 170/170 quốc gia có châu lục. Đây là ví dụ điển hình cho lý do
rubric bắt buộc phải có bước EDA **trước** khi dựng dashboard: nếu bỏ qua bước này,
bản đồ sẽ để trống toàn bộ Bắc Mỹ và không ai phát hiện ra cho đến lúc bảo vệ.

### Phân bố lạm phát 2023 theo châu lục (sau khi sửa)

| Châu lục | Số nước | Vượt 10% | Tỷ lệ | Trung vị |
|---|---|---|---|---|
| Châu Phi | 45 | 14 | 31,1% | 6,3% |
| Châu Á | 42 | 9 | 21,4% | 3,7% |
| Châu Âu | 40 | 8 | 20,0% | 6,5% |
| Nam Mỹ | 10 | 2 | 20,0% | 5,2% |
| Châu Đại Dương | 11 | 2 | 18,2% | 6,3% |
| Bắc Mỹ | 22 | 1 | 4,5% | 4,5% |

Châu Phi có tỷ lệ quốc gia lạm phát cao nhất. Châu Á có trung vị thấp nhất nhưng
chứa các ca cực đoan nhất — Lebanon 221%, Thổ Nhĩ Kỳ 54%, Iran 45%. Nghĩa là trên
bản đồ, thang màu phải xử lý được giá trị ngoại lai cực lớn: nếu để thang tuyến
tính chạy tới 221%, toàn bộ phần còn lại của thế giới sẽ cùng một màu nhạt.

---

## 6. Những gì EDA quyết định cho thiết kế Dashboard

| Phát hiện từ EDA | Ràng buộc cho dashboard |
|---|---|
| Vốn hoá trải 6 bậc độ lớn (H06) | Mọi biểu đồ vốn hoá phải có nút chuyển thang log |
| Lịch sử các coin chênh nhau rất xa (H01) | Bộ lọc thời gian phải mặc định cắt về khoảng chung |
| Đuôi phân phối dày (H03, H04) | Hiển thị drawdown và phân vị, không chỉ độ lệch chuẩn |
| Biến động thay đổi theo giai đoạn (H05) | Cho phép so sánh theo từng năm, không gộp toàn kỳ |
| Chuỗi vĩ mô là dữ liệu tháng | Biểu đồ tương quan phải ghi rõ tần suất; không so theo ngày |
| Lạm phát phân tán theo không gian (H09) | Bản đồ mặc định năm 2023, tô theo lạm phát |
| Lebanon 221% làm lệch thang màu (H09) | Bản đồ phải cắt ngưỡng hoặc dùng thang phân vị |
| Ngưỡng ngoại lai lệch theo thời kỳ (H10) | Thêm z-score cửa sổ trượt bên cạnh cột hiện có |

---

## 7. Hạn chế của phần EDA này

Phân tích tập trung vào BTC và ETH, chưa mở rộng cho toàn bộ 39 đồng coin — các
đồng còn lại có lịch sử ngắn hơn nhiều và kết quả sẽ kém ổn định.

Tương quan Pearson chỉ đo quan hệ tuyến tính. Quan hệ phi tuyến, hoặc quan hệ có
độ trễ (macro tác động sau vài tháng), chưa được kiểm tra — đó là việc của phần
mô hình dự báo.

Giai đoạn phân tích bắt đầu từ 2018 để có đủ dữ liệu vĩ mô chất lượng. Chu kỳ
2013–2017 nằm ngoài phạm vi, nên kết luận không nên khái quát cho toàn bộ lịch sử
Bitcoin.

Số quan sát tháng là 100 — đủ cho kiểm định tương quan nhưng còn khiêm tốn. Một
vài quan hệ đang ở ranh giới ý nghĩa (p ≈ 0,03) có thể đổi kết luận nếu thêm hoặc
bớt vài tháng.
