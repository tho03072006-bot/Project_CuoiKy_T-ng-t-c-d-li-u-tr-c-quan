# -*- coding: utf-8 -*-
"""Trang Bản đồ - choropleth có drill-down 3 cấp.

  Hình 9 - Choropleth (bản đồ bắt buộc của barem)  <- NGUỒN cross-filter
  Hình 10 - Bar so sánh trong phạm vi đang xem     <- ĐÍCH cross-filter

Drill-down 3 cấp, trạng thái giữ trong st.session_state:
  Cấp 1 "toan_cau"  - cả thế giới, bấm một quốc gia -> xuống cấp 2
  Cấp 2 "chau_luc"  - phóng vào châu lục của quốc gia đó, bấm tiếp -> cấp 3
  Cấp 3 "quoc_gia"  - một quốc gia, hiện chuỗi thời gian của chính nó
Có breadcrumb và nút "Quay lại" ở mọi cấp.

HAI BẪY DỮ LIỆU phải xử lý trên trang này:
  * Bẫy 1: cột `continent` có giá trị "NA" = Bắc Mỹ, không phải giá trị thiếu.
    Đã xử lý ở tầng nạp (dl.DOC_QUOC_GIA).
  * Bẫy 5: lạm phát có ca cực đoan (Lebanon 221% năm 2023) kéo giãn thang màu
    làm cả thế giới chung một màu nhạt. Xử lý bằng cắt ngưỡng phân vị 95.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import data_layer as dl
from style import C1_BLUE, INK_SOFT, SEQ_BLUE, dinh_dang_tien, so_viet, tieu_de, ve

NAM_MAC_DINH = 2023

# Mã châu lục trong dữ liệu -> tên tiếng Việt và vùng scope của Plotly.
# "NA" ở đây là Bắc Mỹ. Plotly gộp Bắc và Nam Mỹ vào một scope "north america" /
# "south america" nên ánh xạ riêng từng mã.
CHAU_LUC = {
    "AF": ("Châu Phi", "africa"),
    "AS": ("Châu Á", "asia"),
    "EU": ("Châu Âu", "europe"),
    "NA": ("Bắc Mỹ", "north america"),
    "OC": ("Châu Đại Dương", "world"),  # Plotly không có scope riêng cho châu Úc
    "SA": ("Nam Mỹ", "south america"),
}

# Ba chỉ số cho phép hiển thị. Mỗi chỉ số khai báo luôn cách xử lý thang màu.
CHI_SO = {
    "inflation_pct": {
        "nhan": "Lạm phát (%/năm)",
        "don_vi": "%",
        "dinh_dang": lambda x: f"{so_viet(x, 1)}%",
        # Cắt phân vị vì có ca cực đoan - xem bẫy dữ liệu số 5.
        "cat_phan_vi": True,
    },
    "gdp_per_capita_usd": {
        "nhan": "GDP đầu người (USD)",
        "don_vi": "USD",
        "dinh_dang": dinh_dang_tien,
        # GDP đầu người trải 3 bậc độ lớn -> dùng log thay vì cắt ngưỡng, giữ
        # được cả nhóm giàu lẫn nhóm nghèo trên cùng một thang.
        "cat_phan_vi": False,
        "log": True,
    },
    "population": {
        "nhan": "Dân số (người)",
        "don_vi": "người",
        "dinh_dang": lambda x: f"{so_viet(x, 0)} người",
        # Trung Quốc và Ấn Độ gấp trăm lần phần còn lại -> bắt buộc log.
        "cat_phan_vi": False,
        "log": True,
    },
}


# =============================================================================
# Trạng thái drill-down
# =============================================================================
def dat_cap(cap: str, chau: str | None = None, quoc_gia: str | None = None) -> None:
    """Ghi trạng thái drill-down vào session_state.

    Dùng callback thay vì gán trực tiếp trong thân script: gán trực tiếp rồi gọi
    st.rerun() ở giữa trang sẽ bỏ dở phần đã vẽ, nhìn thấy hình nhấp nháy.
    """
    st.session_state["bando_cap"] = cap
    st.session_state["bando_chau"] = chau
    st.session_state["bando_quoc_gia"] = quoc_gia
    # Đổi khóa widget/chart khi chuyển cấp để lựa chọn cũ không tự kéo người
    # dùng quay xuống sau khi họ bấm Quay lại hoặc Về toàn cầu.
    st.session_state["bando_lan_chuyen"] = st.session_state.get("bando_lan_chuyen", 0) + 1
    st.session_state.pop("bando_diem_chon", None)


cap = st.session_state.setdefault("bando_cap", "toan_cau")
chau_hien = st.session_state.setdefault("bando_chau", None)
quoc_gia_hien = st.session_state.setdefault("bando_quoc_gia", None)
lan_chuyen = st.session_state.setdefault("bando_lan_chuyen", 0)

quoc_gia_df = dl.nap_country_macro()

st.title("Bản đồ kinh tế vĩ mô")
st.caption(
    "Bộ lọc riêng: năm → châu lục → quốc gia. Bản đồ mô tả bối cảnh kinh tế; "
    "dữ liệu này không đo mức sở hữu hay mức chấp nhận cryptocurrency theo quốc gia."
)


# =============================================================================
# Thanh điều khiển: chỉ số + năm
# =============================================================================
c1, c2, c3 = st.columns([2, 2, 1], vertical_alignment="bottom")
with c1:
    ma_chi_so = st.selectbox(
        "Chỉ số hiển thị",
        list(CHI_SO),
        format_func=lambda k: CHI_SO[k]["nhan"],
        key="w_chi_so_ban_do",
    )
with c2:
    cac_nam = sorted(quoc_gia_df["year"].unique())
    nam = st.select_slider(
        "Năm",
        options=cac_nam,
        value=NAM_MAC_DINH if NAM_MAC_DINH in cac_nam else cac_nam[-1],
        key="w_nam_ban_do",
        help=f"Dữ liệu quốc gia: {cac_nam[0]}–{cac_nam[-1]}; độc lập với khoảng ngày crypto ở sidebar.",
    )
with c3:
    st.button(
        "Về toàn cầu",
        icon=":material/public:",
        key="w_ve_toan_cau",
        disabled=cap == "toan_cau",
        on_click=dat_cap,
        args=("toan_cau", None, None),
    )

cau_hinh = CHI_SO[ma_chi_so]
nam_df = quoc_gia_df[quoc_gia_df["year"] == nam].dropna(subset=[ma_chi_so]).copy()
if cau_hinh.get("log"):
    nam_df = nam_df[nam_df[ma_chi_so] > 0]
if nam_df.empty:
    st.warning("Không có dữ liệu cho chỉ số và năm này.")
    st.stop()
if chau_hien and chau_hien not in set(nam_df["continent"]):
    dat_cap("toan_cau")
    st.rerun()


# =============================================================================
# Breadcrumb + nút Quay lại
# =============================================================================
def _iso_tu_diem(diem: dict, khung: pd.DataFrame) -> str | None:
    """Rút mã ISO-3 ra khỏi một điểm trong `event.selection.points`.

    Streamlit không trả về cùng một bộ khoá cho mọi loại trace: với choropleth
    thì KHÔNG có khoá "location" như tài liệu Plotly, chỉ có chỉ số của điểm.
    Vì vậy phải thử lần lượt và cuối cùng dùng chỉ số để tra ngược vào chính
    DataFrame đã nạp cho trace - thứ tự dòng của khung chính là thứ tự điểm.
    """
    tap_iso = set(khung["iso3"])
    for khoa in ("location", "locations"):
        if isinstance(diem.get(khoa), str) and diem[khoa] in tap_iso:
            return diem[khoa]
    # customdata của cả hai hình đều có ISO-3 ở cuối, ổn định hơn chỉ số điểm.
    du_lieu = diem.get("customdata")
    if isinstance(du_lieu, (list, tuple)) and du_lieu and du_lieu[-1] in tap_iso:
        return du_lieu[-1]
    # Bar ngang: trục y chính là tên quốc gia.
    if diem.get("y"):
        khop = khung[khung["country_name"] == diem["y"]]
        if len(khop):
            return khop["iso3"].iloc[0]
    for khoa in ("point_index", "point_number", "pointIndex", "pointNumber"):
        chi_so = diem.get(khoa)
        if isinstance(chi_so, (int, float)) and 0 <= int(chi_so) < len(khung):
            return khung["iso3"].iloc[int(chi_so)]
    # customdata[0] là tên quốc gia - đường cứu cánh cuối cùng.
    if diem.get("customdata"):
        khop = khung[khung["country_name"] == diem["customdata"][0]]
        if len(khop):
            return khop["iso3"].iloc[0]
    return None


def ten_quoc_gia(iso3: str) -> str:
    """Tên quốc gia từ mã ISO-3, tra trong bảng chiều."""
    khop = quoc_gia_df.loc[quoc_gia_df["iso3"] == iso3, "country_name"]
    return khop.iloc[0] if len(khop) else iso3


# --- Bộ chọn nhanh: đường drill xuống luôn dùng được ------------------------
# Widget là đường đi thay thế cho quốc gia quá nhỏ để bấm chính xác trên bản đồ.
chon1, chon2 = st.columns(2, vertical_alignment="bottom")
with chon1:
    ten_chau = {ma: ten for ma, (ten, _) in CHAU_LUC.items()}
    chau_co = [c for c in CHAU_LUC if c in set(nam_df["continent"])]
    chon_chau = st.selectbox(
        "Đi tới châu lục",
        ["— chọn —"] + chau_co,
        format_func=lambda c: c if c == "— chọn —" else ten_chau[c],
        index=0 if cap == "toan_cau" else (chau_co.index(chau_hien) + 1 if chau_hien in chau_co else 0),
        key=f"w_chon_chau_{lan_chuyen}_{nam}_{ma_chi_so}",
    )
    if chon_chau != "— chọn —" and (cap == "toan_cau" or chon_chau != chau_hien):
        dat_cap("chau_luc", chon_chau, None)
        st.rerun()
    if chon_chau == "— chọn —" and cap != "toan_cau":
        dat_cap("toan_cau")
        st.rerun()
with chon2:
    trong_pham_vi = (
        nam_df[nam_df["continent"] == chau_hien] if chau_hien else nam_df
    ).sort_values("country_name")
    ds_nuoc = trong_pham_vi["iso3"].tolist()
    ten_theo_iso = dict(zip(trong_pham_vi["iso3"], trong_pham_vi["country_name"]))
    chon_nuoc = st.selectbox(
        "Đi tới quốc gia",
        ["— chọn —"] + ds_nuoc,
        format_func=lambda i: i if i == "— chọn —" else ten_theo_iso.get(i, i),
        index=(ds_nuoc.index(quoc_gia_hien) + 1) if quoc_gia_hien in ds_nuoc else 0,
        key=f"w_chon_nuoc_{lan_chuyen}_{nam}_{ma_chi_so}",
        disabled=cap == "toan_cau",
        help="Chọn châu lục trước, hoặc bấm một cột ở Hình 10.",
    )
    if chon_nuoc != "— chọn —" and chon_nuoc != quoc_gia_hien:
        dat_cap("quoc_gia", quoc_gia_df.loc[quoc_gia_df["iso3"] == chon_nuoc, "continent"].iloc[0], chon_nuoc)
        st.rerun()
    if chon_nuoc == "— chọn —" and cap == "quoc_gia":
        dat_cap("chau_luc", chau_hien)
        st.rerun()

vun, nut_lui = st.columns([5, 1], vertical_alignment="center")
with vun:
    duong_dan = ["Toàn cầu"]
    if cap in ("chau_luc", "quoc_gia") and chau_hien:
        duong_dan.append(CHAU_LUC.get(chau_hien, (chau_hien, "world"))[0])
    if cap == "quoc_gia" and quoc_gia_hien:
        duong_dan.append(ten_quoc_gia(quoc_gia_hien))
    st.markdown(
        "### "
        + f" <span style='color:{INK_SOFT};font-weight:400'>›</span> ".join(duong_dan),
        unsafe_allow_html=True,
    )
    st.caption(
        {
            "toan_cau": "Cấp 1/3 — chọn châu lục hoặc bấm cột quốc gia ở Hình 10 để đi sâu.",
            "chau_luc": "Cấp 2/3 — chọn quốc gia hoặc bấm cột ở Hình 10 để xem lịch sử riêng.",
            "quoc_gia": "Cấp 3/3 — đang xem một quốc gia.",
        }[cap]
    )
with nut_lui:
    if cap == "quoc_gia":
        st.button(
            "Quay lại",
            icon=":material/arrow_back:",
            key="w_quay_lai",
            on_click=dat_cap,
            args=("chau_luc", chau_hien, None),
        )
    elif cap == "chau_luc":
        st.button(
            "Quay lại",
            icon=":material/arrow_back:",
            key="w_quay_lai",
            on_click=dat_cap,
            args=("toan_cau", None, None),
        )
    else:
        st.button(
            "Quay lại",
            icon=":material/arrow_back:",
            key="w_quay_lai",
            disabled=True,
            help="Đang ở cấp cao nhất.",
        )


# =============================================================================
# HÌNH 9 - Choropleth
# =============================================================================
# Phạm vi dữ liệu theo cấp đang đứng.
if cap == "toan_cau":
    hien = nam_df
    scope = "world"
elif cap == "chau_luc":
    hien = nam_df[nam_df["continent"] == chau_hien]
    scope = CHAU_LUC.get(chau_hien, ("", "world"))[1]
else:
    hien = nam_df[nam_df["continent"] == chau_hien]
    scope = CHAU_LUC.get(chau_hien, ("", "world"))[1]

if hien.empty:
    st.warning(
        f"Năm {nam} không có dữ liệu {cau_hinh['nhan'].lower()} cho phạm vi này.",
        icon=":material/warning:",
    )
    st.stop()

with st.container(border=True):
    st.markdown("**Hình 9 — Bản đồ choropleth** · phạm vi thay đổi theo drill-down")

    gia_tri = hien[ma_chi_so]

    # --- Xử lý thang màu ------------------------------------------------------
    if cau_hinh.get("cat_phan_vi"):
        # BẪY DỮ LIỆU SỐ 5: Lebanon 221% năm 2023 trong khi phân vị 95 chỉ 31%.
        # Không cắt thì 95% quốc gia rơi vào 14% đầu của thang màu và cả bản đồ
        # chung một màu nhạt. Cắt ở phân vị 95: các nước vượt ngưỡng vẫn hiển
        # thị (màu đậm nhất) nhưng không còn kéo giãn thang.
        tran = float(np.nanpercentile(gia_tri, 95))
        san = float(np.nanmin(gia_tri))
        hien = hien.assign(gia_tri_ve=gia_tri.clip(upper=tran))
        vuot_nguong = hien[hien[ma_chi_so] > tran]
        ghi_chu_thang = (
            f"Thang màu cắt ở phân vị 95 = {so_viet(tran, 1)}%. "
            f"{len(vuot_nguong)} quốc gia vượt ngưỡng vẫn hiện màu đậm nhất"
            + (
                f" (cao nhất: {vuot_nguong.nlargest(1, ma_chi_so)['country_name'].iloc[0]} "
                f"{so_viet(vuot_nguong[ma_chi_so].max(), 1)}%)"
                if len(vuot_nguong)
                else ""
            )
            + "."
        )
    elif cau_hinh.get("log"):
        # Log hoá để 3 bậc độ lớn nằm vừa một thang. Giá trị <= 0 không lấy log
        # được nên loại, và nói rõ đã loại bao nhiêu dòng.
        truoc = len(hien)
        hien = hien[hien[ma_chi_so] > 0].copy()
        hien["gia_tri_ve"] = np.log10(hien[ma_chi_so])
        san, tran = hien["gia_tri_ve"].min(), hien["gia_tri_ve"].max()
        ghi_chu_thang = (
            f"Thang màu theo log10 vì chỉ số trải nhiều bậc độ lớn"
            + (f"; đã bỏ {truoc - len(hien)} quốc gia có giá trị ≤ 0" if truoc > len(hien) else "")
            + "."
        )
    else:
        hien = hien.assign(gia_tri_ve=gia_tri)
        san, tran = float(gia_tri.min()), float(gia_tri.max())
        ghi_chu_thang = "Thang màu tuyến tính."

    # Cột chữ đã định dạng sẵn cho tooltip (Plotly không viết được "1,2 tỷ USD").
    hien = hien.copy()
    hien["gia_tri_txt"] = hien[ma_chi_so].map(cau_hinh["dinh_dang"])
    hien["chau_ten"] = hien["continent"].map(lambda c: CHAU_LUC.get(c, (c, ""))[0])
    # Xếp hạng trong phạm vi đang xem - thông tin đắt giá trên tooltip.
    hien["hang"] = hien[ma_chi_so].rank(ascending=False, method="min").astype(int)

    hinh9 = px.choropleth(
        hien,
        locations="iso3",
        locationmode="ISO-3",
        color="gia_tri_ve",
        scope=scope,
        # Thang MỘT màu nhạt -> đậm. Tuyệt đối không rainbow.
        color_continuous_scale=SEQ_BLUE,
        range_color=(san, tran),
        custom_data=["country_name", "gia_tri_txt", "chau_ten", "hang", "iso3"],
    )
    hinh9.update_traces(
        marker_line_color="#fcfcfb",
        marker_line_width=0.4,
        hovertemplate=(
            "<b>%{customdata[0]}</b> · %{customdata[2]}<br>"
            + cau_hinh["nhan"]
            + ": <b>%{customdata[1]}</b><br>"
            "Hạng %{customdata[3]}/" + str(len(hien)) + " trong phạm vi đang xem"
            "<extra></extra>"
        ),
    )

    cao_nhat = hien.nlargest(1, ma_chi_so).iloc[0]
    trung_vi = hien[ma_chi_so].median()
    pham_vi_ten = (
        "toàn cầu" if cap == "toan_cau" else CHAU_LUC.get(chau_hien, ("", ""))[0]
    )
    hinh9.update_layout(
        title=tieu_de(
            f"{cao_nhat['country_name']} cao nhất {pham_vi_ten}: "
            f"{cau_hinh['dinh_dang'](cao_nhat[ma_chi_so])} năm {nam}",
            f"Trung vị {pham_vi_ten}: {cau_hinh['dinh_dang'](trung_vi)} · "
            f"{len(hien)} quốc gia có dữ liệu. {ghi_chu_thang}",
        ),
        height=560,
        margin=dict(l=12, r=12, t=110, b=12),
        geo=dict(
            bgcolor="#fcfcfb",
            lakecolor="#fcfcfb",
            landcolor="#f0efec",  # quốc gia KHÔNG có dữ liệu: xám trung tính
            showland=True,
            showframe=False,
            showcoastlines=False,
            projection_type="natural earth" if scope == "world" else "mercator",
        ),
        coloraxis_colorbar=dict(
            title=dict(text=cau_hinh["don_vi"], side="right"),
            thickness=12,
            len=0.6,
            # Ở thang log, nhãn colorbar phải quy ngược về giá trị thật, nếu để
            # nguyên thì người đọc thấy "3,5" mà không biết đó là 3.162 USD.
            **(
                dict(
                    tickvals=list(range(int(np.floor(san)), int(np.ceil(tran)) + 1)),
                    ticktext=[
                        so_viet(10**v, 0)
                        for v in range(int(np.floor(san)), int(np.ceil(tran)) + 1)
                    ],
                )
                if cau_hinh.get("log")
                else {}
            ),
        ),
    )

    su_kien_ban_do = ve(
        hinh9,
        key=f"bieu_do_ban_do_{cap}_{lan_chuyen}_{nam}_{ma_chi_so}",
        on_select="rerun",
        selection_mode=("points",),
    )

    # --- Xử lý sự kiện chọn khi phiên bản Plotly hỗ trợ choropleth selection.
    # Luôn giữ widget và bar chart để thao tác không phụ thuộc trace địa lý.
    diem = su_kien_ban_do.get("selection", {}).get("points", [])
    if diem:
        iso_chon = _iso_tu_diem(diem[0], hien)
        if iso_chon and iso_chon != st.session_state.get("bando_diem_chon"):
            st.session_state["bando_diem_chon"] = iso_chon
            dong = quoc_gia_df[quoc_gia_df["iso3"] == iso_chon]
            if len(dong):
                chau_cua_nuoc = dong.iloc[0]["continent"]
                if cap == "toan_cau":
                    dat_cap("chau_luc", chau_cua_nuoc, None)
                    st.rerun()
                elif cap == "chau_luc":
                    dat_cap("quoc_gia", chau_cua_nuoc, iso_chon)
                    st.rerun()

    st.caption(
        f"Nguồn: data/processed/fact_country_macro.csv · năm {nam} · "
        "quốc gia màu xám là không có số liệu trong phạm vi đang xem. "
        "Thang màu được tính lại khi đổi phạm vi, không dùng màu để so sánh trực tiếp giữa hai phạm vi."
    )


# =============================================================================
# HÌNH 10 - Bar so sánh  (ĐÍCH cross-filter của bản đồ)
# =============================================================================
with st.container(border=True):
    if cap == "quoc_gia" and quoc_gia_hien:
        # Cấp 3: đổi sang chuỗi thời gian của chính quốc gia đó.
        st.markdown("**Hình 10 — Lịch sử của quốc gia đang chọn (bar chart)**")
        lich_su = (
            quoc_gia_df[quoc_gia_df["iso3"] == quoc_gia_hien]
            .dropna(subset=[ma_chi_so])
            .sort_values("year")
            .copy()
        )
        if lich_su.empty:
            st.warning("Quốc gia này không có dữ liệu cho chỉ số đang chọn.")
        else:
            lich_su["gia_tri_txt"] = lich_su[ma_chi_so].map(cau_hinh["dinh_dang"])
            hinh10 = px.bar(
                lich_su,
                x="year",
                y=ma_chi_so,
                custom_data=["gia_tri_txt"],
                labels={"year": "", ma_chi_so: cau_hinh["nhan"]},
                color_discrete_sequence=[C1_BLUE],
            )
            hinh10.update_traces(
                hovertemplate="<b>Năm %{x}</b><br>"
                + cau_hinh["nhan"]
                + ": %{customdata[0]}<extra></extra>",
                marker_line_width=0,
            )
            dinh = lich_su.nlargest(1, ma_chi_so).iloc[0]
            hinh10.update_layout(
                title=tieu_de(
                    f"{ten_quoc_gia(quoc_gia_hien)} đạt đỉnh "
                    f"{cau_hinh['dinh_dang'](dinh[ma_chi_so])} năm {int(dinh['year'])}",
                    f"{len(lich_su)} năm có số liệu, {int(lich_su['year'].min())}–"
                    f"{int(lich_su['year'].max())}.",
                ),
                height=400,
                hovermode="closest",
                xaxis=dict(dtick=1),
            )
            ve(hinh10, key="bieu_do_lich_su")
    else:
        # Cấp 1 và 2: top 15 quốc gia trong phạm vi đang xem.
        st.markdown(
            "**Hình 10 — Xếp hạng trong phạm vi đang xem (bar chart)** · nguồn cross-filter · "
            "bấm một cột để đi sâu xuống"
        )
        top = hien.nlargest(15, ma_chi_so).sort_values(ma_chi_so)
        hinh10 = px.bar(
            top,
            x=ma_chi_so,
            y="country_name",
            orientation="h",
            custom_data=["gia_tri_txt", "chau_ten", "iso3"],
            labels={ma_chi_so: cau_hinh["nhan"], "country_name": ""},
            color_discrete_sequence=[C1_BLUE],
        )
        hinh10.update_traces(
            hovertemplate=(
                "<b>%{y}</b> · %{customdata[1]}<br>"
                + cau_hinh["nhan"]
                + ": %{customdata[0]}<br>"
                "<i>bấm để đi sâu xuống</i><extra></extra>"
            ),
            marker_line_width=0,
        )
        hinh10.update_layout(
            title=tieu_de(
                f"{len(top)} quốc gia dẫn đầu {pham_vi_ten} năm {nam}",
                "Biểu đồ này đi theo bản đồ: thu hẹp phạm vi là bảng xếp hạng "
                "tự tính lại. Bấm một cột để xuống cấp tiếp theo.",
            ),
            height=520,
            hovermode="closest",
            **({"xaxis": dict(type="log")} if cau_hinh.get("log") else {}),
        )
        su_kien_top = ve(
            hinh10,
            key=f"bieu_do_top_quoc_gia_{cap}_{lan_chuyen}_{nam}_{ma_chi_so}",
            on_select="rerun",
            selection_mode=("points",),
        )

        # Bar là trace hệ trục Đề-các nên selection CHẠY THẬT - đây là đường
        # drill-down chính thay cho cú bấm trên bản đồ.
        diem_top = su_kien_top.get("selection", {}).get("points", [])
        if diem_top:
            iso_bam = _iso_tu_diem(diem_top[0], top)
            if iso_bam and iso_bam != st.session_state.get("bando_diem_chon"):
                st.session_state["bando_diem_chon"] = iso_bam
                chau_cua_nuoc = quoc_gia_df.loc[
                    quoc_gia_df["iso3"] == iso_bam, "continent"
                ].iloc[0]
                if cap == "toan_cau":
                    dat_cap("chau_luc", chau_cua_nuoc, None)
                else:
                    dat_cap("quoc_gia", chau_cua_nuoc, iso_bam)
                st.rerun()
