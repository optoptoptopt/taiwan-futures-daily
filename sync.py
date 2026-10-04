"""從 acaiprotocol.com 抓最新 CSV 覆蓋 data/。抓到的檔案不對勁就不覆蓋 (保留舊檔、排程亮紅燈)。

檢查: HTTP 200、開頭是 UTF-8 BOM、欄位列跟現有檔一樣、筆數不比現有少、最後日期不早於現有。
"""
import sys
import urllib.request
from pathlib import Path

SITE = "https://acaiprotocol.com/data/"
DATA = Path(__file__).parent / "data"


def check(name, new):
    old_path = DATA / name
    if not new.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{name}: 不是 UTF-8 BOM 開頭, 可能抓到錯誤頁")
    nl = new.decode("utf-8-sig").strip().splitlines()
    if old_path.exists():
        ol = old_path.read_bytes().decode("utf-8-sig").strip().splitlines()
        if nl[0] != ol[0]:
            raise ValueError(f"{name}: 欄位變了\n舊 {ol[0]}\n新 {nl[0]}")
        if len(nl) < len(ol):
            raise ValueError(f"{name}: 筆數變少 {len(ol) - 1} -> {len(nl) - 1}")
        if nl[-1][:10] < ol[-1][:10]:
            raise ValueError(f"{name}: 最後日期倒退 {ol[-1][:10]} -> {nl[-1][:10]}")
    return len(nl) - 1, nl[-1][:10]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    bad = 0
    for name in ("chips_daily.csv", "basis_daily.csv"):
        try:
            req = urllib.request.Request(SITE + name, headers={"User-Agent": "taiwan-futures-daily-sync"})
            with urllib.request.urlopen(req, timeout=60) as r:
                new = r.read()
            n, last = check(name, new)
            (DATA / name).write_bytes(new)
            print(f"{name}: {n} 筆, 最新 {last}")
        except Exception as e:
            bad += 1
            print(f"{name}: 沒更新 ({e})")
    sys.exit(1 if bad else 0)
