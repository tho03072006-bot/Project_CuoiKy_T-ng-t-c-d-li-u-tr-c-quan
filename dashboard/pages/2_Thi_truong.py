# -*- coding: utf-8 -*-
"""Trang Cấu trúc thị trường - 4 loại biểu đồ chính và dải giá quan sát + một cặp cross-filtering.

Các loại biểu đồ trên trang này (theo yêu cầu "≥ 8 loại" của barem):
  Hình 2 - Line + dải biến động  (thay cho candlestick)
  Hình 3 - Bar                    (top coin theo lợi suất)   <- NGUỒN cross-filter
  Hình 4 - Box plot               (phân phối biến động)      <- ĐÍCH cross-filter
  Hình 5 - Treemap                (thị phần vốn hoá)
  Hình 6 - Stacked area           (thị phần BTC theo thời gian)

Cross-filtering: bấm/quét chọn cột trên Hình 3, Hình 2 và Hình 4 lọc lại theo
đúng những coin vừa chọn. Lựa chọn lưu trong st.session_state["chon_coin_bar"]
và được đặt lại khi thay bộ lọc để không dùng nhầm vùng chọn cũ.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_layer as dl
from style import C1_BLUE, GRID, dinh_dang_tien, so_viet, tieu_de, ve

SO_COIN_TOP = 15

bo_loc = st.session_state["bo_loc"]

# Xóa lựa chọn ngay cả khi bộ lọc mới rỗng và trang dừng trước khi vẽ biểu đồ.
dau_loc = repr(bo_loc)
if st.session_state.get("thi_truong_dau_loc") != dau_loc:
    st.session_state["thi_truong_dau_loc"] = dau_loc
    st.session_state["chon_coin_bar"] = []
    st.session_state["thi_truong_lan_chon"] = st.session_state.get("thi_truong_lan_chon", 0) + 1

# Hai khung dữ liệu khác nhau, cố ý:
#   df       - áp đủ 4 tầng lọc, dùng cho những hình mô tả đúng coin đã chọn.
#   df_nhom  - BỎ tầng 3 (coin cụ thể), dùng cho bảng xếp hạng. Nếu xếp hạng mà
#              cũng lọc theo tầng 3 thì người dùng chọn 2 coin sẽ ra bảng xếp
#              hạng 2 dòng - vô nghĩa. Thay vào đó xếp hạng cả nhóm rồi TÔ SÁNG
#              những coin đang chọn.
df = dl.loc_du_lieu(**bo_loc)
df_nhom = dl.loc_du_lieu(
    bo_loc["tu_ngay"],
    bo_loc["den_ngay"],
    None,
    bo_loc["nhom_coin"],
    bo_loc["von_hoa_toi_thieu"],
)

st.title("Cấu trúc thị trường")
st.caption(
    f"Khoảng lọc: {bo_loc['tu_ngay']:%d/%m/%Y} → {bo_loc['den_ngay']:%d/%m/%Y} · "
    f"Nhóm: {bo_loc['nhom_coin']} · Vốn hoá tối thiểu: "
    f"{dinh_dang_tien(bo_loc['von_hoa_toi_thieu']) if bo_loc['von_hoa_toi_thieu'] else 'không giới hạn'}"
)

if df_nhom.empty:
    st.warning(
        "Bốn tầng lọc hiện tại không chừa lại dòng nào. Hãy hạ ngưỡng vốn hoá "
        "hoặc nới khoảng ngày.",
        icon=":material/filter_alt_off:",
    )
    st.stop()


# =============================================================================
# Bảng xếp hạng lợi suất - nguyên liệu chung cho Hình 3
# =============================================================================
def xep_hang_loi_suat(khung: pd.DataFrame) -> pd.DataFrame:
    """Lợi suất của từng coin từ phiên đầu đến phiên cuối trong khoảng lọc.

    Dùng giá đầu/cuối của CHÍNH coin đó trong khung, không dùng giá của ngày
    biên chung: nhiều coin ra đời muộn, ép chúng về cùng ngày đầu sẽ ra NaN.
    """
    dau_cuoi = (
        khung.sort_values("date")
        .groupby("ticker")
        .agg(
            gia_dau=("price_usd", "first"),
            gia_cuoi=("price_usd", "last"),
            von_hoa=("market_cap_usd", "last"),
            nhom=("category", "last"),
            so_phien=("price_usd", "size"),
        )
    )
    dau_cuoi = dau_cuoi[(dau_cuoi["gia_dau"] > 0) & (dau_cuoi["so_phien"] >= 2)]
    dau_cuoi["loi_suat"] = (dau_cuoi["gia_cuoi"] / dau_cuoi["gia_dau"] - 1) * 100
    return dau_cuoi.sort_values("loi_suat", ascending=False).reset_index()


xep_hang = xep_hang_loi_suat(df_nhom)

if xep_hang.empty:
    st.info("Cần ít nhất hai phiên có giá cho mỗi coin để xếp hạng lợi suất. Hãy mở rộng khoảng ngày.")
    st.stop()

def bo_chon_coin() -> None:
    """Đổi khóa chart vì trạng thái selection do Streamlit quản lý là chỉ đọc."""
    st.session_state["chon_coin_bar"] = []
    st.session_state["thi_truong_lan_chon"] += 1


khoa_xep_hang = f"bieu_do_xep_hang_{st.session_state['thi_truong_lan_chon']}"


def nhan_chon_coin() -> None:
    """Callback chạy trước trang để màu cột và hai chart đích cùng một lựa chọn."""
    diem = st.session_state.get(khoa_xep_hang, {}).get("selection", {}).get("points", [])
    hop_le = set(xep_hang.head(SO_COIN_TOP)["ticker"])
    st.session_state["chon_coin_bar"] = list(dict.fromkeys(
        p["y"] for p in diem if p.get("y") in hop_le
    ))

# Lựa chọn cross-filter hiện hành. Mặc định = tầng 3 của sidebar; khi người dùng
# quét chọn trên Hình 3 thì giá trị này bị ghi đè.
coin_sidebar = (
    xep_hang["ticker"].tolist()
    if bo_loc["danh_sach_coin"] is None else bo_loc["danh_sach_coin"]
)
coin_dang_chon = st.session_state.get("chon_coin_bar") or coin_sidebar
coin_dang_chon = [c for c in coin_dang_chon if c in set(xep_hang["ticker"])]


# =============================================================================
# HÌNH 3 - Bar: top coin theo lợi suất  (NGUỒN cross-filter)
# =============================================================================
with st.container(border=True):
    st.markdown(f"**Hình 3 — Xếp hạng lợi suất (bar chart)** · nguồn cross-filter")

    top = xep_hang.head(SO_COIN_TOP).copy()
    top["duoc_chon"] = np.where(
        top["ticker"].isin(coin_dang_chon), "Đang chọn", "Còn lại"
    )
    # Chuỗi tiền đã rút gọn sẵn cho tooltip: Plotly không biết viết "1,2 tỷ USD",
    # nên phải tính trước rồi đưa vào customdata.
    top["von_hoa_txt"] = top["von_hoa"].map(dinh_dang_tien)

    dan_dau = top.iloc[0]
    so_tang = int((xep_hang["loi_suat"] > 0).sum())
    hinh3 = px.bar(
        top.sort_values("loi_suat"),
        x="loi_suat",
        y="ticker",
        orientation="h",
        color="duoc_chon",
        # Hai màu cho hai NHÓM (đang chọn / còn lại) - đây là tô màu theo nhóm,
        # không phải tô đậm theo giá trị, nên không phạm lỗi bị trừ điểm.
        color_discrete_map={"Đang chọn": C1_BLUE, "Còn lại": GRID},
        custom_data=["von_hoa_txt", "nhom", "so_phien"],
        labels={"loi_suat": "Lợi suất (%)", "ticker": "", "duoc_chon": ""},
    )
    hinh3.update_traces(
        hovertemplate=(
            "<b>%{y}</b> · %{customdata[1]}<br>"
            "Lợi suất cả kỳ: <b>%{x:+,.1f}%</b><br>"
            "Vốn hoá cuối kỳ: %{customdata[0]}<br>"
            "Số phiên có giá: %{customdata[2]:,.0f}"
            "<extra></extra>"
        ),
        marker_line_width=0,
    )
    hinh3.update_layout(
        title=tieu_de(
            f"{dan_dau['ticker']} dẫn đầu {so_viet(dan_dau['loi_suat'], 1)}%, "
            f"{so_tang}/{len(xep_hang)} coin tăng giá",
            f"Xếp hạng {min(SO_COIN_TOP, len(xep_hang))} coin đầu bảng trong khoảng lọc. "
            "Bấm hoặc quét chọn cột để lọc Hình 2 và 4; ngày đầu/cuối theo lịch sử từng coin.",
        ),
        height=max(360, 26 * len(top) + 190),
        hovermode="closest",  # bar ngang: gộp theo trục x là vô nghĩa
        xaxis=dict(ticksuffix="%"),
        legend=dict(y=-0.12),
    )

    # on_select="rerun": Streamlit chạy lại script mỗi khi vùng chọn đổi và trả
    # về các điểm đang chọn trong `event.selection`.
    su_kien = ve(
        hinh3,
        key=khoa_xep_hang,
        on_select=nhan_chon_coin,
        selection_mode=("points", "box"),
    )

    if st.session_state.get("chon_coin_bar"):
        st.info(
            "Đang lọc chéo theo: **"
            + ", ".join(st.session_state["chon_coin_bar"])
            + "** — lựa chọn này thay bộ lọc coin cụ thể cho Hình 2 và 4.",
            icon=":material/filter_alt:",
        )
        st.button("Bỏ chọn biểu đồ", key="bo_chon_bar", on_click=bo_chon_coin)

# Danh sách coin thực sự dùng cho hai hình bên dưới, sau khi đã tính cross-filter.
coin_hieu_luc = st.session_state.get("chon_coin_bar")
df_lien_ket = df_nhom[df_nhom["ticker"].isin(coin_hieu_luc)] if coin_hieu_luc else df
coin_hieu_luc = sorted(df_lien_ket["ticker"].unique())


# =============================================================================
# HÌNH 2 - Line + dải biến động  (ĐÍCH cross-filter)
# =============================================================================
trai, phai = st.columns(2)

with trai:
    with st.container(border=True):
        st.markdown("**Hình 2 — Giá kèm dải biến động (line + band)**")
        st.caption(
            "Dải phân vị 10–90% của giá trong 30 phiên gần nhất mô tả giá đã quan sát. "
            "Đây không phải khoảng tin cậy, dự báo hay giá open/high/low. "
            "Cửa sổ dùng cả các phiên trước khoảng lọc để tránh dải đứt ở đầu hình."
        )

        ds_coin = sorted(df_lien_ket["ticker"].unique())
        if not ds_coin:
            st.warning("Không còn coin nào sau khi lọc.", icon=":material/warning:")
        else:
            if st.session_state.get("w_coin_dai_bien_dong") not in ds_coin:
                st.session_state["w_coin_dai_bien_dong"] = ds_coin[0]
            coin = st.selectbox(
                "Coin hiển thị", ds_coin, key="w_coin_dai_bien_dong",
                help="Theo bộ lọc sidebar; vùng chọn Hình 3 thay lựa chọn coin khi đang lọc chéo.",
            )
            # Phân vị thực nghiệm không đòi hỏi giả định lợi suất có phân phối chuẩn.
            day_du = dl.nap_crypto_daily()
            day_du = day_du[day_du["ticker"] == coin].sort_values("date").copy()
            cua_so = day_du["price_usd"].rolling(30, min_periods=10)
            day_du["duoi"] = cua_so.quantile(0.1)
            day_du["tren"] = cua_so.quantile(0.9)
            ngay_hien = df_lien_ket.loc[df_lien_ket["ticker"] == coin, "date"]
            mot = day_du[day_du["date"].isin(ngay_hien)].copy()
            hinh2 = go.Figure()
            hinh2.add_trace(go.Scatter(
                x=mot["date"], y=mot["duoi"], name="Phân vị 10%",
                line=dict(width=0), showlegend=False, hoverinfo="skip",
            ))
            hinh2.add_trace(go.Scatter(
                x=mot["date"], y=mot["tren"], name="Dải giá 10–90% (30 phiên)",
                line=dict(width=0), fill="tonexty", fillcolor="rgba(42,120,214,0.16)",
                customdata=mot[["duoi"]],
                hovertemplate="Phân vị 10–90%: %{customdata[0]:,.4f}–%{y:,.4f} USD<extra></extra>",
            ))
            hinh2.add_trace(go.Scatter(
                x=mot["date"], y=mot["price_usd"], name=f"Giá {coin}",
                line=dict(color=C1_BLUE, width=1.6),
                mode="lines+markers" if len(mot) == 1 else "lines",
                hovertemplate="Giá: <b>%{y:,.4f} USD</b><extra></extra>",
            ))
            do_rong = ((mot["tren"] / mot["duoi"] - 1) * 100).dropna()
            ket_luan = (
                f"{coin}: độ rộng dải giá trung vị {so_viet(do_rong.median(), 1)}%"
                if len(do_rong) else f"{coin}: chưa đủ phiên để tính dải phân vị"
            )
            hinh2.update_layout(
                title=tieu_de(ket_luan, "Độ rộng = phân vị 90% / phân vị 10% − 1; cần ít nhất 10 phiên."),
                height=420, yaxis=dict(type="log", title="Giá (USD)"),
                xaxis=dict(hoverformat="%d/%m/%Y", title=""), legend=dict(y=-0.14),
            )
            ve(hinh2, key="bieu_do_dai")


# =============================================================================
# HÌNH 4 - Box plot: phân phối biến động 30 ngày theo năm  (ĐÍCH cross-filter)
# =============================================================================
with phai:
    with st.container(border=True):
        st.markdown("**Hình 4 — Phân phối biến động theo năm (box plot)**")
        st.caption(
            "Hộp tóm tắt trung vị và tứ phân vị của biến động lịch sử 30 ngày đã quy năm. "
            "Các cửa sổ ngày chồng lấn, nên đây là thống kê mô tả; không phải "
            "các quan sát độc lập hay ước lượng xác suất thua lỗ."
        )

        hop = df_lien_ket.dropna(subset=["volatility_30d"]).copy()
        if hop.empty:
            st.warning("Không đủ dữ liệu biến động.", icon=":material/warning:")
        else:
            hop["nam"] = hop["date"].dt.year.astype(str)
            theo_nam = hop.groupby("nam")["volatility_30d"].median()
            nam_cao, nam_thap = theo_nam.idxmax(), theo_nam.idxmin()

            hinh4 = px.box(
                hop.sort_values("nam"),
                x="nam",
                y="volatility_30d",
                labels={"nam": "", "volatility_30d": "Biến động quy năm (%)"},
                # points=False: 6.000 điểm ngoại lai vẽ chồng lên nhau sẽ che mất
                # chính cái hộp cần đọc.
                points=False,
                color_discrete_sequence=[C1_BLUE],
            )
            # Tooltip mặc định của box trace hiển thị đúng median/quartiles/whiskers;
            # các biến %{median} trong hovertemplate không được Plotly giải mã ổn định.
            hinh4.update_traces(marker=dict(color=C1_BLUE), line=dict(width=1.2))
            hinh4.update_layout(
                title=tieu_de(
                    f"Trung vị cao nhất {nam_cao}: {so_viet(theo_nam.max(), 0)}%; "
                    f"thấp nhất {nam_thap}: {so_viet(theo_nam.min(), 0)}%",
                    f"{', '.join(coin_hieu_luc) if coin_hieu_luc else 'Toàn bộ coin trong nhóm'}"
                    f" · {so_viet(len(hop), 0)} quan sát coin-ngày; năm đầu/cuối có thể chưa đủ năm.",
                ),
                height=420,
                hovermode="closest",
                showlegend=False,
                yaxis=dict(ticksuffix="%"),
            )
            ve(hinh4, key="bieu_do_hop")


# =============================================================================
# HÌNH 5 - Treemap: thị phần vốn hoá theo nhóm coin
# =============================================================================
trai2, phai2 = st.columns(2)

with trai2:
    with st.container(border=True):
        st.markdown("**Hình 5 — Thị phần vốn hoá (treemap)**")
        st.caption(
            "Bảng vốn hoá gồm cả coin không có lịch sử giá. Áp dụng ngày, nhóm và ngưỡng "
            "vốn hoá; không áp dụng coin cụ thể hoặc vùng chọn Hình 3. Diện tích ô giữ "
            "tỷ lệ vốn hoá thực để đọc thị phần, không log diện tích."
        )
        thi_truong = dl.nap_market_daily()
        trong_khoang = thi_truong[thi_truong["date"].between(
            pd.Timestamp(bo_loc["tu_ngay"]), pd.Timestamp(bo_loc["den_ngay"])
        )]
        if trong_khoang.empty:
            st.warning("Khoảng ngày không có dữ liệu vốn hoá.", icon=":material/warning:")
        else:
            ngay_chot = trong_khoang["date"].max()
            anh = (
                trong_khoang[trong_khoang["date"] == ngay_chot]
                .merge(dl.nap_dim_coin()[["ticker", "category"]], on="ticker", how="left")
                .dropna(subset=["market_cap_usd", "category"])
            )
            if bo_loc["nhom_coin"] != dl.NHOM_TAT_CA:
                anh = anh[anh["category"] == bo_loc["nhom_coin"]]
            anh = anh[anh["market_cap_usd"] >= max(bo_loc["von_hoa_toi_thieu"], 1)]
            if anh.empty:
                st.info(f"Không có coin đủ ngưỡng vốn hoá tại ngày chốt {ngay_chot:%d/%m/%Y}.")
            else:
                tong = anh["market_cap_usd"].sum()
                theo_nhom = anh.groupby("category")["market_cap_usd"].sum().sort_values()
                hinh5 = px.treemap(
                    anh, path=[px.Constant("Phạm vi đang xem"), "category", "ticker"],
                    values="market_cap_usd", color="category",
                )
                # Tính tooltip cho cả nút cha; customdata chuỗi từ bảng gốc không cộng được.
                for trace in hinh5.data:
                    trace.customdata = [[dinh_dang_tien(v)] for v in trace.values]
                hinh5.update_traces(
                    marker=dict(cornerradius=3, line=dict(color="#fcfcfb", width=1.5)),
                    texttemplate="<b>%{label}</b><br>%{percentRoot:.1%}",
                    hovertemplate=(
                        "<b>%{label}</b><br>Vốn hoá: %{customdata[0]}<br>"
                        "Tỷ trọng trong phạm vi: %{percentRoot:.1%}<br>"
                        "Tỷ trọng trong nhóm cha: %{percentParent:.1%}<extra></extra>"
                    ), tiling=dict(pad=2),
                )
                hinh5.update_layout(
                    title=tieu_de(
                        f"Nhóm {theo_nhom.index[-1]} chiếm {so_viet(100 * theo_nhom.iloc[-1] / tong, 1)}% phạm vi",
                        f"Ngày {ngay_chot:%d/%m/%Y} · {len(anh)} coin · tổng {dinh_dang_tien(tong)}. Bấm ô để đi sâu.",
                    ), height=440, margin=dict(l=12, r=12, t=100, b=24),
                )
                ve(hinh5, key="bieu_do_treemap")


# =============================================================================
# HÌNH 6 - Stacked area: thị phần BTC vs phần còn lại
# =============================================================================
with phai2:
    with st.container(border=True):
        st.markdown("**Hình 6 — Thị phần BTC theo thời gian (stacked area)**")
        st.caption(
            "Chỉ số toàn thị trường, chỉ áp dụng khoảng ngày. Hai dải cộng thành 100%; "
            "tháng đầu/cuối dùng các ngày có dữ liệu trong khoảng lọc."
        )

        thi_phan = (
            dl.loc_du_lieu(bo_loc["tu_ngay"], bo_loc["den_ngay"], ["BTC"])[["date", "btc_dominance_pct"]]
            .dropna(subset=["btc_dominance_pct"])
            .drop_duplicates("date")
            .sort_values("date")
            .set_index("date")
        )
        if thi_phan.empty:
            st.warning("Không có dữ liệu thị phần.", icon=":material/warning:")
        else:
            # Gộp về tháng: vẽ 3.000 điểm ngày cho một tỷ lệ đổi chậm chỉ làm hình
            # nặng thêm mà không thêm thông tin nào.
            thang = thi_phan["btc_dominance_pct"].resample("ME").mean().dropna()
            khung = pd.DataFrame(
                {
                    "thang": thang.index,
                    "Bitcoin": thang.to_numpy(),
                    "Các coin còn lại": 100 - thang.to_numpy(),
                }
            ).melt(id_vars="thang", var_name="Phần", value_name="thi_phan")

            hinh6 = px.area(
                khung,
                x="thang",
                y="thi_phan",
                color="Phần",
                color_discrete_map={
                    "Bitcoin": C1_BLUE,
                    "Các coin còn lại": "#cde2fb",
                },
                labels={"thang": "", "thi_phan": "Thị phần (%)"},
            )
            hinh6.update_traces(
                line=dict(width=0.8),
                hovertemplate="%{y:,.1f}%<extra></extra>",
            )
            hinh6.update_layout(
                title=tieu_de(
                    f"Thị phần BTC đi từ {so_viet(thang.iloc[0], 0)}% "
                    f"{'lên' if thang.iloc[-1] >= thang.iloc[0] else 'xuống'} {so_viet(thang.iloc[-1], 0)}%",
                    f"Trung bình tháng, {thang.index[0]:%m/%Y}–{thang.index[-1]:%m/%Y}. "
                    "Tỷ trọng vốn hoá không đo trực tiếp dòng tiền vào/ra.",
                ),
                height=440,
                yaxis=dict(range=[0, 100], ticksuffix="%"),
                xaxis=dict(hoverformat="%m/%Y", title=""),
                legend=dict(y=-0.14),
            )
            ve(hinh6, key="bieu_do_area")
