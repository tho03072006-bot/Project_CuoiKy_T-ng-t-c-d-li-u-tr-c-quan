# -*- coding: utf-8 -*-
"""Kiểm thử các rủi ro thật: leakage, tháng dở dang, lịch thiếu, artifact cũ.

Chạy từ thư mục gốc: python -m unittest discover -s models -p "test_*.py" -v
"""
import hashlib
import json
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

import du_bao as m


class TestDuBaoTheoThoiGian(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Nạp dữ liệu thật một lần để các test cùng dùng đúng cutoff dự án."""
        df = pd.read_csv(m.DUONG_DAN_DU_LIEU, parse_dates=["date"])
        cls.btc = df.loc[df.ticker.eq("BTC")].set_index("date").sort_index()
        cls.bang = m.dung_bang_thang(cls.btc)
        cls.tt = m.huan_luyen_tuyen_tinh(cls.bang)
        cls.lg = m.huan_luyen_logistic(cls.btc)

    def test_thang_chua_hoan_tat_khong_thanh_nhan(self):
        """Biến tháng dở dang thành giá cực đoan vẫn không đổi model tháng."""
        cutoff = self.bang.thang.max()
        self.assertTrue(cutoff.is_month_end)
        self.assertLessEqual(cutoff, self.btc.index.max())
        x = self.btc.copy()
        x.loc[x.index > cutoff, "price_usd"] *= 100
        assert_frame_equal(m.dung_bang_thang(x), self.bang)
        features, _ = m.chuan_bi_du_lieu_tuyen_tinh(self.bang)
        self.assertEqual(features.index.min(), pd.Timestamp("2018-01-31"))

    def test_thay_doi_tuong_lai_khong_doi_dac_trung_qua_khu(self):
        """Perturb giá từ một ngày không được đổi đặc trưng đến chính ngày đó."""
        moc = pd.Timestamp("2025-01-15")
        x1, _ = m.chuan_bi_du_lieu_logistic(self.btc)
        doi = self.btc.copy()
        doi.loc[moc:, ["price_usd", "volume_usd", "market_cap_usd"]] *= 3
        x2, _ = m.chuan_bi_du_lieu_logistic(doi)
        assert_frame_equal(x1.loc[:moc], x2.loc[:moc])
        self.assertFalse(x1.loc[moc + pd.Timedelta(days=1):].equals(x2.loc[moc + pd.Timedelta(days=1):]))

    def test_logistic_train_khong_doc_holdout(self):
        """Sửa mạnh holdout phải giữ nguyên scaler và hệ số đã học trên train."""
        doi = self.btc.copy()
        doi.loc["2024":, "price_usd"] *= np.linspace(0.5, 4, len(doi.loc["2024":]))
        khac = m.huan_luyen_logistic(doi)
        for step, thuoc_tinh in [("chuan_hoa", "mean_"), ("chuan_hoa", "scale_"), ("logistic", "coef_")]:
            np.testing.assert_array_equal(getattr(self.lg["mo_hinh"].named_steps[step], thuoc_tinh),
                                          getattr(khac["mo_hinh"].named_steps[step], thuoc_tinh))

    def test_ols_chon_bien_va_fit_khong_doc_holdout(self):
        """Cả VIF lẫn hệ số phải giữ nguyên khi holdout thay đổi."""
        doi = self.bang.copy()
        holdout = doi.thang.dt.year >= 2024
        doi.loc[holdout, ["btc_ret", *m.BIEN_GOC]] *= 4
        khac = m.huan_luyen_tuyen_tinh(doi)
        self.assertEqual(self.tt["ten_bien"], khac["ten_bien"])
        self.assertEqual(self.tt["nhat_ky_vif"], khac["nhat_ky_vif"])
        assert_series_equal(self.tt["ket_qua"].params, khac["ket_qua"].params)

    def test_mat_ngay_khong_ep_lag_thanh_mot_phien(self):
        """Một ngày mất phải loại target ngày sau; không nối chuỗi qua lỗ trống."""
        mat = pd.Timestamp("2024-06-15")
        x, y = m.chuan_bi_du_lieu_logistic(self.btc.drop(index=mat))
        self.assertNotIn(mat, y.index)
        self.assertNotIn(mat + pd.Timedelta(days=1), y.index)
        self.assertNotIn(mat + pd.Timedelta(days=1), x.index)
        bang = m.dung_bang_thang(self.btc.drop(index=mat)).set_index("thang")
        self.assertTrue(pd.isna(bang.loc["2024-06-30", "btc_ret"]))
        self.assertTrue(pd.isna(bang.loc["2024-07-31", "btc_ret"]))

    def test_forecast_thuc_su_nam_sau_cutoff(self):
        """Forecast ngày tới dùng đặc trưng ngày cuối, không lấy dự đoán test cuối."""
        phien = self.lg["phien_gan_nhat"]
        self.assertEqual(pd.Timestamp(phien["ngay"]), self.btc.index.max() + pd.Timedelta(days=1))
        cuoi = m._dac_trung_ngay(self.btc).iloc[[-1]]
        self.assertEqual(phien["xac_suat_tang"], self.lg["mo_hinh_refit"].predict_proba(cuoi)[0, 1])
        tt = self.tt["du_bao_tiep"]
        self.assertGreater(pd.Timestamp(tt["thang"]), self.btc.index.max())
        self.assertEqual(pd.Timestamp(tt["ngay_thong_tin"]), self.bang.thang.max())

    def test_metrics_baseline_va_split(self):
        """Kiểm chứng metrics độc lập từ từng dự đoán đã xuất, đúng tập holdout."""
        d = self.tt["bang_du_bao"]
        self.assertTrue((d.thang.dt.year >= 2024).all())
        self.assertEqual(len(d), self.tt["chi_so"]["n_test"])
        self.assertAlmostEqual(np.sqrt(np.mean(d.loi_suat_thuc**2)), self.tt["chi_so"]["rmse_co_so"])
        self.assertAlmostEqual(np.sqrt(np.mean((d.loi_suat_thuc-d.loi_suat_du_bao)**2)), self.tt["chi_so"]["rmse_test"])
        ngay = self.lg["du_doan_test"]
        nhan = int(self.lg["chi_so"]["ty_le_tang_train"] >= 0.5)
        self.assertTrue(ngay.du_doan_co_so.eq(nhan).all())
        self.assertAlmostEqual(ngay.thuc_te.eq(ngay.du_doan_co_so).mean(), self.lg["chi_so"]["accuracy_co_so"])

    def test_artifact_tai_lap_dung_nguon(self):
        """Artifact giao nộp phải khớp dữ liệu hiện tại và lần fit độc lập."""
        j = json.loads((m.THU_MUC_MO_HINH / "ket_qua_mo_hinh.json").read_text(encoding="utf-8"))
        self.assertEqual(j["schema_version"], 2)
        self.assertEqual(j["provenance"]["source_sha256"], hashlib.sha256(m.DUONG_DAN_DU_LIEU.read_bytes()).hexdigest())
        self.assertEqual(j["tuyen_tinh"], self.tt["chi_so"])
        self.assertEqual(j["logistic"], self.lg["chi_so"])
        self.assertEqual(j["phien_gan_nhat"], self.lg["phien_gan_nhat"])


if __name__ == "__main__":
    unittest.main()
