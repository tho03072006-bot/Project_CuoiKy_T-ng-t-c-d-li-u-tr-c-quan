# -*- coding: utf-8 -*-
"""Dự báo BTC có holdout theo thời gian; chạy ``python models/du_bao.py``.

OLS: lợi suất tháng t dùng BTC tháng t-1 và vĩ mô tháng t-2. Chỉ tháng BTC
đủ ngày mới là nhãn huấn luyện/đánh giá. Logistic: hướng giá ngày t chỉ dùng
giá/khối lượng đến cuối ngày t-1. Chia train <2024, test >=2024; mọi bước học
được fit trên train. Một mô hình refit riêng dùng dữ liệu đến cutoff để dự báo
phiên tiếp theo, không dùng mô hình refit tính các chỉ số holdout.

Dữ liệu vĩ mô không có vintage/ngày công bố: trễ hai tháng là giả định bảo thủ,
không chứng minh được tính point-in-time của dữ liệu đã chỉnh sửa về sau.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import platform
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, brier_score_loss, confusion_matrix,
                             f1_score, mean_absolute_error, mean_squared_error,
                             precision_score, r2_score, recall_score,
                             roc_auc_score, roc_curve)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson

GOC = Path(__file__).resolve().parent.parent
THU_MUC_MO_HINH = GOC / "models"
DUONG_DAN_DU_LIEU = GOC / "data" / "processed" / "fact_crypto_daily.csv.gz"
NAM_BAT_DAU, NAM_CAT_TRAIN = 2018, 2024
NGUONG_VIF, ALPHA = 10.0, 0.05
BIEN_GOC = ["sp500", "cpi_yoy_pct", "dxy", "real_rate", "vix"]
BIEN_LOGISTIC = ["log_return", "volatility_30d", "turnover_ratio", "drawdown_pct",
                 "ty_le_ma", "gia_tren_ma30", "volume_tren_ma30"]


def _kiem_tra_ngay(btc: pd.DataFrame) -> pd.DataFrame:
    """Dừng nếu trùng ngày để shift không âm thầm lấy nhầm một quan sát."""
    x = btc.copy().sort_index()
    if not isinstance(x.index, pd.DatetimeIndex) or x.index.has_duplicates:
        raise ValueError("BTC cần DatetimeIndex duy nhất theo ngày.")
    return x


def dung_bang_thang(btc: pd.DataFrame) -> pd.DataFrame:
    """Không dùng ngày 23 như giá cuối tháng; giữ lịch sử trước 2018 cho lag."""
    x = _kiem_tra_ngay(btc)
    muc = x[["price_usd", *BIEN_GOC]].resample("ME").last()
    # BTC giao dịch cả cuối tuần: một tháng hoàn tất phải có giá cho đủ mọi ngày.
    so_ngay = x["price_usd"].resample("ME").count()
    du_thang = (so_ngay == so_ngay.index.days_in_month) & (muc.index <= x.index.max())
    muc.loc[~du_thang] = np.nan
    bang = muc.copy()
    bang["btc_ret"] = muc["price_usd"].pct_change(fill_method=None)
    bang["sp500"] = muc["sp500"].pct_change(fill_method=None)
    bang["dxy"] = muc["dxy"].pct_change(fill_method=None)
    bang["cpi_yoy_pct"] = muc["cpi_yoy_pct"].diff()
    bang["real_rate"] = muc["real_rate"].diff()
    bang["vix"] = x["vix"].resample("ME").mean().where(du_thang).diff()
    # Loại đuôi chưa hoàn tất nhưng giữ tháng trống ở giữa để lag còn đúng lịch.
    bang = bang.loc[:du_thang[du_thang].index.max()]
    bang.index.name = "thang"
    return bang.reset_index()


def _dac_trung_thang(bang: pd.DataFrame) -> pd.DataFrame:
    """Lag vĩ mô hai tháng dành một tháng cho độ trễ công bố; không dùng cùng kỳ."""
    b = bang.set_index("thang").sort_index()
    x = pd.DataFrame({"btc_ret_tre1": b["btc_ret"].shift(1)}, index=b.index)
    for bien in BIEN_GOC:
        x[f"{bien}_tre2"] = b[bien].shift(2)
    return x.replace([np.inf, -np.inf], np.nan)


def chuan_bi_du_lieu_tuyen_tinh(bang: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Chỉ nhãn đủ tháng được dùng; không dropna trước shift làm lệch khoảng lag."""
    b = bang.set_index("thang").sort_index()
    du = pd.concat([b["btc_ret"], _dac_trung_thang(bang)], axis=1).dropna()
    du = du.loc[str(NAM_BAT_DAU):]
    return du.drop(columns="btc_ret"), du["btc_ret"]


