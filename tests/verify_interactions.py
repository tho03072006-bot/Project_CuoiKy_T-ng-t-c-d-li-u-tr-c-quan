# -*- coding: utf-8 -*-
"""Regression tests cho bộ lọc và drill-down của ba trang dashboard.

Chạy từ thư mục project:
    .venv\Scripts\python.exe tests\verify_interactions.py

AppTest kiểm tra trạng thái Python và widget. Click/hover thực của Plotly cần
kiểm tra thêm trên trình duyệt; test không giả vờ mô phỏng sự kiện DOM đó.
"""
from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dashboard"))
import data_layer as dl


class InteractionRegressionTests(unittest.TestCase):
    """Giữ các lỗi từng gặp không quay lại khi sửa dashboard."""

    @classmethod
    def setUpClass(cls):
        """Lấy mốc ngày và ngưỡng thử từ dữ liệu để không cố định số liệu thị trường."""
        cls.crypto = dl.nap_crypto_daily()
        cls.last_date = cls.crypto["date"].max().date()
        cls.filters = {
            "tu_ngay": date(2018, 1, 1),
            "den_ngay": cls.last_date,
            "danh_sach_coin": ["BTC", "ETH"],
            "nhom_coin": dl.NHOM_TAT_CA,
            "von_hoa_toi_thieu": 0.0,
        }

    def page(self, filename, **updates):
        """Harness cung cấp đúng hợp đồng bo_loc, không phụ thuộc navigation của app."""
        source = (
            "import sys, runpy\n"
            f"sys.path.insert(0, {str(ROOT / 'dashboard')!r})\n"
            "from style import dang_ky_template\n"
            "dang_ky_template()\n"
            f"runpy.run_path({str(ROOT / 'dashboard' / 'pages' / filename)!r}, run_name='__main__')\n"
        )
        app = AppTest.from_string(source, default_timeout=45)
        app.session_state["bo_loc"] = {**self.filters, **updates}
        app.run()
        self.assert_clean(app)
        return app

    def assert_clean(self, app):
        """Thông báo exception giữ nguyên nội dung để lỗi dễ lần theo khi chạy CLI."""
        self.assertFalse(list(app.exception), [error.message for error in app.exception])

    def select(self, app, label, value):
        """Tìm theo nhãn ổn định vì khóa map đổi theo cấp/năm/chỉ số để bỏ selection cũ."""
        next(widget for widget in app.selectbox if widget.label == label).select(value).run()
        self.assert_clean(app)

    def click(self, app, label):
        """Nút có nhãn cố định nên test không lệ thuộc thứ tự bố cục."""
        next(widget for widget in app.button if widget.label == label).click().run()
        self.assert_clean(app)

    def test_overview_single_day_and_empty_selection(self):
        app = self.page("1_Tong_quan.py", tu_ngay=self.last_date)
        btc_metric = next(metric for metric in app.metric if metric.label == "Giá BTC")
        self.assertIn("30 ngày", btc_metric.delta)
        btc = self.crypto[self.crypto["ticker"] == "BTC"].sort_values("date")
        latest = btc.iloc[-1]
        previous = btc[btc["date"] <= latest["date"] - pd.Timedelta(days=30)].iloc[-1]
        expected = (latest["price_usd"] / previous["price_usd"] - 1) * 100
        from style import so_viet
        self.assertIn(so_viet(expected), btc_metric.delta)
        self.assertEqual(len(app.get("plotly_chart")), 1)
        app.session_state["bo_loc"] = {**self.filters, "danh_sach_coin": []}
        app.run()
        self.assert_clean(app)
        self.assertEqual(len(app.get("plotly_chart")), 0)
        self.assertTrue(list(app.warning))

    def test_market_none_means_all_and_empty_means_no_price_charts(self):
        app = self.page("2_Thi_truong.py", danh_sach_coin=None)
        chart = json.loads(app.get("plotly_chart")[0].proto.spec)
        self.assertEqual({trace["name"] for trace in chart["data"]}, {"Đang chọn"})
        self.assertGreater(len(app.selectbox[0].options), 2)
        app.session_state["bo_loc"] = {**self.filters, "danh_sach_coin": []}
        app.run()
        self.assert_clean(app)
        self.assertEqual(len(app.selectbox), 0)
        self.assertEqual(len(app.get("plotly_chart")), 3)  # Chỉ ba chart ngữ cảnh còn lại.

    def test_market_linked_state_and_clear_button(self):
        app = self.page("2_Thi_truong.py")
        # AppTest chưa điều khiển click Plotly: đặt kết quả callback để thử hai chart đích.
        app.session_state["chon_coin_bar"] = ["ETH"]
        app.run()
        self.assert_clean(app)
        self.assertEqual(app.selectbox[0].options, ["ETH"])
        self.assertEqual(app.selectbox[0].value, "ETH")
        self.click(app, "Bỏ chọn biểu đồ")
        self.assertEqual(app.session_state["chon_coin_bar"], [])
        self.assertEqual(app.selectbox[0].options, ["BTC", "ETH"])

    def test_market_empty_filters_clear_stale_cross_selection(self):
        app = self.page("2_Thi_truong.py")
        app.session_state["chon_coin_bar"] = ["ETH"]
        app.session_state["bo_loc"] = {
            **self.filters, "von_hoa_toi_thieu": float(self.crypto["market_cap_usd"].max() * 2)
        }
        app.run()
        self.assert_clean(app)
        self.assertEqual(app.session_state["chon_coin_bar"], [])
        app.session_state["bo_loc"] = {**self.filters, "danh_sach_coin": ["BTC"]}
        app.run()
        self.assert_clean(app)
        self.assertEqual(app.selectbox[0].options, ["BTC"])
        app.session_state["bo_loc"] = {**self.filters, "tu_ngay": self.last_date}
        app.run()
        self.assert_clean(app)
        self.assertTrue(any("hai phiên" in note.value for note in app.info))

    def test_treemap_empty_latest_snapshot_is_explained(self):
        market = dl.nap_market_daily()
        latest_max = market.loc[market["date"] == market["date"].max(), "market_cap_usd"].max()
        historical_max = self.crypto["market_cap_usd"].max()
        self.assertGreater(historical_max, latest_max, "Fixture cần có đỉnh cũ cao hơn ngày cuối.")
        threshold = float((latest_max + historical_max) / 2)
        app = self.page("2_Thi_truong.py", von_hoa_toi_thieu=threshold)
        self.assertTrue(any("Không có coin đủ ngưỡng vốn hoá" in note.value for note in app.info))
        self.assertEqual(len(app.get("plotly_chart")), 4)

    def test_map_north_america_country_back_and_world(self):
        app = self.page("4_Ban_do.py")
        self.select(app, "Đi tới châu lục", "NA")
        chart = json.loads(app.get("plotly_chart")[0].proto.spec)
        self.assertIn("USA", chart["data"][0]["locations"])
        self.select(app, "Đi tới quốc gia", "USA")
        self.assertEqual(app.session_state["bando_cap"], "quoc_gia")
        self.click(app, "Quay lại")
        self.assertEqual(app.session_state["bando_cap"], "chau_luc")
        self.assertIsNone(app.session_state["bando_quoc_gia"])
        self.click(app, "Về toàn cầu")
        self.assertEqual(app.session_state["bando_cap"], "toan_cau")
        self.assertIsNone(app.session_state["bando_chau"])
        app.run()  # Rerun thường cũng không được khôi phục vùng chọn cũ.
        self.assert_clean(app)
        self.assertEqual(app.session_state["bando_cap"], "toan_cau")

    def test_map_clearing_selectors_returns_to_parent(self):
        app = self.page("4_Ban_do.py")
        self.select(app, "Đi tới châu lục", "NA")
        self.select(app, "Đi tới quốc gia", "USA")
        self.select(app, "Đi tới quốc gia", "— chọn —")
        self.assertEqual(app.session_state["bando_cap"], "chau_luc")
        self.select(app, "Đi tới châu lục", "— chọn —")
        self.assertEqual(app.session_state["bando_cap"], "toan_cau")

    def test_map_metric_continent_matrix_and_year_change(self):
        app = self.page("4_Ban_do.py")
        for metric in ["inflation_pct", "gdp_per_capita_usd", "population"]:
            self.select(app, "Chỉ số hiển thị", metric)
            for continent in ["NA", "OC", "SA", "AF", "AS", "EU"]:
                with self.subTest(metric=metric, continent=continent):
                    self.select(app, "Đi tới châu lục", continent)
                    self.assertEqual(app.session_state["bando_cap"], "chau_luc")
                    self.assertEqual(len(app.get("plotly_chart")), 2)
                    self.click(app, "Về toàn cầu")
                    self.assertEqual(app.session_state["bando_cap"], "toan_cau")
        last_year = int(dl.nap_country_macro()["year"].max())
        app.select_slider[0].set_value(last_year).run()
        self.assert_clean(app)
        self.assertEqual(app.session_state["bando_cap"], "toan_cau")


if __name__ == "__main__":
    unittest.main(verbosity=2)
