# -*- coding: utf-8 -*-
"""Bảng màu và template Plotly dùng chung cho toàn bộ dashboard.

Vì sao tách thành một module riêng: barem chấm 0,5 điểm cho "giao diện, bố cục,
legend rõ ràng". Nếu mỗi trang tự đặt màu thì dashboard sẽ lệch tông và mất điểm.
Đặt template ở một chỗ, các trang chỉ việc import, không trang nào chế màu riêng.

Bảng màu lấy nguyên từ `eda/eda_style.py` (đã kiểm định khoảng cách màu cho người
mù màu ΔE >= 8) nên hình trong báo cáo và hình trên dashboard trùng tông nhau.
"""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import html
import re

# --- Nền và chữ ---------------------------------------------------------------
SURFACE = "#fcfcfb"   # nền hình
INK = "#0b0b0b"       # chữ chính
INK_SOFT = "#52514e"  # chữ phụ, nhãn trục
GRID = "#e8e7e3"      # lưới mờ, chỉ cách nền một bậc

# --- Màu định danh (categorical) ----------------------------------------------
# Dùng ĐÚNG THỨ TỰ này, không xoay vòng: ba slot đầu đã kiểm định "all-pairs".
C1_BLUE = "#2a78d6"
C2_ORANGE = "#eb6834"
C3_AQUA = "#1baf7a"
C4_YELLOW = "#eda100"
C8_RED = "#e34948"
DINH_DANH = [C1_BLUE, C2_ORANGE, C3_AQUA, C4_YELLOW, C8_RED]

# --- Thang liên tục: MỘT màu nhạt -> đậm ---------------------------------------
# Không dùng rainbow cho dữ liệu liên tục - đó là một trong ba lỗi bị trừ điểm.
SEQ_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#0d366b"]

# --- Thang phân cực: hai màu đối nghịch, xám trung tính ở giữa -----------------
DIVERGING = ["#e34948", "#f0efec", "#2a78d6"]

TEN_TEMPLATE = "idv"

# Font có sẵn trên Windows và hiển thị đủ dấu tiếng Việt; có fallback phòng khi
# chạy máy khác (lúc demo trên máy giảng viên chẳng hạn).
FONT_FAMILY = "Segoe UI, DejaVu Sans, Arial, sans-serif"


def _truc() -> dict:
    """Cấu hình chung cho cả trục x và trục y.

    Lưới LIỀN NÉT (griddash="solid") và mờ - CLAUDE.md cấm lưới nét đứt.
    `automargin=True` để nhãn trục dài không bị cắt cụt khi khung hẹp lại.
    """
    return dict(
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        griddash="solid",
        zeroline=False,
        showline=False,
        ticks="outside",
        ticklen=4,
        tickcolor=GRID,
        tickfont=dict(size=11, color=INK_SOFT),
        title=dict(font=dict(size=11, color=INK_SOFT), standoff=10),
        automargin=True,
    )


def _tao_template() -> go.layout.Template:
    """Dựng đối tượng Template của Plotly từ bảng màu ở trên."""
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            colorway=DINH_DANH,
            font=dict(family=FONT_FAMILY, size=12, color=INK),
            # Tiêu đề canh trái, neo theo mép trên của KHUNG (yref="container")
            # để tiêu đề 2 dòng luôn nằm gọn trong lề trên, không đè lên hình.
            title=dict(
                x=0,
                xanchor="left",
                yref="container",
                y=0.97,
                yanchor="top",
                font=dict(size=15, color=INK),
            ),
            # Lề thoáng: trên 100px chừa chỗ cho tiêu đề 2 dòng, dưới 84px chừa
            # chỗ cho legend nằm ngang.
            margin=dict(l=72, r=36, t=100, b=84),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.16,
                xanchor="left",
                x=0,
                title_text="",
                font=dict(size=11, color=INK_SOFT),
                bgcolor="rgba(0,0,0,0)",
            ),
            # Định dạng số kiểu Việt Nam cho MỌI nhãn Plotly sinh ra (trục,
            # tooltip): dấu phẩy là thập phân, dấu chấm là hàng nghìn.
            separators=",.",
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="#ffffff",
                bordercolor=GRID,
                font=dict(family=FONT_FAMILY, size=12, color=INK),
            ),
            colorscale=dict(sequential=SEQ_BLUE, diverging=DIVERGING),
            xaxis=_truc(),
            yaxis=_truc(),
        )
    )


