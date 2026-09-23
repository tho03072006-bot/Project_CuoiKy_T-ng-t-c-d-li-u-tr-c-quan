# -*- coding: utf-8 -*-
"""
Bảng màu và style dùng chung cho toàn bộ biểu đồ EDA.

Bộ màu đã qua kiểm định: dải độ sáng, sàn chroma, khoảng cách màu cho người mù màu
(CVD ΔE >= 8 trên OKLab ×100) và độ tương phản với nền. Ba slot đầu kiểm định đạt ở
chế độ "all-pairs" nên dùng an toàn cho biểu đồ phân tán nhiều nhóm.
"""
import textwrap
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# --- Nền và chữ ---
SURFACE  = "#fcfcfb"
INK      = "#0b0b0b"   # chữ chính
INK_SOFT = "#52514e"   # chữ phụ
GRID     = "#e8e7e3"   # lưới mờ, chỉ cách nền một bậc

# --- Màu định danh (categorical), dùng ĐÚNG THỨ TỰ, không xoay vòng ---
C1_BLUE   = "#2a78d6"
C2_ORANGE = "#eb6834"
C3_AQUA   = "#1baf7a"
C4_YELLOW = "#eda100"
C8_RED    = "#e34948"

# --- Thang đo liên tục (sequential): MỘT màu, nhạt -> đậm ---
SEQ_BLUE = LinearSegmentedColormap.from_list(
    "seq_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#0d366b"])

# --- Thang đo phân cực (diverging): hai màu đối nghịch + xám trung tính ở giữa ---
DIVERGING = LinearSegmentedColormap.from_list(
    "div_red_blue", ["#e34948", "#f0efec", "#2a78d6"])


def apply_style():
    """Nét mảnh, lưới mờ liền nét, bỏ khung viền thừa."""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans",          # hỗ trợ đầy đủ dấu tiếng Việt
        "font.size": 10, "axes.labelsize": 10,
        "axes.labelcolor": INK_SOFT, "text.color": INK,
        "xtick.color": INK_SOFT, "ytick.color": INK_SOFT,
        "xtick.labelsize": 9, "ytick.labelsize": 9,
        "axes.edgecolor": GRID, "axes.linewidth": 0.8,
        "grid.color": GRID, "grid.linewidth": 0.8,
        "grid.linestyle": "-",                 # lưới LIỀN NÉT, không đứt nét
        "legend.frameon": False, "legend.fontsize": 9,
        "lines.linewidth": 1.6,                # nét mảnh
        "figure.dpi": 130, "savefig.dpi": 150, "savefig.bbox": "tight",
    })


def tidy(ax, grid_axis="y"):
    """Bỏ khung trên/phải, chỉ giữ lưới mờ một chiều."""
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.grid(True, axis=grid_axis, alpha=0.9, zorder=0)
    ax.set_axisbelow(True)
    return ax


def tieu_de_2_dong(ax, chinh, phu, rong=80, gap=0.014, **_):
    """Tiêu đề đậm ở trên, dòng diễn giải mảnh màu nhạt ở dưới.

    Chiều cao khối diễn giải được tính theo chiều cao THỰC của trục (inch) nên
    tiêu đề luôn nằm phía trên, không bao giờ chồng lên - kể cả khi diễn giải
    dài 3 dòng hay hình có tỉ lệ khác nhau.
    """
    fig = ax.figure
    cao_truc_inch = fig.get_size_inches()[1] * ax.get_position().height
    if cao_truc_inch <= 0:
        cao_truc_inch = fig.get_size_inches()[1]
    cao_dong_phu = (9.5 * 1.45 / 72) / cao_truc_inch      # 1 dòng phụ, quy ra tỉ lệ trục
    khoi = textwrap.fill(phu, rong)
    so_dong = khoi.count("\n") + 1
    y_phu = 1.0 + gap
    ax.text(0, y_phu, khoi, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=9.5, color=INK_SOFT, linespacing=1.45)
    ax.text(0, y_phu + so_dong * cao_dong_phu + gap, chinh, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=12.5, fontweight="bold", color=INK)


def dat_tieu_de(ax, chinh, phu=None, rong=78):
    """Giữ lại cho tương thích - gọi sang tieu_de_2_dong."""
    if phu:
        tieu_de_2_dong(ax, chinh, phu, rong)
    else:
        ax.set_title(chinh, loc="left", pad=12, fontsize=12.5,
                     fontweight="bold", color=INK)


def caption(fig, text):
    """Chú thích nguồn ở chân hình - bắt buộc cho báo cáo khoa học."""
    fig.text(0.005, -0.02, text, ha="left", va="top", fontsize=7.5, color=INK_SOFT)