def vif_cuoi(x: pd.DataFrame) -> pd.DataFrame:
    """VIF tính trên train để lựa chọn biến không nhìn thấy phân phối test."""
    thiet_ke = sm.add_constant(x, has_constant="add")
    return pd.DataFrame({"bien": x.columns, "vif": [
        float(variance_inflation_factor(thiet_ke.to_numpy(), i + 1))
        for i in range(x.shape[1])]})


def loai_theo_vif(x: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Bỏ từng biến trên train vì VIF còn lại đổi sau mỗi lần bỏ."""
    x, nhat_ky = x.copy(), []
    for ten in list(x):
        if x[ten].std() == 0:
            x = x.drop(columns=ten)
            nhat_ky.append({"bien_bi_loai": ten, "vif": None, "ly_do": "Hằng số trên train"})
    while x.shape[1] > 1:
        vif = vif_cuoi(x).set_index("bien")["vif"]
        ten = vif.idxmax()
        if vif[ten] <= NGUONG_VIF:
            break
        nhat_ky.append({"bien_bi_loai": ten, "vif": float(vif[ten])})
        x = x.drop(columns=ten)
    if x.empty:
        raise ValueError("Không còn đặc trưng biến thiên trên train.")
    return x, pd.DataFrame(nhat_ky)


def _fit_ols(x: pd.DataFrame, y: pd.Series):
    """HAC giảm nhạy với phương sai thay đổi/tự tương quan; không bảo đảm CI đúng."""
    return sm.OLS(y, sm.add_constant(x, has_constant="add")).fit(
        cov_type="HAC", cov_kwds={"maxlags": 3}, use_t=True)


def _khoang_ngay(index: pd.DatetimeIndex, ten: str) -> dict:
    """Lưu ngày thật của từng split để dashboard không tự đoán khoảng đánh giá."""
    return {f"ngay_{ten}_dau": str(index.min().date()),
            f"ngay_{ten}_cuoi": str(index.max().date())}


def huan_luyen_tuyen_tinh(bang: pd.DataFrame) -> dict:
    """OLS giữ holdout cố định; baseline dự đoán lợi suất 0 (giá không đổi)."""
    x, y = chuan_bi_du_lieu_tuyen_tinh(bang)
    train, test = x.index.year < NAM_CAT_TRAIN, x.index.year >= NAM_CAT_TRAIN
    if train.sum() < 24 or test.sum() < 2:
        raise ValueError("Không đủ dữ liệu train/test theo mốc 2024.")
    xtr, nhat_ky = loai_theo_vif(x.loc[train])
    xte, ytr, yte = x.loc[test, xtr.columns], y.loc[train], y.loc[test]
    kq = _fit_ols(xtr, ytr)
    du_bao = kq.get_prediction(sm.add_constant(xte, has_constant="add")).summary_frame(alpha=ALPHA)
    mean = du_bao["mean"].to_numpy()
    baseline = np.zeros(len(yte))
    rmse = float(np.sqrt(mean_squared_error(yte, mean)))
    rmse_co_so = float(np.sqrt(mean_squared_error(yte, baseline)))
    bang_db = pd.DataFrame({"thang": yte.index, "loi_suat_thuc": yte.to_numpy(),
        "loi_suat_du_bao": mean, "loi_suat_co_so": baseline,
        "can_duoi": du_bao["obs_ci_lower"].to_numpy(),
        "can_tren": du_bao["obs_ci_upper"].to_numpy(), "tap": "test"})
    so_cn = int((kq.pvalues.drop("const") < ALPHA).sum())
    # Refit riêng sau khi đóng băng đánh giá; không ghi đè model train/holdout.
    kq_refit = _fit_ols(x[xtr.columns], y)
    b = bang.copy().sort_values("thang")
    ngay_cuoi = pd.Timestamp(b["thang"].max())
    thang_tiep = ngay_cuoi + pd.offsets.MonthEnd(1)
    b_tiep = pd.concat([b, pd.DataFrame({"thang": [thang_tiep]})], ignore_index=True)
    x_tiep = _dac_trung_thang(b_tiep).loc[[thang_tiep], xtr.columns]
    if x_tiep.isna().any().any():
        raise ValueError("Thiếu đặc trưng cho dự báo tháng tiếp theo.")
    db_tiep = kq_refit.get_prediction(sm.add_constant(x_tiep, has_constant="add")).summary_frame(alpha=ALPHA).iloc[0]
    gia_truoc = float(b.set_index("thang").loc[ngay_cuoi, "price_usd"])
    du_bao_tiep = {"thang": str(thang_tiep.date()), "ngay_thong_tin": str(ngay_cuoi.date()),
        "loi_suat_du_bao": float(db_tiep["mean"]), "can_duoi": float(db_tiep["obs_ci_lower"]),
        "can_tren": float(db_tiep["obs_ci_upper"]), "gia_truoc": gia_truoc,
        "gia_du_bao": gia_truoc * (1 + float(db_tiep["mean"])), "loai": "refit_toan_bo_thang_hoan_tat"}
    chi_so = {"n": int(len(y)), "n_train": int(len(ytr)), "n_test": int(len(yte)),
        "so_bien": int(xtr.shape[1]), "so_bien_ung_vien": int(x.shape[1]),
        "r2": float(kq.rsquared), "r2_hieu_chinh": float(kq.rsquared_adj),
        "r2_test": float(r2_score(yte, mean)), "mae_test": float(mean_absolute_error(yte, mean)),
        "rmse_test": rmse, "mae_co_so": float(mean_absolute_error(yte, baseline)),
        "rmse_co_so": rmse_co_so, "hon_co_so": bool(rmse < rmse_co_so),
        "coverage_test": float(((yte.to_numpy() >= bang_db.can_duoi) & (yte.to_numpy() <= bang_db.can_tren)).mean()),
        "f_stat": float(kq.fvalue), "f_pvalue": float(kq.f_pvalue), "aic": float(kq.aic),
        "bic": float(kq.bic), "durbin_watson": float(durbin_watson(kq.resid)),
        "jarque_bera_p": float(sm.stats.stattools.jarque_bera(kq.resid)[1]), "so_bien_co_y_nghia": so_cn,
        **_khoang_ngay(xtr.index, "train"), **_khoang_ngay(xte.index, "test")}
    return {"schema_version": 2, "ket_qua": kq, "mo_hinh_refit": kq_refit, "ten_bien": list(xtr.columns),
        "he_so_chuan_hoa": {ten: float(kq.params[ten] * xtr[ten].std() / ytr.std()) for ten in xtr},
        "bang_vif": vif_cuoi(xtr).to_dict("records"), "nhat_ky_vif": nhat_ky.to_dict("records"),
        "bang_du_bao": bang_db, "du_bao_tiep": du_bao_tiep,
        "phan_du": pd.DataFrame({"gia_tri_khop": kq.fittedvalues, "phan_du": kq.resid}),
        "chi_so": chi_so,
        "phuong_phap": {"target": "Lợi suất BTC tháng hoàn tất", "split": "Train <2024; holdout >=2024",
            "baseline": "Lợi suất 0, tương ứng giữ nguyên giá tháng trước", "sai_so_chuan": "HAC, maxlags=3",
            "dac_trung": "BTC lợi suất trễ 1 tháng; S&P500 và DXY lợi suất, CPI YoY/lãi suất thực/VIX sai phân trễ 2 tháng",
            "han_che": "Vĩ mô không có vintage/ngày công bố; lag 2 tháng là giả định. Khoảng dự báo 95% xấp xỉ theo OLS, không bảo đảm với đuôi dày. P-value sau chọn VIF có tính thăm dò; hệ số không chứng minh nhân quả."},
        "he_so": [{"bien": ten, "he_so": float(kq.params[ten]), "sai_so_chuan": float(kq.bse[ten]),
            "t": float(kq.tvalues[ten]), "p": float(kq.pvalues[ten]),
            "ci_duoi": float(kq.conf_int().loc[ten, 0]), "ci_tren": float(kq.conf_int().loc[ten, 1])}
            for ten in kq.params.index]}


def _dac_trung_ngay(btc: pd.DataFrame) -> pd.DataFrame:
    """Tính lại chỉ từ giá/khối lượng quá khứ để không phụ thuộc cột tính toàn kỳ."""
    x = _kiem_tra_ngay(btc)
    # Reindex lịch đầy đủ: thiếu một ngày phải thành NaN, không giả làm ngày kế tiếp.
    x = x.reindex(pd.date_range(x.index.min(), x.index.max(), freq="D"))
    gia, volume = x["price_usd"], x["volume_usd"]
    lr = np.log(gia.where(gia > 0)).diff()
    ma30 = gia.rolling(30, min_periods=30).mean()
    f = pd.DataFrame({"log_return": lr,
        "volatility_30d": lr.rolling(30, min_periods=30).std() * np.sqrt(365),
        "turnover_ratio": volume / x["market_cap_usd"].where(x["market_cap_usd"] > 0),
        "drawdown_pct": gia / gia.cummax() - 1,
        "ty_le_ma": gia.rolling(7, min_periods=7).mean() / ma30,
        "gia_tren_ma30": gia / ma30,
        "volume_tren_ma30": volume / volume.rolling(30, min_periods=30).mean()}, index=x.index)
    return f[BIEN_LOGISTIC].replace([np.inf, -np.inf], np.nan)


def chuan_bi_du_lieu_logistic(btc: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Shift đúng một ngày và tự tính target; giá thiếu không bị gán lớp giảm."""
    x = _dac_trung_ngay(btc).shift(1)
    gia = btc["price_usd"].reindex(x.index)
    ret = gia.pct_change(fill_method=None)
    y = (ret > 0).astype(float).where(ret.notna())
    du = pd.concat([y.rename("y"), x], axis=1).dropna().loc[str(NAM_BAT_DAU):]
    return du.drop(columns="y"), du["y"].astype(int)


def _logistic_pipeline() -> Pipeline:
    """Chuẩn hóa nằm trong pipeline nên holdout không tham gia học mean/std."""
    return Pipeline([("chuan_hoa", StandardScaler()),
                     ("logistic", LogisticRegression(max_iter=2000, C=1.0, random_state=42))])


def huan_luyen_logistic(btc: pd.DataFrame) -> dict:
    """Threshold 0.5 cố định; baseline là lớp đa số TRAIN, không chọn bằng test."""
    btc = _kiem_tra_ngay(btc)
    x, y = chuan_bi_du_lieu_logistic(btc)
    train, test = x.index.year < NAM_CAT_TRAIN, x.index.year >= NAM_CAT_TRAIN
    xtr, xte, ytr, yte = x.loc[train], x.loc[test], y.loc[train], y.loc[test]
    if min(len(ytr), len(yte)) == 0 or ytr.nunique() != 2 or yte.nunique() != 2:
        raise ValueError("Train/test logistic cần đủ hai lớp để đánh giá AUC.")
    model = _logistic_pipeline().fit(xtr, ytr)
    p = model.predict_proba(xte)[:, 1]
    pred = (p >= 0.5).astype(int)
    nhan_co_so = int(ytr.mean() >= 0.5)
    baseline = np.full(len(yte), nhan_co_so)
    acc, acc_co_so = float(accuracy_score(yte, pred)), float(accuracy_score(yte, baseline))
    fpr, tpr, _ = roc_curve(yte, p)
    # Refit riêng cho ngày CHƯA có nhãn; dùng đặc trưng cuối ngày cuối cùng.
    refit = _logistic_pipeline().fit(x, y)
    f = _dac_trung_ngay(btc)
    ngay_thong_tin = btc.index.max()
    cuoi = f.loc[[ngay_thong_tin]]
    if cuoi.isna().any().any():
        raise ValueError("Ngày cuối thiếu đặc trưng; không được dùng phiên cũ giả làm forecast mới.")
    phien = {"ngay": str((ngay_thong_tin + pd.Timedelta(days=1)).date()),
        "ngay_thong_tin": str(ngay_thong_tin.date()),
        "xac_suat_tang": float(refit.predict_proba(cuoi)[0, 1]), "loai": "refit_toan_bo_lich_su"}
    he_so = model.named_steps["logistic"].coef_[0]
    return {"schema_version": 2, "mo_hinh": model, "mo_hinh_refit": refit, "ten_dac_trung": list(x.columns),
        "he_so": {ten: float(h) for ten, h in zip(x.columns, he_so)},
        "chi_so": {"accuracy": acc, "precision": float(precision_score(yte, pred, zero_division=0)),
            "recall": float(recall_score(yte, pred, zero_division=0)), "f1": float(f1_score(yte, pred, zero_division=0)),
            "auc": float(roc_auc_score(yte, p)), "brier": float(brier_score_loss(yte, p)),
            "accuracy_co_so": acc_co_so, "f1_co_so": float(f1_score(yte, baseline, zero_division=0)),
            "brier_co_so": float(brier_score_loss(yte, np.full(len(yte), ytr.mean()))),
            "nhan_co_so": nhan_co_so, "hon_co_so": bool(acc > acc_co_so),
            "n_train": int(len(ytr)), "n_test": int(len(yte)),
            "ty_le_tang_train": float(ytr.mean()), "ty_le_tang_test": float(yte.mean()),
            **_khoang_ngay(xtr.index, "train"), **_khoang_ngay(xte.index, "test")},
        "ma_tran_nham_lan": confusion_matrix(yte, pred, labels=[0, 1]).tolist(),
        "roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "du_doan_test": pd.DataFrame({"ngay": xte.index, "thuc_te": yte.to_numpy(), "xac_suat": p,
                                       "du_doan": pred, "du_doan_co_so": baseline}),
        "phien_gan_nhat": phien,
        "phuong_phap": {"dac_trung": "7 biến giá/khối lượng tính nhân quả, trễ 1 ngày; bỏ vĩ mô/on-chain không rõ ngày khả dụng",
            "baseline": "Lớp đa số trên train; xác suất baseline là tỷ lệ tăng trên train",
            "nguong": 0.5, "han_che": "Đánh giá holdout lịch sử, chưa xác minh thời điểm công bố từng dòng dữ liệu. Không suy ra giả thuyết thị trường hiệu quả hay lợi nhuận giao dịch chỉ từ accuracy/AUC."}}


