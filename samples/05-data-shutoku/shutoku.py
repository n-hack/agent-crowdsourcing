#!/usr/bin/env python3
"""手元に立てた架空の店舗一覧の頁から、表を CSV に取る小道具（見本）。

使い方:
  python3 -m http.server 8765 --bind 127.0.0.1 --directory site &   # 手元に頁を立てる
  python3 shutoku.py                                                # 正常な回（頁の形が想定どおり）
  python3 shutoku.py http://127.0.0.1:8765/kawatta/index.html       # 頁の形を変えた回（止まる）

作法:
  - 手元（127.0.0.1・localhost）の頁しか取らない。外のサイトの URL を渡すと取らずに止まる
  - 取る前に robots.txt を読み、取ってよいかを見る
  - 「次の頁」をたどり、1頁ごとに1秒空ける
  - 前回の CSV があれば、増えた店と消えた店を出す
止まる形:
  頁の形が変わった（表の class・列の見出しが想定と違う）・行が0・空の欄の多い行が半分を超えた
  → 空の表を出さず、前回の CSV も書き換えずに rc=2 で止まり、理由を出す
rc: 0 = 取れた ／ 2 = 止めた（理由つき）
Python 3 の標準だけで動く。
"""
import argparse
import csv
import datetime
import html.parser
import pathlib
import sys
import time
import urllib.parse
import urllib.request
import urllib.robotparser

KOKO = pathlib.Path(__file__).resolve().parent
TEBURA = {"127.0.0.1", "localhost", "::1"}
HYOU_CLASS = "tenpo-ichiran"
MIDASHI = ["店舗ID", "店舗名", "都道府県", "住所", "営業時間", "定休日"]
UA = "mihon-shutoku/1.0"
MAX_PAGE = 20


class Yomu(html.parser.HTMLParser):
    """頁の中の表（class・見出し・行）と「次の頁」の行き先を拾う。"""

    def __init__(self):
        super().__init__()
        self.hyou = []          # [{"class": str, "midashi": [...], "gyou": [[...], ...]}]
        self.tsugi = None
        self._cell = None
        self._row = None
        self._in_a_tsugi = False

    def handle_starttag(self, tag, attrs):
        at = dict(attrs)
        if tag == "table":
            self.hyou.append({"class": at.get("class", ""), "midashi": [], "gyou": []})
        elif tag == "tr" and self.hyou:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = ""
        elif tag == "a" and "tsugi" in (at.get("class") or "").split():
            self.tsugi = at.get("href")

    def handle_data(self, data):
        if self._cell is not None:
            self._cell += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append((tag, self._cell.strip()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row and all(t == "th" for t, _ in self._row):
                self.hyou[-1]["midashi"] = [c for _, c in self._row]
            elif self._row:
                self.hyou[-1]["gyou"].append([c for _, c in self._row])
            self._row = None


def tomaru(riyuu):
    print(f"🔴 止めた：{riyuu}")
    print("🔴 空の表は出さない・前回の CSV も書き換えない（rc=2）")
    return 2


def toru(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode(r.headers.get_content_charset() or "utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("url", nargs="?", default="http://127.0.0.1:8765/seijou/index.html")
    p.add_argument("-o", "--out", default=str(KOKO / "tenpo_ichiran.csv"))
    a = p.parse_args()

    u = urllib.parse.urlsplit(a.url)
    if u.scheme != "http" or u.hostname not in TEBURA:
        return tomaru(f"手元の頁ではない（{u.hostname}）。この見本は手元に立てた頁しか取らない")

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{u.scheme}://{u.netloc}/robots.txt")
    try:
        rp.read()
    except Exception as e:
        return tomaru(f"robots.txt が読めない（{e}）")
    if not rp.can_fetch(UA, a.url):
        return tomaru("robots.txt で取ってはいけない頁になっている")
    print(f"robots.txt を読んだ：取ってよい（{u.scheme}://{u.netloc}/robots.txt）")

    gyou, url, n = [], a.url, 0
    while url and n < MAX_PAGE:
        if n:
            time.sleep(1)
        try:
            y = Yomu()
            y.feed(toru(url))
        except Exception as e:
            return tomaru(f"頁が取れない（{url}・{e}）")
        n += 1
        hit = [h for h in y.hyou if HYOU_CLASS in h["class"].split()]
        if not hit:
            mieta = "・".join(h["class"] or "（class 無し）" for h in y.hyou) or "表そのものが無い"
            return tomaru(f"頁の形が変わった：class=\"{HYOU_CLASS}\" の表が無い（{url}・見つかった表の class：{mieta}）")
        h = hit[0]
        if h["midashi"] != MIDASHI:
            zure = [f"{i + 1}列目「{x}」→「{y_}」" for i, (x, y_) in enumerate(zip(MIDASHI, h["midashi"])) if x != y_]
            if len(h["midashi"]) != len(MIDASHI):
                zure.append(f"列の数 {len(MIDASHI)} → {len(h['midashi'])}")
            return tomaru(f"頁の形が変わった：列の見出しが想定と違う（{url}・{'／'.join(zure)}）")
        print(f"{n}頁目 {url} … {len(h['gyou'])} 行")
        tori = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        for r in h["gyou"]:
            gyou.append(r + [url, tori])
        url = urllib.parse.urljoin(url, y.tsugi) if y.tsugi else None

    if not gyou:
        return tomaru("行が0（表はあるが中身が無い）")
    sukasu = [r for r in gyou if sum(1 for c in r[:len(MIDASHI)] if not c) > 0]
    if len(sukasu) * 2 > len(gyou):
        return tomaru(f"空の欄がある行が半分を超えた（{len(sukasu)}／{len(gyou)} 行）")
    ids = [r[0] for r in gyou]
    if len(set(ids)) != len(ids):
        return tomaru("店舗ID が重なっている（同じ頁を2回取った恐れ）")

    out = pathlib.Path(a.out)
    mae = None
    if out.exists():
        with out.open(encoding="utf-8-sig", newline="") as f:
            mae = {r["店舗ID"] for r in csv.DictReader(f)}
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(MIDASHI + ["取得元URL", "取得日時"])
        w.writerows(gyou)
    print(f"✅ {n} 頁から {len(gyou)} 行を {out.name} に書いた（空の欄がある行 {len(sukasu)}）")
    if mae is None:
        print("前回の CSV：無し（今回が1回目）")
    else:
        fueta, kieta = sorted(set(ids) - mae), sorted(mae - set(ids))
        print(f"前回との差：増えた {len(fueta)} 店{(' ' + '・'.join(fueta)) if fueta else ''} ／ 消えた {len(kieta)} 店{(' ' + '・'.join(kieta)) if kieta else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
