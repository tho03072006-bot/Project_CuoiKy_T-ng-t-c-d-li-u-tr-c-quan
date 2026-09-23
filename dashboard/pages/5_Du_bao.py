# -*- coding: utf-8 -*-
"""Đánh giá ngoài mẫu và dự báo tại mốc chốt dữ liệu, không huấn luyện trong UI."""
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from style import C1_BLUE, C8_RED, GRID, SEQ_BLUE, so_viet, ve

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"


@st.cache_resource
def nap_mo_hinh(dau_van_tay):
    """Đổi cache theo mtime để huấn luyện lại được phản ánh ngay trên dashboard."""
    packs = []
    for name in ("mo_hinh_tuyen_tinh.pkl", "mo_hinh_logistic.pkl"):
        with (MODEL_DIR / name).open("rb") as f:
            packs.append(pickle.load(f))
    return packs


st.title("Mô hình dự báo")
st.caption("BTC · đánh giá theo thời gian trên tập test cố định. Bộ lọc sidebar không thay đổi tập kiểm định.")
files = [MODEL_DIR / n for n in ("mo_hinh_tuyen_tinh.pkl", "mo_hinh_logistic.pkl")]
if not all(p.exists() for p in files):
    st.error("Chưa có mô hình. Chạy python models/du_bao.py từ thư mục project.")
    st.stop()
tt, lg = nap_mo_hinh(tuple(p.stat().st_mtime_ns for p in files))
a, b = tt["chi_so"], lg["chi_so"]
if "r2_test" not in a:
    st.warning("Kết quả mô hình cũ. Chạy lại python models/du_bao.py để tạo kiểm định ngoài mẫu.")
    st.stop()

with st.container(border=True):
    st.subheader("Hồi quy tuyến tính — lợi suất BTC tháng")
    st.caption(f"Train: {a['ngay_train_dau']} → {a['ngay_train_cuoi']} ({a['n_train']} tháng). "
               f"Test: {a['ngay_test_dau']} → {a['ngay_test_cuoi']} ({a['n_test']} tháng).")
    with st.container(horizontal=True):
        st.metric("R² ngoài mẫu", so_viet(a['r2_test'], 3), border=True)
        st.metric("MAE mô hình", f"{so_viet(100*a['mae_test'])} điểm %", border=True)
        st.metric("MAE mốc cơ sở", f"{so_viet(100*a['mae_co_so'])} điểm %", border=True)
        st.metric("RMSE mô hình", f"{so_viet(100*a['rmse_test'])} điểm %", border=True)
    st.info("Dự báo một bước: mỗi tháng sử dụng dữ liệu đã có trước tháng cần dự báo. "
            "Mốc cơ sở dự báo lợi suất bằng 0 (giá không đổi). R² âm nghĩa mô hình "
            "kém hơn dự đoán bằng trung bình tập test; so sánh MAE/RMSE riêng với mốc giá không đổi.")
    d = tt['bang_du_bao'].copy()
    d['thang'] = pd.to_datetime(d['thang'])
    actual_col = 'loi_suat_thuc' if 'loi_suat_thuc' in d else 'loi_suat_thuc_te'
    if actual_col not in d:
        # Tính cùng định nghĩa tháng hoàn tất nếu gói kết quả chỉ chứa dự đoán.
        import data_layer as dl
        observed = dl.bang_thang().set_index('thang')['btc_ret']
        d['loi_suat_thuc'] = d['thang'].map(observed)
        actual_col = 'loi_suat_thuc'
    f = go.Figure()
    f.add_trace(go.Scatter(x=d.thang, y=d.can_duoi*100, line=dict(width=0), showlegend=False, hoverinfo='skip'))
    f.add_trace(go.Scatter(x=d.thang, y=d.can_tren*100, line=dict(width=0), fill='tonexty',
                          fillcolor='rgba(42,120,214,0.13)', name='Khoảng dự báo danh nghĩa 95%'))
    f.add_trace(go.Scatter(x=d.thang, y=d[actual_col]*100, name='Thực tế ngoài mẫu', line=dict(color='#0b0b0b')))
    f.add_trace(go.Scatter(x=d.thang, y=d.loi_suat_du_bao*100, name='OLS dự báo', line=dict(color=C1_BLUE)))
    f.add_trace(go.Scatter(x=d.thang, y=np.zeros(len(d)), name='Cơ sở: 0%', line=dict(color=C8_RED, dash='dot')))
    f.update_layout(height=430, yaxis_title='Lợi suất tháng (%)', hovermode='x unified', margin_t=30)
    ve(f, key='forecast_holdout')
    coverage = ((d[actual_col] >= d.can_duoi) & (d[actual_col] <= d.can_tren)).mean()
    st.caption(f"Khoảng dự báo chứa {so_viet(coverage*100, 1)}% quan sát test. "
               "Mức 95% dựa trên giả định OLS, không bảo đảm độ phủ tương lai với phân phối đuôi dày.")
    status = "thấp hơn" if a['mae_test'] < a['mae_co_so'] else "không thấp hơn"
    st.markdown(f"**Kết quả:** MAE của OLS {status} mốc giá không đổi trên tập test này.")
    st.download_button('Tải dự báo ngoài mẫu (CSV)', d.to_csv(index=False).encode('utf-8-sig'),
                       'du_bao_btc_ngoai_mau.csv', 'text/csv')

