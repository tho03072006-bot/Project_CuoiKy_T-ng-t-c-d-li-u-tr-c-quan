"""Tien ich dung chung cho cac script tai du lieu."""
from pathlib import Path
import time
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
for _p in (RAW, INTERIM, PROCESSED):
    _p.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "IDV-final-project/1.0 (student research)"}


def get(url, params=None, retries=4, timeout=60, as_json=True):
    """GET co retry va backoff. Tra ve json hoac text."""
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            if r.status_code == 429:          # bi rate-limit -> cho lau hon
                wait = 15 * (i + 1)
                print(f"    429 rate limit, cho {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json() if as_json else r.text
        except Exception as e:
            last = e
            print(f"    loi lan {i+1}/{retries}: {e}")
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"Tai that bai sau {retries} lan: {url}\n{last}")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
