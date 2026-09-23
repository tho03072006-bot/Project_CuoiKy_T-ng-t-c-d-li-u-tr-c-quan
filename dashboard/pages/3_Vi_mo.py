# -*- coding: utf-8 -*-
"""Trang Tương quan vĩ mô - scatter + heatmap, có cross-filtering theo tháng.

  Hình 7 - Scatter + đường hồi quy  <- NGUỒN cross-filter
  Hình 8 - Heatmap ma trận tương quan <- ĐÍCH cross-filter

Quét chọn một vùng trên Hình 7 (chế độ box) là Hình 8 tính lại ma trận tương
quan CHỈ trên những tháng nằm trong vùng đó. Nhờ vậy trả lời được câu hỏi kiểu
"trong các tháng BTC giảm mạnh thì quan hệ với vĩ mô có khác không".

TOÀN BỘ trang này chạy trên bảng THÁNG (dl.bang_thang), không đụng tới dữ liệu
ngày - xem bẫy dữ liệu số 2 trong CLAUDE.md.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

import data_layer as dl
from style import C1_BLUE, C8_RED, DIVERGING, so_viet, tieu_de, ve

# Ngưỡng ý nghĩa thống kê quy ước.
ALPHA = 0.05

bo_loc = st.session_state["bo_loc"]

st.title("Tương quan với kinh tế vĩ mô")
st.caption(
    "Tính trên **tháng lịch hoàn tất, không chồng lấn** của BTC/ETH. "
    "Chỉ khoảng ngày ở thanh bên áp dụng cho trang này; tương quan không chứng minh nhân quả."
)

bang = dl.bang_thang()

# Chỉ lấy tháng nằm trọn trong bộ lọc; không dùng dữ liệu sau ngày kết thúc.
tu = pd.Timestamp(bo_loc["tu_ngay"])
den = pd.Timestamp(bo_loc["den_ngay"])
dau_thang = bang["thang"].dt.to_period("M").dt.to_timestamp()
bang = bang[(dau_thang >= tu) & (bang["thang"] <= den)].copy()


def bo_vung_chon() -> None:
    """Đổi khóa biểu đồ để xóa cả selection phía trình duyệt."""
    st.session_state["chon_thang_scatter"] = []
    st.session_state["chon_scatter_epoch"] = st.session_state.get("chon_scatter_epoch", 0) + 1


pham_vi = (str(tu), str(den))
if st.session_state.get("chon_scatter_pham_vi") != pham_vi:
    bo_vung_chon()
    st.session_state["chon_scatter_pham_vi"] = pham_vi

if len(bang.dropna(subset=["btc_ret"])) < 10:
    st.warning(
        "Khoảng ngày đang chọn chưa đủ 10 tháng để tính tương quan có nghĩa. "
        "Hãy nới khoảng ngày ở thanh bên.",
        icon=":material/warning:",
    )
    st.stop()

# Nhãn có dấu cho khẩu vị rủi ro.
bang["khau_vi"] = bang["risk_regime"].map(dl.NHAN_RISK_REGIME).fillna("Không rõ")
bang["nhan_thang"] = bang["thang"].dt.strftime("%m/%Y")


# =============================================================================
# HÌNH 7 - Scatter + đường hồi quy  (NGUỒN cross-filter)
# =============================================================================
with st.container(border=True):
    st.markdown("**Hình 7 — BTC và S&P 500 theo tháng (scatter)** · nguồn cross-filter")

    diem = bang.dropna(subset=["btc_ret", "sp500"]).copy()
    diem["btc_pct"] = diem["btc_ret"] * 100
    diem["sp_pct"] = diem["sp500"] * 100
    if len(diem) < 3 or diem["sp_pct"].nunique() < 2:
        st.warning("Chưa đủ dữ liệu S&P 500 có biến thiên để hồi quy trong khoảng này.")
        st.stop()

    # Hồi quy tuyến tính OLS. Tự tính bằng scipy thay vì dùng trendline="ols" của
    # Plotly Express vì trendline đó đòi statsmodels, mà môi trường demo chưa cài.
    hq = stats.linregress(diem["sp_pct"], diem["btc_pct"])
    x_line = np.linspace(diem["sp_pct"].min(), diem["sp_pct"].max(), 50)
    y_line = hq.intercept + hq.slope * x_line

    hinh7 = px.scatter(
        diem,
        x="sp_pct",
        y="btc_pct",
        color="khau_vi",
        # Đúng 3 màu cho 3 trạng thái - biến định danh, dùng màu định danh.
        color_discrete_map={
            "Risk-on (ưa rủi ro)": "#1baf7a",
            "Risk-off (né rủi ro)": C8_RED,
            "Trung tính": "#9a9894",
            "Không rõ": "#d6d4cf",
        },
        custom_data=["nhan_thang", "khau_vi"],
        labels={
            "sp_pct": "Lợi suất S&P 500 trong tháng (%)",
            "btc_pct": "Lợi suất BTC trong tháng (%)",
            "khau_vi": "",
        },
    )
    hinh7.update_traces(
        marker=dict(size=9, opacity=0.85, line=dict(width=0)),
        hovertemplate=(
            "<b>Tháng %{customdata[0]}</b> · %{customdata[1]}<br>"
            "BTC: %{y:+,.1f}%<br>"
            "S&P 500: %{x:+,.1f}%"
            "<extra></extra>"
        ),
    )
    hinh7.add_trace(
        go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            name="Đường hồi quy OLS",
            line=dict(color=C1_BLUE, width=2),
            hovertemplate="Đường hồi quy<extra></extra>",
        )
    )

    y_nghia = "có ý nghĩa thống kê" if hq.pvalue < ALPHA else "KHÔNG có ý nghĩa"
    hinh7.update_layout(
        title=tieu_de(
            f"Quan hệ BTC–S&P 500 {'dương' if hq.rvalue >= 0 else 'âm'} và {y_nghia}: r = {so_viet(hq.rvalue, 3)}",
            f"n = {len(diem)} tháng · p = {so_viet(hq.pvalue, 3)} · "
            f"R² = {so_viet(hq.rvalue ** 2, 3)} — tức S&P 500 chỉ giải thích được "
            f"{so_viet(100 * hq.rvalue ** 2, 1)}% biến thiên của BTC. "
            "Quét chọn một vùng để lọc Hình 8.",
        ),
        height=520,
        hovermode="closest",
        # dragmode mặc định của Plotly là "zoom"/"pan", lúc đó kéo chuột chỉ di
        # chuyển hình chứ không quét chọn, người dùng phải tự tìm nút Box Select
        # trong thanh công cụ mới chọn được. Đặt sẵn "select" để kéo là chọn.
        dragmode="select",
        xaxis=dict(ticksuffix="%", zeroline=True, zerolinecolor="#e8e7e3", zerolinewidth=1),
        yaxis=dict(ticksuffix="%", zeroline=True, zerolinecolor="#e8e7e3", zerolinewidth=1),
        legend=dict(y=-0.16),
    )

    su_kien = ve(
        hinh7,
        key=f"bieu_do_scatter_{st.session_state.get('chon_scatter_epoch', 0)}",
        on_select="rerun",
        selection_mode=("points", "box"),
    )

    # Mỗi điểm đang chọn trả về customdata; phần tử [0] là nhãn tháng "MM/YYYY".
    thang_chon = [
        d["customdata"][0]
        for d in su_kien.get("selection", {}).get("points", [])
        if d.get("customdata")
    ]
    # Bỏ trùng mà vẫn giữ thứ tự, phòng khi vùng chọn trùm lên cả đường hồi quy.
    thang_chon = list(dict.fromkeys(thang_chon))
    st.session_state["chon_thang_scatter"] = thang_chon


# =============================================================================
# HÌNH 8 - Heatmap ma trận tương quan  (ĐÍCH cross-filter)
# =============================================================================
thang_loc = st.session_state.get("chon_thang_scatter") or []
bang_hm = bang[bang["nhan_thang"].isin(thang_loc)] if thang_loc else bang

COT_HEATMAP = [
    "btc_ret",
    "eth_ret",
    "sp500",
    "gold_usd",
    "vix",
    "dxy",
    "us10y_yield",
    "real_rate",
    "cpi_yoy_pct",
]


def ma_tran_tuong_quan(khung: pd.DataFrame, cot: list[str]):
    """Ma trận hệ số Pearson kèm p-value và cỡ mẫu của TỪNG cặp.

    Không dùng thẳng `DataFrame.corr()` vì nó không trả về p-value, mà barem
    cần đánh dấu cặp nào có ý nghĩa thống kê. Mỗi cặp được dropna riêng
    (pairwise) chứ không dropna cả bảng: `us10y_yield` khuyết nhiều tháng, ép
    dropna toàn bảng sẽ kéo cỡ mẫu của MỌI cặp tụt theo cột yếu nhất đó.
    """
    n = len(cot)
    r = np.full((n, n), np.nan)
    p = np.full((n, n), np.nan)
    so_mau = np.zeros((n, n), dtype=int)

    for i in range(n):
        # Đường chéo tính riêng: `khung[[a, a]]` trả về DataFrame hai cột TRÙNG
        # TÊN, lúc đó `cap[a]` cho ra DataFrame chứ không phải Series và pandas
        # ném ValueError "truth value of a Series is ambiguous".
        cot_i = khung[cot[i]].dropna()
        so_mau[i, i] = len(cot_i)
        if len(cot_i) >= 3 and cot_i.nunique() > 1:
            r[i, i], p[i, i] = 1.0, 0.0

        # Chỉ chạy nửa trên rồi soi gương xuống nửa dưới: ma trận tương quan đối
        # xứng nên tính cả hai nửa là làm thừa gấp đôi số phép kiểm định.
        for j in range(i + 1, n):
            cap = khung[[cot[i], cot[j]]].dropna()
            so_mau[i, j] = so_mau[j, i] = len(cap)
            a, b = cap[cot[i]], cap[cot[j]]
            # pearsonr đòi ít nhất 3 điểm; phương sai bằng 0 thì hệ số không xác
            # định (chia cho 0) nên để NaN và ô sẽ hiện dấu "—".
            if len(cap) < 3 or a.std() == 0 or b.std() == 0:
                continue
            r[i, j], p[i, j] = stats.pearsonr(a, b)
            r[j, i], p[j, i] = r[i, j], p[i, j]

    return r, p, so_mau


with st.container(border=True):
    dau, nut = st.columns([4, 1], vertical_alignment="center")
    with dau:
        st.markdown("**Hình 8 — Ma trận tương quan (heatmap)** · đích cross-filter")
    with nut:
        if thang_loc:
            st.button(
                "Bỏ vùng chọn",
                icon=":material/close:",
                key="w_bo_chon_scatter",
                on_click=bo_vung_chon,
            )

    if len(bang_hm) < 3:
        st.warning(
            f"Vùng chọn chỉ có {len(bang_hm)} tháng — cần ít nhất 3 tháng mới "
            "tính được hệ số tương quan.",
            icon=":material/warning:",
        )
    else:
        r, p, so_mau = ma_tran_tuong_quan(bang_hm, COT_HEATMAP)
        n_bien = len(COT_HEATMAP)
        nhan = [dl.NHAN_NGAN[c] for c in COT_HEATMAP]      # trục: tên ngắn
        nhan_dai = [dl.NHAN_BIEN[c] for c in COT_HEATMAP]  # tooltip: tên đầy đủ

        # Chữ trong ô: hệ số + dấu * khi p < 0,05.
        chu = np.empty(r.shape, dtype=object)
        for i in range(n_bien):
            for j in range(n_bien):
                if np.isnan(r[i, j]):
                    chu[i, j] = "—"
                elif i == j:
                    # Đường chéo luôn bằng 1 theo định nghĩa, không phải một
                    # phát hiện thống kê, nên KHÔNG gắn dấu *.
                    chu[i, j] = "1,00"
                else:
                    sao = "*" if p[i, j] < ALPHA else ""
                    chu[i, j] = f"{so_viet(r[i, j], 2)}{sao}"

        # customdata dựng bằng list lồng nhau (không dùng np.dstack) để giữ
        # nguyên kiểu: dstack sẽ ép cả số lẫn chuỗi về một dtype chuỗi, lúc đó
        # định dạng ":,.3f" trong hovertemplate hỏng.
        du_lieu_o = [
            [
                [
                    None if np.isnan(p[i, j]) else float(p[i, j]),
                    int(so_mau[i, j]),
                    nhan_dai[i],
                    nhan_dai[j],
                ]
                for j in range(n_bien)
            ]
            for i in range(n_bien)
        ]

        hinh8 = go.Figure(
            go.Heatmap(
                z=r,
                x=nhan,
                y=nhan,
                # Thang PHÂN CỰC đỏ - xám - xanh, neo cứng ở [-1, 1] để màu của ô
                # không đổi nghĩa khi người dùng quét chọn vùng khác.
                colorscale=DIVERGING,
                zmid=0,
                zmin=-1,
                zmax=1,
                text=chu,
                texttemplate="%{text}",
                textfont=dict(size=11),
                customdata=du_lieu_o,
                hovertemplate=(
                    "<b>%{customdata[2]}</b><br>và <b>%{customdata[3]}</b><br>"
                    "Hệ số r = %{z:,.3f}<br>"
                    "p = %{customdata[0]:,.3f}<br>"
                    "Cỡ mẫu: %{customdata[1]:,.0f} tháng"
                    "<extra></extra>"
                ),
                colorbar=dict(
                    title=dict(text="r", side="right"),
                    thickness=12,
                    len=0.7,
                    tickvals=[-1, -0.5, 0, 0.5, 1],
                ),
            )
        )

        # Câu kết luận: đếm số cặp có ý nghĩa trong nửa trên ma trận.
        tren = np.triu_indices(n_bien, k=1)
        co_nghia = int(np.nansum(p[tren] < ALPHA))
        tong_cap = len(tren[0])
        # Cỡ mẫu khác nhau giữa các cặp vì dropna theo từng cặp. Nêu khoảng thay
        # vì nêu số dòng của bảng - số dòng luôn lớn hơn cỡ mẫu thực của mọi cặp
        # có dính cột lợi suất (tháng đầu tiên không tính được % thay đổi).
        n_min, n_max = int(so_mau[tren].min()), int(so_mau[tren].max())
        # Cặp vĩ mô mạnh nhất với BTC (bỏ chính nó và bỏ ETH vì ETH là crypto).
        hang_btc = pd.Series(r[0], index=COT_HEATMAP).drop(["btc_ret", "eth_ret"])
        hop_le = hang_btc.dropna()
        manh_nhat = hop_le.abs().idxmax() if not hop_le.empty else None
        mo_ta_manh = (
            f"biến vĩ mô liên hệ mạnh nhất với BTC là {dl.NHAN_BIEN[manh_nhat]} "
            f"(r = {so_viet(hang_btc[manh_nhat], 2)})"
            if manh_nhat else "chưa đủ biến thiên để so sánh với BTC"
        )

        co_mau = (
            f"cỡ mẫu {n_min}–{n_max} tháng"
            if n_min != n_max
            else f"cỡ mẫu {n_min} tháng"
        )
        pham_vi = (
            f"Tính trên vùng quét chọn ở Hình 7, {co_mau}"
            if thang_loc
            else f"Tính trên toàn khoảng lọc, {co_mau}"
        )
        hinh8.update_layout(
            title=tieu_de(
                f"{co_nghia}/{tong_cap} cặp có ý nghĩa thống kê; "
                + mo_ta_manh,
                f"Dấu * đánh dấu p < 0,05. {pham_vi}. "
                "Ô càng xanh = cùng chiều, càng đỏ = ngược chiều.",
            ),
            height=620,
            margin=dict(l=150, r=40, t=110, b=130),
            # tickmode="array" ép Plotly in ĐỦ 9 nhãn. Để mặc định thì khi hẹp
            # chỗ Plotly tự bỏ bớt nhãn mà không cảnh báo, người đọc không biết
            # cột mình đang nhìn là biến nào.
            xaxis=dict(
                tickmode="array",
                tickvals=nhan,
                ticktext=nhan,
                tickangle=-35,
                showgrid=False,
                ticks="",
            ),
            yaxis=dict(
                tickmode="array",
                tickvals=nhan,
                ticktext=nhan,
                autorange="reversed",
                showgrid=False,
                ticks="",
            ),
        )
        ve(hinh8, key="bieu_do_heatmap")

        if thang_loc:
            st.info(
                f"Đang tính trên {len(bang_hm)} tháng quét chọn từ Hình 7: "
                + ", ".join(thang_loc[:12])
                + ("…" if len(thang_loc) > 12 else ""),
                icon=":material/filter_alt:",
            )

        st.caption(
            "Cách gộp tháng: giá (BTC, ETH, S&P 500, vàng) → lợi suất % của giá "
            "cuối tháng; lãi suất, lạm phát và chỉ số USD → giữ nguyên mức cuối "
            "tháng; VIX → trung bình trong tháng. Dấu * dùng p-value danh nghĩa "
            "chưa hiệu chỉnh nhiều phép thử; kết quả sau quét chọn chỉ để khám phá. "
            "Tháng không chồng lấn vẫn có thể có tự tương quan theo thời gian."
        )

with st.container(border=True):
    st.markdown("**Phân phối lợi suất BTC theo tháng (histogram)** · cùng vùng chọn Hình 7")
    phan_phoi = bang_hm.dropna(subset=["btc_ret"]).assign(loi_suat_pct=lambda d: d["btc_ret"] * 100)
    if not phan_phoi.empty:
        fig_hist = px.histogram(phan_phoi, x="loi_suat_pct", nbins=20,
                                labels={"loi_suat_pct": "Lợi suất tháng (%)"})
        fig_hist.update_layout(height=340, yaxis_title="Số tháng", showlegend=False,
                               hovermode="closest")
        ve(fig_hist, key="phan_phoi_thang")
        st.caption(f"{len(phan_phoi)} tháng; trung vị {so_viet(phan_phoi['loi_suat_pct'].median(), 2)}%. "
                   "Tần suất quan sát mô tả mẫu đã chọn, không phải xác suất tương lai.")