next_m = tt.get('du_bao_tiep')
if next_m:
    with st.container(border=True):
        st.subheader("Dự báo tháng kế tiếp tại mốc chốt")
        st.caption(f"Tháng mục tiêu: {pd.Timestamp(next_m['thang']):%m/%Y}. "
                   f"Chỉ dùng thông tin đến {next_m['ngay_thong_tin']}; đây không phải dự báo theo thời gian thực.")
        with st.container(horizontal=True):
            st.metric('Lợi suất dự báo', f"{so_viet(100*next_m['loi_suat_du_bao'])}%", border=True)
            st.metric('Khoảng dự báo danh nghĩa 95%',
                      f"{so_viet(100*next_m['can_duoi'],1)}% → {so_viet(100*next_m['can_tren'],1)}%", border=True)
        nf = go.Figure(go.Scatter(x=[pd.Timestamp(next_m['thang'])], y=[100*next_m['loi_suat_du_bao']],
            mode='markers', name='Tháng kế tiếp', marker=dict(size=12, color=C1_BLUE),
            error_y=dict(type='data', symmetric=False,
                         array=[100*(next_m['can_tren']-next_m['loi_suat_du_bao'])],
                         arrayminus=[100*(next_m['loi_suat_du_bao']-next_m['can_duoi'])])))
        nf.update_layout(height=250, yaxis_title='Lợi suất tháng (%)', margin_t=20, showlegend=False)
        ve(nf, key='forecast_next_month')

with st.container(border=True):
    st.subheader('Hồi quy Logistic — xác suất BTC tăng ngày kế tiếp')
    st.caption(f"Train {b['ngay_train_dau']} → {b['ngay_train_cuoi']}; "
               f"test {b['ngay_test_dau']} → {b['ngay_test_cuoi']} ({b['n_test']} phiên).")
    with st.container(horizontal=True):
        st.metric('ROC AUC test', so_viet(b['auc'],3), border=True)
        st.metric('Accuracy test', f"{so_viet(100*b['accuracy'])}%", border=True)
        st.metric('Accuracy cơ sở', f"{so_viet(100*b['accuracy_co_so'])}%", border=True)
        st.metric('F1 test', so_viet(b['f1'],3), border=True)
    st.caption("Cơ sở luôn dự đoán lớp chiếm đa số trong tập train. "
               "Scaler và mô hình đánh giá chỉ học trên train, không xáo trộn thứ tự thời gian.")
    latest = lg['phien_gan_nhat']
    st.metric(f"Xác suất tăng ngày {pd.Timestamp(latest['ngay']):%d/%m/%Y}",
              f"{so_viet(100*latest['xac_suat_tang'])}%")
    st.progress(float(latest['xac_suat_tang']))
    st.caption(f"Dùng dữ liệu đến {latest.get('ngay_thong_tin', 'phiên trước')}. "
               "Dự báo tại mốc cuối dataset, không phải tín hiệu giao dịch hiện tại. "
               "Xác suất chưa được kiểm định hiệu chuẩn; AUC 0,5 tương ứng phân hạng ngẫu nhiên.")