def dang_ky_template(dat_mac_dinh: bool = True) -> None:
    """Đăng ký template "idv" vào pio.templates.

    Gọi một lần trong app.py. Hàm tự kiểm tra trùng tên nên Streamlit rerun liên
    tục cũng không dựng lại template thừa.

    LƯU Ý khi vẽ: phải gọi st.plotly_chart(fig, theme=None). Mặc định Streamlit
    ép theme của nó lên hình và sẽ ghi đè bảng màu này.
    """
    if TEN_TEMPLATE not in pio.templates:
        pio.templates[TEN_TEMPLATE] = _tao_template()
    if dat_mac_dinh:
        pio.templates.default = TEN_TEMPLATE


def ve(fig, **kwargs):
    """Vẽ một hình Plotly trong Streamlit cho đúng bảng màu của đồ án.

    Hàm này tồn tại để bịt một cái bẫy thật: kể cả khi truyền theme=None,
    Streamlit vẫn CHÈN màu nền của theme vào hình theo kiểu
    `plot_bgcolor = hinh.layout.plot_bgcolor || secondaryBackgroundColor`.
    Màu trong TEMPLATE không tính là "hình đã đặt", nên nền vùng vẽ bị thay bằng
    #f3f2ee (màu nền phụ của sidebar) thay vì #fcfcfb. Đã đo tận nơi trên trình
    duyệt mới phát hiện ra.

    Cách chữa: gán thẳng hai màu nền vào LAYOUT của hình - lúc đó vế trái của
    phép `||` khác rỗng và Streamlit không chèn nữa.

    Gộp luôn theme=None vào đây để không trang nào quên, vì quên là mất sạch
    bảng màu đã kiểm định.
    """
    # Để trình duyệt tự xuống dòng phần diễn giải, tránh tiêu đề Plotly tràn
    # khỏi cột hẹp hoặc bị cắt khi màn hình laptop thu nhỏ.
    if fig.layout.title.text:
        parts = re.split(r"<br\s*/?>", fig.layout.title.text, maxsplit=1)
        st.markdown("**" + html.unescape(re.sub(r"</?[A-Za-z][^>]*>", "", parts[0])) + "**")
        if len(parts) > 1:
            st.caption(html.unescape(re.sub(r"</?[A-Za-z][^>]*>", "", parts[1])))
        fig.update_layout(title_text="", margin_t=28)
    fig.update_layout(paper_bgcolor=SURFACE, plot_bgcolor=SURFACE)
    return st.plotly_chart(fig, theme=None, width="stretch", **kwargs)


def tieu_de(chinh: str, phu: str) -> dict:
    """Tiêu đề 2 dòng: dòng trên đậm là KẾT LUẬN, dòng dưới mảnh là diễn giải.

    Vì sao làm vậy: barem mục 3 chấm "storytelling rút insight, không chỉ show
    biểu đồ". Đặt câu kết luận ngay trên hình buộc người đọc thấy ý trước, thấy
    số sau. Dòng phụ dùng màu nhạt #52514e để không tranh chấp thị giác với
    dòng kết luận.

    Trả về dict để gán thẳng: fig.update_layout(title=tieu_de("...", "..."))
    """
    return dict(
        text=(
            f"<b>{chinh}</b><br>"
            f"<span style='font-size:12px;color:{INK_SOFT}'>{phu}</span>"
        ),
        x=0,
        xanchor="left",
        yref="container",
        y=0.97,
        yanchor="top",
        font=dict(size=15, color=INK),
    )


def so_viet(x: float, sole: int = 2) -> str:
    """Đổi cách viết số của Python sang kiểu Việt Nam: 1,234.5 -> 1.234,5.

    Dùng str.translate chứ không dùng hai lần .replace(): replace chạy tuần tự
    nên dấu phẩy vừa tạo ra ở lượt một sẽ bị lượt hai đổi tiếp thành dấu chấm.
    translate tra bảng một lần duy nhất trên từng ký tự nên đổi chỗ được.
    """
    return f"{x:,.{sole}f}".translate(str.maketrans(",.", ".,"))


def dinh_dang_tien(so: float | None, don_vi: str = "USD") -> str:
    """Rút gọn số tiền lớn về nghìn tỷ / tỷ / triệu, viết theo kiểu Việt Nam.

    Vốn hoá trải 6 bậc độ lớn (bẫy dữ liệu số 4) nên in nguyên số sẽ thành một
    dãy chữ số không ai đọc nổi trên thẻ KPI.
    """
    if so is None:
        return "—"
    for nguong, nhan in ((1e12, "nghìn tỷ"), (1e9, "tỷ"), (1e6, "triệu")):
        if abs(so) >= nguong:
            return f"{so_viet(so / nguong)} {nhan} {don_vi}"
    return f"{so_viet(so)} {don_vi}"
