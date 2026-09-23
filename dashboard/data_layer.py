# -*- coding: utf-8 -*-
"""Tầng dữ liệu: nạp 7 bảng trong data/processed/, cache lại và lọc.

Vì sao tách riêng khỏi phần vẽ: Streamlit chạy lại TOÀN BỘ script mỗi lần người
dùng động vào một widget. Nếu đọc CSV ngay trong trang thì mỗi cú click là một
lần đọc 123.358 dòng. Bọc `@st.cache_data` ở đây nên đọc đúng một lần cho cả
phiên, các trang sau chỉ lọc trên dữ liệu đã nằm sẵn trong RAM.

Quy ước: hàm nạp trả về dữ liệu THÔ (không lọc). Lọc là việc rẻ nên đặt ngoài
cache - nếu cache cả bước lọc thì mỗi tổ hợp filter lại sinh một bản sao 44MB.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

# dashboard/data_layer.py -> lùi một cấp ra Project_CuoiKy/ rồi vào data/processed
THU_MUC_DU_LIEU = Path(__file__).resolve().parent.parent / "data" / "processed"

# Nhãn của lựa chọn "không lọc theo nhóm" trên sidebar.
NHOM_TAT_CA = "Tất cả"

# ----------------------------------------------------------------------------
# Cách gộp biến vĩ mô về tháng - BẪY DỮ LIỆU SỐ 2 (CLAUDE.md)
#
# Các biến vĩ mô gốc là dữ liệu THÁNG đã forward-fill sang ngày. Tính tương quan
# ở tần suất ngày, hay dùng cửa sổ trượt 30 ngày, đều thổi phồng hệ số (r = 0,37
# thay vì 0,22 đúng) vì các quan sát chồng lấn nhau 29/30. Bắt buộc gộp về tháng.
#
# Gộp thế nào thì tuỳ BẢN CHẤT của biến - ba nhóm dưới đây tái lập đúng từng con
# số trong bảng "Kết quả đã kiểm chứng" của CLAUDE.md (đã đối chiếu cả 7 dòng):
#   * BIEN_GIA : là mức giá -> lấy giá cuối tháng rồi tính % thay đổi.
#   * BIEN_MUC : vốn đã là tỷ lệ phần trăm (lãi suất, lạm phát) hoặc chỉ số ->
#                giữ nguyên MỨC cuối tháng. Tính % thay đổi của một lãi suất là
#                vô nghĩa: 0,1% lên 0,2% thành "+100%".
#   * BIEN_TB  : VIX nhảy rất mạnh theo ngày nên lấy TRUNG BÌNH trong tháng,
#                đúng thông lệ khi tóm tắt một chỉ số đo sợ hãi.
# ----------------------------------------------------------------------------
BIEN_GIA = ["sp500", "gold_usd", "brent_oil"]
BIEN_MUC = ["dxy", "real_rate", "cpi_yoy_pct", "us10y_yield"]
BIEN_TB = ["vix"]

# Nhãn tiếng Việt cho từng cột của bảng tháng, dùng chung cho scatter và heatmap.
NHAN_BIEN = {
    "btc_ret": "BTC (lợi suất tháng)",
    "eth_ret": "ETH (lợi suất tháng)",
    "sp500": "S&P 500 (lợi suất tháng)",
    "gold_usd": "Vàng (lợi suất tháng)",
    "brent_oil": "Dầu Brent (lợi suất tháng)",
    "dxy": "Chỉ số USD (mức)",
    "real_rate": "Lãi suất thực (mức)",
    "cpi_yoy_pct": "Lạm phát Mỹ YoY (mức)",
    "us10y_yield": "Lợi suất TP Mỹ 10 năm (mức)",
    "vix": "VIX (trung bình tháng)",
}

# Nhãn RÚT GỌN cho trục của heatmap. Nhãn dài ở NHAN_BIEN đặt trên trục 9 ô sẽ
# chồng lên nhau, và Plotly âm thầm bỏ bớt nhãn khi không đủ chỗ - người đọc mất
# luôn tên cột mà không hay biết. Tên đầy đủ vẫn hiện trong tooltip.
NHAN_NGAN = {
    "btc_ret": "BTC",
    "eth_ret": "ETH",
    "sp500": "S&P 500",
    "gold_usd": "Vàng",
    "brent_oil": "Dầu Brent",
    "dxy": "Chỉ số USD",
    "real_rate": "Lãi suất thực",
    "cpi_yoy_pct": "Lạm phát Mỹ",
    "us10y_yield": "TP Mỹ 10 năm",
    "vix": "VIX",
}

# Ba trạng thái khẩu vị rủi ro trong cột `risk_regime`. Giá trị trong file không
# dấu nên phải ánh xạ sang nhãn có dấu trước khi hiện lên biểu đồ.
NHAN_RISK_REGIME = {
    "Risk-on": "Risk-on (ưa rủi ro)",
    "Risk-off": "Risk-off (né rủi ro)",
    "Trung tinh": "Trung tính",
}

# ----------------------------------------------------------------------------
# BẪY DỮ LIỆU SỐ 1 (CLAUDE.md): trong hai bảng quốc gia, cột `continent` có giá
# trị chuỗi "NA" nghĩa là North America - Bắc Mỹ. Mặc định pandas hiểu "NA" là
# giá trị THIẾU và nuốt mất 22 quốc gia Bắc Mỹ, lại không báo lỗi gì. Vì vậy
# mọi lần đọc bảng quốc gia đều phải kèm hai tham số dưới đây.
# ----------------------------------------------------------------------------
DOC_QUOC_GIA = dict(keep_default_na=False, na_values=[""], encoding="utf-8-sig")


# =============================================================================
# 7 hàm nạp dữ liệu - mỗi bảng một hàm, đều được cache
# =============================================================================
@st.cache_data(show_spinner="Đang nạp bảng giá crypto…")
def nap_crypto_daily() -> pd.DataFrame:
    """Bảng fact chính: 123.358 dòng, 39 coin, đã join sẵn chỉ số vĩ mô theo ngày."""
    return pd.read_csv(
        THU_MUC_DU_LIEU / "fact_crypto_daily.csv.gz",
        parse_dates=["date"],
        encoding="utf-8-sig",
    )


@st.cache_data(show_spinner="Đang nạp bảng vốn hoá…")
def nap_market_daily() -> pd.DataFrame:
    """Vốn hoá + khối lượng của 63 coin.

    Nhiều coin hơn bảng trên vì có coin chỉ công bố vốn hoá mà không có giá.
    Dùng cho treemap thị phần ở bước sau.
    """
    return pd.read_csv(
        THU_MUC_DU_LIEU / "fact_market_daily.csv",
        parse_dates=["date"],
        encoding="utf-8-sig",
    )


@st.cache_data(show_spinner="Đang nạp chỉ số vĩ mô…")
def nap_macro_daily() -> pd.DataFrame:
    """16 chỉ số vĩ mô theo ngày, 2013 -> 2026-09."""
    return pd.read_csv(
        THU_MUC_DU_LIEU / "fact_macro_daily.csv",
        parse_dates=["date"],
        encoding="utf-8-sig",
    )


@st.cache_data(show_spinner="Đang nạp dữ liệu quốc gia…")
def nap_country_macro() -> pd.DataFrame:
    """Lạm phát / GDP / dân số của 215 quốc gia, 2013-2024. Bảng cấp cho bản đồ."""
    return pd.read_csv(
        THU_MUC_DU_LIEU / "fact_country_macro.csv",
        **DOC_QUOC_GIA,
    )


@st.cache_data(show_spinner="Đang nạp tỷ giá…")
def nap_fx_daily() -> pd.DataFrame:
    """Tỷ giá nội tệ / USD của 22 nền kinh tế."""
    return pd.read_csv(
        THU_MUC_DU_LIEU / "fact_fx_daily.csv",
        parse_dates=["date"],
        encoding="utf-8-sig",
    )


@st.cache_data(show_spinner="Đang nạp danh mục coin…")
def nap_dim_coin() -> pd.DataFrame:
    """Bảng chiều 63 coin: nhóm, hạng vốn hoá, có lịch sử giá hay không."""
    return pd.read_csv(
        THU_MUC_DU_LIEU / "dim_coin.csv",
        parse_dates=["first_date", "last_date"],
        encoding="utf-8-sig",
    )


@st.cache_data(show_spinner="Đang nạp danh mục quốc gia…")
def nap_dim_country() -> pd.DataFrame:
    """Bảng chiều 249 quốc gia. Cũng dính bẫy "NA" = Bắc Mỹ nên đọc kèm DOC_QUOC_GIA."""
    return pd.read_csv(
        THU_MUC_DU_LIEU / "dim_country.csv",
        **DOC_QUOC_GIA,
    )


# =============================================================================
# Hàm phục vụ sidebar
# =============================================================================
@st.cache_data
def khoang_ngay_crypto() -> tuple[pd.Timestamp, pd.Timestamp]:
    """Ngày đầu và ngày cuối có trong bảng giá.

    Đọc từ dim_coin (63 dòng) chứ không quét bảng fact 123k dòng - rẻ hơn nhiều
    mà vẫn ra đúng biên. Ngày cuối là 2026-05-23 (bẫy dữ liệu số 6: dữ liệu
    crypto dừng ở đây, còn vĩ mô chạy tới 2026-09).
    """
    dim = nap_dim_coin()
    co_gia = dim[dim["has_price_history"] == 1]
    return co_gia["first_date"].min(), co_gia["last_date"].max()


@st.cache_data
def danh_sach_nhom_coin() -> list[str]:
    """Các nhóm coin để đổ vào selectbox, kèm lựa chọn "Tất cả" ở đầu.

    Chỉ lấy nhóm của những coin CÓ giá, nếu không người dùng chọn trúng một nhóm
    toàn coin thiếu giá và biểu đồ ra trắng trơn.
    """
    dim = nap_dim_coin()
    co_gia = dim[dim["has_price_history"] == 1]
    return [NHOM_TAT_CA] + sorted(co_gia["category"].dropna().unique().tolist())


@st.cache_data
def coin_co_gia(nhom: str = NHOM_TAT_CA) -> list[str]:
    """Danh sách ticker có lịch sử giá, xếp theo hạng vốn hoá (BTC, ETH... trước).

    BẪY DỮ LIỆU SỐ 7: chỉ 39/63 coin có giá, phải lọc `has_price_history == 1`.
    Xếp theo `mcap_rank` để coin lớn nằm đầu danh sách - người dùng đỡ phải cuộn.
    """
    dim = nap_dim_coin()
    co_gia = dim[dim["has_price_history"] == 1]
    if nhom and nhom != NHOM_TAT_CA:
        co_gia = co_gia[co_gia["category"] == nhom]
    return co_gia.sort_values("mcap_rank")["ticker"].tolist()


# =============================================================================
# Hàm lọc dùng chung cho mọi trang
# =============================================================================
def loc_du_lieu(
    tu_ngay,
    den_ngay,
    danh_sach_coin: list[str] | None = None,
    nhom_coin: str = NHOM_TAT_CA,
    von_hoa_toi_thieu: float = 0.0,
) -> pd.DataFrame:
    """Lọc bảng fact chính theo 4 tầng lồng nhau.

    khoảng ngày -> nhóm coin -> coin cụ thể -> ngưỡng vốn hoá tối thiểu.

    Bốn điều kiện nối bằng AND, đúng nghĩa "filter nhiều cấp" mà barem yêu cầu.
    Tầng 2 còn quyết định luôn danh sách đổ vào tầng 3 (xem `coin_co_gia`), nên
    chọn nhóm "DeFi" là ô chọn coin bên dưới tự rút lại chỉ còn coin DeFi.

    Tầng 4 lọc theo vốn hoá TẠI TỪNG NGÀY chứ không theo vốn hoá hiện tại: một
    coin mới ra đời có thể chưa đạt ngưỡng ở 2019 nhưng vượt ngưỡng từ 2021.
    Lọc theo vốn hoá hiện tại sẽ kéo ngược cả lịch sử lúc nó còn rất nhỏ vào
    biểu đồ, làm sai phần so sánh theo thời gian.

    Không bọc `@st.cache_data` cho hàm này: lọc 123k dòng chỉ mất vài mili-giây,
    trong khi cache sẽ giữ một bản sao DataFrame cho MỖI tổ hợp filter mà người
    dùng từng bấm qua, rất tốn RAM.

    Trả về bản `.copy()` để trang gọi có thêm cột tính toán mà không đụng vào
    DataFrame gốc đang nằm trong cache.
    """
    df = nap_crypto_daily()
    tu, den = pd.Timestamp(tu_ngay), pd.Timestamp(den_ngay)

    dieu_kien = df["date"].between(tu, den)
    if nhom_coin and nhom_coin != NHOM_TAT_CA:
        dieu_kien &= df["category"] == nhom_coin
    if danh_sach_coin is not None:
        dieu_kien &= df["ticker"].isin(danh_sach_coin)
    if von_hoa_toi_thieu and von_hoa_toi_thieu > 0:
        dieu_kien &= df["market_cap_usd"] >= von_hoa_toi_thieu

    return df.loc[dieu_kien].copy()


# =============================================================================
# Bảng tháng dùng cho scatter và heatmap (trang Vĩ mô)
# =============================================================================
def dung_bang_thang(df: pd.DataFrame, nam_bat_dau: int = 2018) -> pd.DataFrame:
    """Gộp tháng lịch hoàn tất; tính lợi suất trước khi cắt khoảng nghiên cứu.

    Giá cuối tháng 12 được dùng làm gốc cho lợi suất tháng 1. Tháng cuối chưa
    hoàn tất không được giả thành quan sát cuối tháng; không điền giá còn thiếu.
    """
    moc = str(nam_bat_dau)
    btc = df[df["ticker"] == "BTC"].set_index("date").sort_index()
    eth = df[df["ticker"] == "ETH"].set_index("date").sort_index()

    bang = pd.concat(
        [
            # Giá BTC + các biến dạng giá -> lợi suất tháng
            btc[["price_usd", *BIEN_GIA]]
            .resample("ME")
            .last()
            .pct_change(fill_method=None)
            .loc[moc:]
            .rename(columns={"price_usd": "btc_ret"}),
            # ETH tách riêng vì nằm ở dòng ticker khác
            eth[["price_usd"]]
            .resample("ME")
            .last()
            .pct_change(fill_method=None)
            .loc[moc:]
            .rename(columns={"price_usd": "eth_ret"}),
            # Lãi suất / lạm phát / chỉ số USD -> giữ nguyên mức cuối tháng
            btc[BIEN_MUC].resample("ME").last().loc[moc:],
            # VIX -> trung bình trong tháng
            btc[BIEN_TB].resample("ME").mean().loc[moc:],
            # Khẩu vị rủi ro của tháng: lấy trạng thái phiên cuối tháng
            btc[["risk_regime"]].resample("ME").last().loc[moc:],
        ],
        axis=1,
    )
    bang.index.name = "thang"
    if not btc.empty:
        bang = bang.loc[bang.index <= btc.index.max()]
    if not eth.empty:
        bang.loc[bang.index > eth.index.max(), "eth_ret"] = float("nan")
    return bang.reset_index()


@st.cache_data(show_spinner="Đang gộp dữ liệu về tháng…")
def bang_thang(nam_bat_dau: int = 2018) -> pd.DataFrame:
    """Bản có cache của `dung_bang_thang`, dùng trong dashboard."""
    return dung_bang_thang(nap_crypto_daily(), nam_bat_dau)
