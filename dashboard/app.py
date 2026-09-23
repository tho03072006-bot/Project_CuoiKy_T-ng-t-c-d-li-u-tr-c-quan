# -*- coding: utf-8 -*-
"""Điểm vào của dashboard - chạy bằng: streamlit run dashboard/app.py

Vì sao file này vừa là trang chủ vừa là bộ khung: `st.navigation` biến app.py
thành router, Streamlit chạy lại app.py TRƯỚC mỗi trang con. Nhờ vậy sidebar
khai báo ở đây xuất hiện trên mọi trang mà không phải chép lại code.

(Nếu để Streamlit tự dò thư mục pages/ theo cách cũ thì app.py chỉ chạy khi đang
đứng ở trang chủ, người dùng bấm sang trang khác là bộ lọc biến mất.)
"""
from __future__ import annotations

import datetime as dt

import streamlit as st

import data_layer as dl
from style import INK_SOFT, dang_ky_template, so_viet

# st.set_page_config phải là lệnh Streamlit ĐẦU TIÊN, nếu không Streamlit báo lỗi.
st.set_page_config(
    page_title="Crypto & Vĩ mô — Đề tài 09",
    page_icon=":material/monitoring:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Đăng ký bảng màu chung. Gọi ở đây, một lần, trước khi bất kỳ trang nào vẽ hình.
dang_ky_template()

# Mặc định bắt đầu từ 2018: toàn bộ kết quả thống kê đã kiểm chứng trong CLAUDE.md
# tính trên 100 quan sát tháng độc lập giai đoạn 2018-2026. Để dashboard khớp với
# báo cáo thì khung ngày mặc định phải trùng khung đó.
NGAY_BAT_DAU_MAC_DINH = dt.date(2018, 1, 1)

# Hai coin mở sẵn khi vào app: vốn hoá lớn nhất và có tương quan r = +0,773.
COIN_MAC_DINH = ["BTC", "ETH"]

# Các mốc ngưỡng vốn hoá cho tầng lọc thứ 4.
# Vốn hoá trải 6 bậc độ lớn (bẫy dữ liệu số 4) nên slider tuyến tính là vô dụng:
# kéo 99% chiều dài thanh trượt vẫn chưa ra khỏi vùng coin lớn. Dùng các mốc
# nhảy theo bậc 10 để mỗi nấc là một hạng coin thật sự khác nhau.
NGUONG_VON_HOA = [
    ("Không giới hạn", 0.0),
    ("≥ 1 triệu USD", 1e6),
    ("≥ 10 triệu USD", 1e7),
    ("≥ 100 triệu USD", 1e8),
    ("≥ 1 tỷ USD", 1e9),
    ("≥ 10 tỷ USD", 1e10),
]

# Mọi khoá widget của sidebar đều mang tiền tố này, để nút "Đặt lại bộ lọc" biết
# chính xác cần xoá những gì mà không đụng tới trạng thái của các trang.
TIEN_TO_WIDGET = "w_"


def dat_lai_bo_loc() -> None:
    """Xoá mọi khoá widget của sidebar khỏi session_state.

    Streamlit chỉ áp giá trị `default`/`value` khi khoá CHƯA tồn tại trong
    session_state. Vì vậy cách đặt lại đúng là xoá hẳn khoá đi rồi để lần chạy
    kế tiếp dựng lại widget từ mặc định - gán đè giá trị sẽ bị Streamlit báo lỗi
    "cannot be modified after the widget is instantiated".

    Xoá cả các khoá lựa chọn cross-filter của từng trang (tiền tố "chon_") để
    bấm một nút là về đúng trạng thái lúc mới mở app.
    """
    for khoa in [
        k
        for k in st.session_state
        if k.startswith(TIEN_TO_WIDGET) or k.startswith("chon_") or k.startswith("bando_")
    ]:
        del st.session_state[khoa]


def ve_sidebar() -> None:
    """Vẽ bộ lọc dùng chung rồi cất kết quả vào st.session_state["bo_loc"].

    Cất vào session_state chứ không trả về giá trị: các trang con là file riêng,
    không gọi được hàm này theo kiểu thông thường. session_state là chỗ duy nhất
    mọi trang cùng đọc được, và Streamlit giữ nguyên nó qua các lần rerun.

    Khoá của dict trùng đúng tên tham số của dl.loc_du_lieu() nên trang con chỉ
    cần viết dl.loc_du_lieu(**bo_loc).
    """
    ngay_dau, ngay_cuoi = dl.khoang_ngay_crypto()
    gioi_han_dau, gioi_han_cuoi = ngay_dau.date(), ngay_cuoi.date()
    # max() để nếu sau này dữ liệu bắt đầu muộn hơn 2018 thì mặc định vẫn hợp lệ,
    # không rơi ra ngoài min_value và làm widget văng lỗi.
    bat_dau_mac_dinh = max(gioi_han_dau, NGAY_BAT_DAU_MAC_DINH)

    with st.sidebar:
        st.markdown("### Bộ lọc dùng chung")

        # --- Tầng 1: khoảng ngày ---------------------------------------------
        khoang = st.date_input(
            "Khoảng ngày",
            value=(bat_dau_mac_dinh, gioi_han_cuoi),
            min_value=gioi_han_dau,
            max_value=gioi_han_cuoi,
            format="DD/MM/YYYY",
            key="w_khoang_ngay",
            help=f"Dữ liệu giá crypto chỉ có tới {ngay_cuoi:%d/%m/%Y}.",
        )
        # Trong lúc người dùng mới bấm ngày đầu, widget trả về tuple 1 phần tử.
        # Không bắt trường hợp này thì app văng IndexError giữa chừng.
        tu_ngay = khoang[0] if khoang else bat_dau_mac_dinh
        den_ngay = khoang[1] if len(khoang) > 1 else gioi_han_cuoi

        # --- Tầng 2: nhóm coin ------------------------------------------------
        nhom = st.selectbox(
            "Nhóm coin",
            dl.danh_sach_nhom_coin(),
            key="w_nhom_coin",
            help="Lọc theo phân loại trong dim_coin (Layer 1, DeFi, Meme…).",
        )

        # --- Tầng 3: coin cụ thể, danh sách phụ thuộc nhóm vừa chọn -----------
        coin_hop_le = dl.coin_co_gia(nhom)
        mac_dinh = [c for c in COIN_MAC_DINH if c in coin_hop_le] or coin_hop_le[:2]
        chon_coin = st.multiselect(
            "Coin",
            coin_hop_le,
            default=mac_dinh,
            # Khoá gắn tên nhóm: đổi nhóm là sinh widget mới, `default` được áp
            # lại. Nếu dùng khoá cố định, Streamlit giữ lựa chọn cũ và báo lỗi
            # vì coin đó không còn nằm trong danh sách options mới.
            key=f"w_coin__{nhom}",
            help=f"{len(coin_hop_le)} coin có lịch sử giá trong nhóm này.",
        )

        # --- Tầng 4: ngưỡng vốn hoá tối thiểu --------------------------------
        nhan_nguong = st.select_slider(
            "Vốn hoá tối thiểu",
            options=[nhan for nhan, _ in NGUONG_VON_HOA],
            value=NGUONG_VON_HOA[0][0],
            key="w_nguong_von_hoa",
            help="Bỏ các phiên mà coin còn quá nhỏ. Lọc theo vốn hoá của CHÍNH "
            "phiên đó, không phải vốn hoá hiện nay.",
        )
        nguong = dict(NGUONG_VON_HOA)[nhan_nguong]

        st.divider()
        st.button(
            "Đặt lại bộ lọc",
            icon=":material/restart_alt:",
            width="stretch",
            # on_click chạy TRƯỚC khi script chạy lại, đúng thời điểm duy nhất
            # còn được phép xoá khoá của widget khỏi session_state.
            on_click=dat_lai_bo_loc,
            help="Trả cả 4 tầng lọc và mọi vùng chọn trên biểu đồ về mặc định.",
        )

        st.caption("Bộ lọc coin áp dụng cho Tổng quan và Cấu trúc thị trường. "
                   "Vĩ mô dùng khoảng ngày; Bản đồ có bộ lọc địa lý riêng; Dự báo dùng tập kiểm định cố định.")
        st.caption(
            f"Toàn bộ dữ liệu giá: {ngay_dau:%d/%m/%Y} → {ngay_cuoi:%d/%m/%Y} · "
            f"{len(dl.coin_co_gia())}/{len(dl.nap_dim_coin())} coin có giá"
        )

    st.session_state["bo_loc"] = {
        "tu_ngay": tu_ngay,
        "den_ngay": den_ngay,
        "danh_sach_coin": chon_coin,
        "nhom_coin": nhom,
        "von_hoa_toi_thieu": nguong,
    }


def trang_chu() -> None:
    """Trang chủ: giới thiệu đề tài và cho biết đang có những bảng nào trong tay.

    Mọi con số ở đây đều đếm thẳng từ DataFrame đã nạp, không gõ tay, để nếu
    pipeline tiền xử lý chạy lại và số dòng đổi thì trang này tự cập nhật.
    """
    st.title("Thị trường Cryptocurrency và các chỉ số kinh tế vĩ mô")
    st.markdown(
        "**Đề tài 09** · Môn Tương tác Dữ liệu Trực quan · "
        f"<span style='color:{INK_SOFT}'>Dashboard Streamlit + Plotly</span>",
        unsafe_allow_html=True,
    )

    ngay_dau, ngay_cuoi = dl.khoang_ngay_crypto()
    bang = {
        "fact_crypto_daily": dl.nap_crypto_daily(),
        "fact_market_daily": dl.nap_market_daily(),
        "fact_macro_daily": dl.nap_macro_daily(),
        "fact_country_macro": dl.nap_country_macro(),
        "fact_fx_daily": dl.nap_fx_daily(),
        "dim_coin": dl.nap_dim_coin(),
        "dim_country": dl.nap_dim_country(),
    }
    tong_dong = sum(len(df) for df in bang.values())

    with st.container(horizontal=True):
        st.metric("Bảng dữ liệu", f"{len(bang)}", border=True)
        st.metric("Tổng số dòng", so_viet(tong_dong, 0), border=True)
        st.metric(
            "Coin có lịch sử giá",
            f"{len(dl.coin_co_gia())}/{len(bang['dim_coin'])}",
            border=True,
        )
        st.metric(
            "Khoảng thời gian",
            f"{ngay_dau:%Y} – {ngay_cuoi:%Y}",
            border=True,
        )

    st.markdown("")
    trai, phai = st.columns([3, 2])

    with trai:
        with st.container(border=True):
            st.markdown("**Các bảng đang nạp**")
            st.dataframe(
                [
                    {
                        "Bảng": ten,
                        "Số dòng": len(df),
                        "Số cột": df.shape[1],
                    }
                    for ten, df in bang.items()
                ],
                hide_index=True,
                width="stretch",
            )

    with phai:
        with st.container(border=True):
            st.markdown("**Cách dùng**")
            st.markdown(
                "1. Đặt bộ lọc ở thanh bên trái — khoảng ngày, nhóm coin, coin.\n"
                "2. Tổng quan và Cấu trúc dùng bộ lọc coin; Vĩ mô dùng khoảng ngày.\n"
                "3. Bản đồ có drill-down địa lý; Dự báo hiển thị đánh giá ngoài mẫu."
            )
            st.info(
                f"Dữ liệu giá crypto dừng ở {ngay_cuoi:%d/%m/%Y}, còn chỉ số vĩ mô "
                "chạy tới 09/2026. Khi so sánh hai nguồn phải cắt về cùng khoảng.",
                icon=":material/info:",
            )

    with st.expander("Hạn chế đã biết của dữ liệu"):
        st.markdown(
            f"- Chỉ **{len(dl.coin_co_gia())}/{len(bang['dim_coin'])}** coin có "
            "lịch sử giá; các coin còn lại chỉ có vốn hoá và khối lượng.\n"
            "- Các biến vĩ mô (`sp500`, `gold_usd`, `cpi_*`…) gốc là dữ liệu "
            "**tháng** đã forward-fill sang ngày, nên không được tính tương quan "
            "ở tần suất ngày.\n"
            "- Cột `is_outlier` dùng z-score toàn kỳ nên dồn ngoại lai về "
            "2010–2014 và bỏ sót các cú sốc gần đây (FTX 11/2022).\n"
            "- Vốn hoá trải 6 bậc độ lớn ⇒ biểu đồ vốn hoá/giá nhiều coin phải "
            "để thang log."
        )


# --- Bộ khung -----------------------------------------------------------------
# Sidebar vẽ TRƯỚC st.navigation để mọi trang con đều có sẵn st.session_state["bo_loc"].
ve_sidebar()

# `url_path` đặt tay cho từng trang: đường dẫn ổn định, đọc được, dùng lại được
# trong báo cáo và video demo (localhost:8501/ban-do). Nếu để Streamlit tự suy ra
# từ tên file thì đường dẫn phụ thuộc cách đặt tên file, đổi tên file là link cũ
# trong báo cáo chết theo.
trang = st.navigation(
    [
        st.Page(trang_chu, title="Trang chủ", icon=":material/home:", default=True),
        st.Page(
            "pages/1_Tong_quan.py",
            title="Tổng quan thị trường",
            icon=":material/show_chart:",
            url_path="tong-quan",
        ),
        st.Page(
            "pages/2_Thi_truong.py",
            title="Cấu trúc thị trường",
            icon=":material/donut_small:",
            url_path="thi-truong",
        ),
        st.Page(
            "pages/3_Vi_mo.py",
            title="Tương quan vĩ mô",
            icon=":material/scatter_plot:",
            url_path="vi-mo",
        ),
        st.Page(
            "pages/4_Ban_do.py",
            title="Bản đồ lạm phát",
            icon=":material/public:",
            url_path="ban-do",
        ),
        st.Page(
            "pages/5_Du_bao.py",
            title="Mô hình dự báo",
            icon=":material/analytics:",
            url_path="du-bao",
        ),
    ]
)
trang.run()