left, right = st.columns(2)
with left, st.container(border=True):
    st.markdown('**Đường ROC trên tập test**')
    roc = lg['roc']
    f = go.Figure(go.Scatter(x=roc['fpr'], y=roc['tpr'], name='Logistic', line=dict(color=C1_BLUE)))
    f.add_trace(go.Scatter(x=[0,1], y=[0,1], name='Ngẫu nhiên', line=dict(color=GRID, dash='dot')))
    f.update_layout(height=370, margin_t=25, xaxis_title='Tỷ lệ báo tăng sai (FPR)',
                    yaxis_title='Tỷ lệ phát hiện ngày tăng (TPR)', hovermode='closest')
    ve(f, key='roc_holdout')
with right, st.container(border=True):
    st.markdown('**Ma trận nhầm lẫn trên tập test**')
    cm = np.array(lg['ma_tran_nham_lan'])
    ratio = np.divide(cm, cm.sum(axis=1, keepdims=True), out=np.zeros_like(cm, dtype=float), where=cm.sum(axis=1, keepdims=True)!=0)
    f = go.Figure(go.Heatmap(z=ratio, text=cm, texttemplate='%{text}',
        x=['Đoán không tăng','Đoán tăng'], y=['Thật không tăng','Thật tăng'],
        colorscale=SEQ_BLUE, zmin=0, zmax=1, showscale=False,
        hovertemplate='%{y}<br>%{x}<br>%{text} phiên · %{z:.1%}<extra></extra>'))
    f.update_layout(height=370, margin_t=25, yaxis_autorange='reversed')
    ve(f, key='confusion_holdout')

with st.container(border=True):
    st.markdown('**Hệ số chuẩn hóa OLS trên tập train**')
    coefs = pd.DataFrame({'Biến': list(tt['he_so_chuan_hoa']), 'Hệ số': list(tt['he_so_chuan_hoa'].values())}).sort_values('Hệ số')
    f = px.bar(coefs, x='Hệ số', y='Biến', orientation='h')
    f.update_layout(height=350, margin_t=25, hovermode='closest')
    ve(f, key='ols_coefficients')
    st.caption('Hệ số cho biết liên hệ có điều kiện trong mô hình; không phải bằng chứng tác động nhân quả.')

with st.expander('Phương pháp và hạn chế cần hiểu khi vấn đáp'):
    st.markdown("""
- **OLS:** lợi suất BTC trễ 1 tháng và biến vĩ mô trễ 2 tháng; chỉ dùng tháng lịch hoàn tất.
  Chọn/chuẩn hóa biến trên train. Đánh giá ngoài mẫu với mô hình giữ cố định;
  mô hình dùng cho dự báo kế tiếp được fit lại trên toàn bộ lịch sử hợp lệ.
- **Logistic:** đặc trưng giá và khối lượng đều trễ ít nhất 1 phiên.
  Không sử dụng lợi suất cùng ngày để đoán nhãn của chính ngày đó.
- Dữ liệu vĩ mô không có lịch công bố và vintage lịch sử. Trễ 2 tháng là giả định
  bảo thủ, vẫn chưa kiểm chứng được ảnh hưởng của sửa đổi dữ liệu về sau.
- Missing không biến thành ngày giảm; mô hình chỉ dùng hàng có đủ đặc trưng và nhãn.
- Dữ liệu quan sát, tập coin hạn chế và chỉ một giai đoạn holdout; kết quả không
  chứng minh nhân quả hay bảo đảm dự báo ở thị trường tương lai.
""")
    st.dataframe(pd.DataFrame(tt['he_so']), hide_index=True, width='stretch')
