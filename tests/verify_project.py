"""Kiểm tra dữ liệu, định nghĩa tháng và khả năng chạy tất cả trang dashboard."""
from pathlib import Path
import sys
import json
import sqlite3
import unittest
import datetime as dt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dashboard'))
import data_layer as dl
from streamlit.testing.v1 import AppTest


class ProjectChecks(unittest.TestCase):
    def test_dataset_keys_and_missing_labels(self):
        """Không để join nhân dòng hoặc gán nhãn giảm cho ngày chưa có lợi suất."""
        qc = json.loads((ROOT/'data/processed/_quality_checks.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(qc['raw_rows'], 5000)
        self.assertEqual(len(qc['tables']), 7)
        c = dl.nap_crypto_daily()
        self.assertFalse(c.duplicated(['ticker','date']).any())
        self.assertTrue(c.loc[c.daily_return_pct.isna(), 'is_up_day'].isna().all())
        self.assertTrue((dl.nap_macro_daily().us10y_yield.dropna() > 0).all())
        country = dl.nap_country_macro()
        self.assertIn('NA', country.continent.unique())
        self.assertTrue(country.loc[country.inflation_pct.isna(), 'high_inflation'].isna().all())

    def test_months_and_empty_selection(self):
        """Tháng cuối dở dang phải bị loại, tháng 1 giữ lợi suất từ cuối tháng 12."""
        m = dl.bang_thang()
        self.assertEqual(m.thang.max(), pd.Timestamp('2026-04-30'))
        self.assertEqual(m.thang.min(), pd.Timestamp('2018-01-31'))
        self.assertTrue(m.btc_ret.notna().all())
        self.assertEqual(len(m), 100)
        c = dl.nap_crypto_daily().query("ticker == 'BTC'").set_index('date').price_usd
        expected = c.loc['2018-01-31'] / c.loc['2017-12-31'] - 1
        self.assertAlmostEqual(m.iloc[0].btc_ret, expected)
        self.assertTrue(dl.loc_du_lieu('2018-01-01','2026-05-23', []).empty)

    def test_sqlite_matches_csv(self):
        """Kiểm tra bản SQLite được giao có đầy đủ Bắc Mỹ và không hỏng file."""
        con = sqlite3.connect((ROOT/'data/processed/crypto_macro.db').as_uri()+'?mode=ro', uri=True)
        try:
            self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            n = con.execute("SELECT count(*) FROM dim_country WHERE continent='NA'").fetchone()[0]
            self.assertEqual(n, int((dl.nap_dim_country().continent == 'NA').sum()))
            self.assertEqual(con.execute('SELECT count(*) FROM fact_crypto_daily').fetchone()[0], len(dl.nap_crypto_daily()))
        finally:
            con.close()

    def test_every_dashboard_page(self):
        """Kiểm tra entrypoint thực để bắt cả lỗi router, sidebar và các trang con."""
        app = AppTest.from_file(str(ROOT/'dashboard/app.py'), default_timeout=45).run()
        self.assertFalse(app.exception, str(app.exception))
        for page in sorted((ROOT/'dashboard/pages').glob('*.py')):
            with self.subTest(page=page.name):
                app.switch_page('pages/'+page.name).run()
                self.assertFalse(app.exception, str(app.exception))
                self.assertFalse(app.error, str(app.error))
                self.assertGreater(len(app.get('plotly_chart')), 0)

    def test_sidebar_empty_dates_and_short_macro_range(self):
        """Trong lúc xóa/chọn dở khoảng ngày, dashboard vẫn phản hồi có nghĩa."""
        app = AppTest.from_file(str(ROOT/'dashboard/app.py'), default_timeout=45).run()
        app.date_input(key='w_khoang_ngay').set_value(()).run()
        self.assertFalse(app.exception, str(app.exception))
        app.switch_page('pages/3_Vi_mo.py').run()
        app.date_input(key='w_khoang_ngay').set_value((dt.date(2026,5,1),dt.date(2026,5,23))).run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertTrue(app.warning)


if __name__ == '__main__':
    unittest.main(verbosity=2)
