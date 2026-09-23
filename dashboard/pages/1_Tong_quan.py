# -*- coding: utf-8 -*-
"""Trang Tổng quan: 4 thẻ KPI + đường giá theo thời gian.

Trang này KHÔNG tự vẽ bộ lọc. Nó đọc st.session_state["bo_loc"] do app.py đặt
sẵn - app.py chạy trước mỗi trang nên khoá này luôn tồn tại.

Nguyên tắc bắt buộc của đồ án: mọi con số hiện trên thẻ KPI đều tính từ
DataFrame, không hằng số gõ tay. Nếu dữ liệu được nạp lại thì số tự đổi theo.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import data_layer as dl
from style import dinh_dang_tien, so_viet, tieu_de, ve

# Số ngày dùng để tính biến động của thẻ KPI giá BTC.
CUA_SO_NGAY = 30

bo_loc = st.session_state["bo_loc"]
df = dl.loc_du_lieu(**bo_loc)

st.title("Tổng quan thị trường")
st.caption(
    f"Khoảng lọc: {bo_loc['tu_ngay']:%d/%m/%Y} → {bo_loc['den_ngay']:%d/%m/%Y} · "
    f"Nhóm: {bo_loc['nhom_coin']}"
)

if df.empty:
    st.warning(
        "Bộ lọc hiện tại không còn dòng dữ liệu nào. Hãy nới khoảng ngày hoặc "
        "chọn thêm coin ở thanh bên.",
        icon=":material/filter_alt_off:",
    )
    st.stop()


# =============================================================================
# 4 thẻ KPI
# =============================================================================
def lay_chuoi_btc() -> pd.DataFrame:
    """Lấy riêng chuỗi BTC trong khoảng ngày đang lọc.

    Gọi lại loc_du_lieu với đúng một ticker thay vì lọc trên `df`: ba KPI đầu mô
    tả TOÀN THỊ TRƯỜNG nên phải độc lập với việc người dùng có tick BTC hay
    không. Nếu lấy từ `df`, bỏ tick BTC là ba thẻ trống ngay.
    """
    return dl.loc_du_lieu(
        pd.Timestamp(bo_loc["tu_ngay"]) - pd.Timedelta(days=CUA_SO_NGAY),
        bo_loc["den_ngay"], ["BTC"], dl.NHOM_TAT_CA
    ).sort_values("date")


btc = lay_chuoi_btc()
btc_trong_khoang = btc[btc["date"] >= pd.Timestamp(bo_loc["tu_ngay"])]

if btc_trong_khoang.empty:
    st.info(
        "Khoảng ngày đang chọn nằm ngoài lịch sử giá của BTC nên ba thẻ đầu "
        "không tính được.",
        icon=":material/info:",
    )
    gia_moi = thay_doi_pct = thi_phan = tong_von_hoa = None
    ngay_chot = pd.Timestamp(bo_loc["den_ngay"])
else:
    dong_cuoi = btc.iloc[-1]
    ngay_chot = dong_cuoi["date"]
    gia_moi = float(dong_cuoi["price_usd"])

    # Lấy phiên gần nhất cách ngày chốt ÍT NHẤT 30 ngày. Không dùng iloc[-31] vì
    # chuỗi có thể khuyết phiên; đếm lùi theo chỉ số sẽ ra mốc sai ngày.
    truoc_do = btc[btc["date"] <= ngay_chot - pd.Timedelta(days=CUA_SO_NGAY)]
    thay_doi_pct = (
        float(gia_moi / truoc_do.iloc[-1]["price_usd"] - 1) * 100
        if not truoc_do.empty
        else None
    )

    # `btc_dominance_pct` và `total_mcap` là chỉ số của CẢ THỊ TRƯỜNG, giá trị
    # giống nhau ở mọi ticker trong cùng một ngày (đã kiểm chứng: nunique = 1),
    # nên đọc từ dòng BTC là đủ, khỏi phải cộng lại bảng vốn hoá 185k dòng.
    thi_phan = float(dong_cuoi["btc_dominance_pct"])
    tong_von_hoa = float(dong_cuoi["total_mcap"])

so_coin = df["ticker"].nunique()

with st.container(horizontal=True):
    st.metric(
        "Giá BTC",
        f"{dinh_dang_tien(gia_moi)}" if gia_moi is not None else "—",
        # Dấu + phải tự thêm: Streamlit chỉ dựa vào dấu trừ ở đầu chuỗi để tô
        # màu mũi tên, chuỗi dương không có dấu nhìn dễ nhầm là số tuyệt đối.
        delta=f"{'+' if thay_doi_pct >= 0 else ''}{so_viet(thay_doi_pct)}% "
        f"/ {CUA_SO_NGAY} ngày"
        if thay_doi_pct is not None
        else None,
        border=True,
        help=f"Chốt phiên {ngay_chot:%d/%m/%Y}. KPI BTC/toàn thị trường chỉ theo khoảng ngày; so sánh 30 ngày có dùng lịch sử trước ngày bắt đầu lọc.",
    )
    st.metric(
        "Thị phần BTC",
        f"{so_viet(thi_phan, 1)}%" if thi_phan is not None else "—",
        border=True,
        help="Vốn hoá BTC / tổng vốn hoá toàn thị trường tại ngày chốt.",
    )
    st.metric(
        "Tổng vốn hoá",
        dinh_dang_tien(tong_von_hoa),
        border=True,
        help="Cộng vốn hoá toàn bộ coin có mặt trong ngày chốt.",
    )
    st.metric(
        "Coin đang lọc",
        so_viet(so_coin, 0),
        delta=f"{so_viet(len(df), 0)} dòng",
        delta_color="off",
        border=True,
        help="Số ticker còn lại sau khi áp cả bốn tầng lọc.",
    )


# =============================================================================
# Biểu đồ đường: giá theo thời gian
# =============================================================================
st.markdown("")
with st.container(border=True):
    # Nhãn "Hình 1" để đối chiếu với báo cáo; câu KẾT LUẬN nằm ở tiêu đề hình
    # bên dưới nên hai dòng này không trùng ý nhau.
    dau_de, dau_toggle = st.columns([4, 1], vertical_alignment="center")
    with dau_de:
        st.markdown("**Hình 1 — Đường giá (line chart)**")
    with dau_toggle:
        # Mặc định BẬT thang log: giá các coin chênh nhau tới 6 bậc độ lớn
        # (BTC ~76.000 USD, DOGE ~0,1 USD). Để thang thường thì mọi coin nhỏ bị
        # ép sát trục 0 thành một đường thẳng, nhìn không ra gì.
        thang_log = st.toggle(
            "Thang log",
            value=True,
            key="w_thang_log",
            help="Tắt để xem giá theo thang tuyến tính.",
        )

    # --- Câu kết luận cho tiêu đề, tính từ chính dữ liệu đang hiển thị --------
    # Tính mức tăng/giảm của từng coin trong khoảng lọc để biết coin nào dẫn đầu.
    dau_cuoi = (
        df.sort_values("date")
        .groupby("ticker")["price_usd"]
        .agg(dau="first", cuoi="last", so_phien="count")
    )
    dau_cuoi = dau_cuoi[(dau_cuoi["dau"] > 0) & (dau_cuoi["so_phien"] >= 2)]
    bien_dong = (dau_cuoi["cuoi"] / dau_cuoi["dau"] - 1) * 100

    if len(bien_dong) == 0:
        chinh = "Chưa đủ dữ liệu để rút kết luận"
        phu = "Cần ít nhất hai phiên có giá cho mỗi coin để tính thay đổi."
    elif len(bien_dong) == 1:
        ten = bien_dong.index[0]
        chinh = f"{ten} {'tăng' if bien_dong.iloc[0] >= 0 else 'giảm'} {so_viet(abs(bien_dong.iloc[0]), 1)}% trong khoảng đã chọn"
        phu = (
            f"Giá {ten} từ {dinh_dang_tien(dau_cuoi['dau'].iloc[0])} lên "
            f"{dinh_dang_tien(dau_cuoi['cuoi'].iloc[0])}."
            if bien_dong.iloc[0] >= 0
            else f"Giá {ten} từ {dinh_dang_tien(dau_cuoi['dau'].iloc[0])} xuống "
            f"{dinh_dang_tien(dau_cuoi['cuoi'].iloc[0])}."
        )
    else:
        cao = bien_dong.idxmax()
        thap = bien_dong.idxmin()
        chinh = f"{cao} dẫn đầu với {so_viet(bien_dong[cao], 1)}%, {thap} bét bảng {so_viet(bien_dong[thap], 1)}%"
        phu = (
            f"Chênh lệch {so_viet(bien_dong[cao] - bien_dong[thap], 1)} điểm phần trăm "
            f"giữa {len(bien_dong)} coin đủ dữ liệu. Mốc đầu/cuối theo từng coin."
        )

    hinh = px.line(
        df.sort_values("date"),
        x="date",
        y="price_usd",
        color="ticker",
        markers=df["date"].nunique() == 1,
        labels={"date": "", "price_usd": "Giá (USD)", "ticker": "Coin"},
    )
    hinh.update_layout(
        title=tieu_de(chinh, phu),
        height=520,
        # Thang log của Plotly nhận log10 của giá trị, nên nhãn trục phải để
        # Plotly tự sinh; chỉ đổi `type` là đủ.
        yaxis=dict(type="log" if thang_log else "linear"),
        # hovermode "x unified" gộp mọi coin vào một khung tooltip theo ngày,
        # nhờ vậy so sánh được các coin ở cùng một phiên.
        xaxis=dict(hoverformat="%d/%m/%Y"),
    )
    hinh.update_traces(
        line=dict(width=1.6),  # nét mảnh, đồng bộ với hình EDA
        # Ở chế độ "x unified", Plotly tự in ngày ở đầu khung và tên coin ở đầu
        # mỗi dòng, nên hovertemplate chỉ cần phần giá trị.
        hovertemplate="%{y:,.4f} USD<extra></extra>",
    )

    ve(
        hinh,
        key="bieu_do_gia",
    )

    st.caption(
        f"Nguồn: data/processed/fact_crypto_daily.csv.gz · "
        f"{so_viet(len(df), 0)} quan sát, {so_coin} coin, "
        f"{bo_loc['tu_ngay']:%d/%m/%Y}–{bo_loc['den_ngay']:%d/%m/%Y}"
    )
