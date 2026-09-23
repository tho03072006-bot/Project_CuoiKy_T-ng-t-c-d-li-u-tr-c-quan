"""Dựng SQLite từ CSV, kiểm tra rồi thay file nguyên tử để không làm hỏng bản đang dùng."""
import argparse
import os
from pathlib import Path
import sqlite3
import tempfile
import sys
from contextlib import closing

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
TABLE_KEYS = {
    "fact_crypto_daily": ["ticker", "date"],
    "fact_market_daily": ["ticker", "date"],
    "fact_macro_daily": ["date"],
    "fact_country_macro": ["iso3", "year"],
    "fact_fx_daily": ["country_fx", "date"],
    "dim_coin": ["ticker"], "dim_country": ["iso3"],
}


def build_database(processed, destination):
    """Dựng ở cùng ổ đĩa để os.replace nguyên tử; lỗi build giữ nguyên DB cũ."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="crypto_macro_", suffix=".db", dir=destination.parent)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(temporary)) as connection:
            for name, key in TABLE_KEYS.items():
                source = processed / f"{name}.csv"
                if not source.exists():
                    source = processed / f"{name}.csv.gz"
                # NA và mã nước NA (Namibia) là mã thật; chỉ ô rỗng mới là missing.
                # UTF-8-SIG ổn với Windows và tránh lỗi ký tự lạ khi đọc file CSV đã export.
                frame = pd.read_csv(
                    source,
                    keep_default_na=False,
                    na_values=[""],
                    encoding="utf-8-sig",
                )
                if frame[key].isna().any().any() or frame.duplicated(key).any():
                    raise ValueError(f"Khóa thiếu hoặc trùng trong {name}")
                frame.to_sql(name, connection, if_exists="replace", index=False)
                columns = ", ".join(key)
                connection.execute(f"CREATE UNIQUE INDEX ix_{name} ON {name}({columns})")
                actual = connection.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
                if actual != len(frame):
                    raise ValueError(f"Sai số dòng khi ghi {name}")
                print(f"  {name:<22} {actual:>9,} dòng")
            connection.execute("CREATE INDEX ix_crypto_date ON fact_crypto_daily(date)")
            connection.commit()
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("SQLite integrity_check không đạt")
            countries = pd.read_csv(processed / "dim_country.csv", keep_default_na=False, na_values=[""])
            expected_na = int(countries.continent.eq("NA").sum())
            actual_na = connection.execute("SELECT count(*) FROM dim_country WHERE continent='NA'").fetchone()[0]
            if expected_na != actual_na:
                raise ValueError("SQLite làm mất mã châu lục Bắc Mỹ")
        # Không sửa/xóa journal của DB đang mở: SQLite phải tự quản lý giao dịch.
        # Windows từ chối thay file bị khóa; khi đó DB cũ vẫn nguyên vẹn.
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"\nXong -> {destination} ({destination.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--dest", type=Path)
    args = parser.parse_args()
    build_database(args.processed.resolve(), (args.dest or args.processed / "crypto_macro.db").resolve())