def main() -> None:
    """Lưu cùng nguồn/hash/phiên bản để có thể tái lập và phát hiện model lỗi thời."""
    THU_MUC_MO_HINH.mkdir(exist_ok=True)
    df = pd.read_csv(DUONG_DAN_DU_LIEU, parse_dates=["date"])
    btc = df.loc[df["ticker"] == "BTC"].set_index("date").sort_index()
    tt, lg = huan_luyen_tuyen_tinh(dung_bang_thang(btc)), huan_luyen_logistic(btc)
    provenance = {"schema_version": 2, "source": str(DUONG_DAN_DU_LIEU.relative_to(GOC)),
        "source_sha256": hashlib.sha256(DUONG_DAN_DU_LIEU.read_bytes()).hexdigest(),
        "source_size_bytes": DUONG_DAN_DU_LIEU.stat().st_size,
        "source_mtime_ns": DUONG_DAN_DU_LIEU.stat().st_mtime_ns,
        "btc_cutoff": str(btc.index.max().date()), "random_state": 42,
        "python": platform.python_version(),
        "packages": {name: version(name) for name in ["pandas", "numpy", "scikit-learn", "statsmodels"]}}
    for ten, goi in [("tuyen_tinh", tt), ("logistic", lg)]:
        goi["provenance"] = provenance
        with open(THU_MUC_MO_HINH / f"mo_hinh_{ten}.pkl", "wb") as f:
            pickle.dump(goi, f)
    tom_tat = {"schema_version": 2, "tuyen_tinh": tt["chi_so"], "he_so_tuyen_tinh": tt["he_so"],
        "logistic": lg["chi_so"], "ma_tran_nham_lan": lg["ma_tran_nham_lan"],
        "phien_gan_nhat": lg["phien_gan_nhat"], "du_bao_thang_tiep": tt["du_bao_tiep"],
        "phuong_phap": {"tuyen_tinh": tt["phuong_phap"], "logistic": lg["phuong_phap"]},
        "provenance": provenance}
    with open(THU_MUC_MO_HINH / "ket_qua_mo_hinh.json", "w", encoding="utf-8") as f:
        json.dump(tom_tat, f, ensure_ascii=False, indent=2, allow_nan=False)
    tt["bang_du_bao"].to_csv(THU_MUC_MO_HINH / "du_bao_thang_holdout.csv", index=False)
    lg["du_doan_test"].to_csv(THU_MUC_MO_HINH / "du_bao_ngay_holdout.csv", index=False)
    print(json.dumps(tom_tat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
