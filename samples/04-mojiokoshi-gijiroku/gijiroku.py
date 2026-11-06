#!/usr/bin/env python3
"""文字起こし（whisper の JSON）から議事録を作り、台本の正解と照らして拾えた数を数える。

使い方:
  python3 gijiroku.py mojiokoshi/kaigi.json            # gijiroku.md と jikoku.txt を書き、数を出す
  python3 gijiroku.py mojiokoshi/kaigi.json --yougo yougo.json   # 用語の直し表を当ててから抜き出す
  python3 gijiroku.py 別の.json -o 別の議事録.md

抜き出しは文字起こしの文だけを見て行う（台本の正解 kotae は数えるときだけ使う）。
  決まったこと … 「決定」「決めます」「決まりました」を含む文
  宿題 ………… 「◯◯さん」と「◯月◯日までに」を両方含む文（担当＝さんの前の名前・期限＝日付）
rc: 0 = 決まったこと・宿題とも全部拾えた ／ 1 = 拾えなかった物がある ／ 2 = 入力が読めない
Python 3 の標準だけで動く。
"""
import argparse
import difflib
import json
import pathlib
import re
import sys
import unicodedata

KOKO = pathlib.Path(__file__).resolve().parent
KANSUJI = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def kansuji(s):
    """十一・二十二 などの小さな漢数字を算用数字に（日付だけに使う）。"""
    if s.isdigit():
        return int(s)
    n = 0
    if "十" in s:
        a, _, b = s.partition("十")
        n = (KANSUJI.get(a, 1) if a else 1) * 10 + (KANSUJI.get(b, 0) if b else 0)
    else:
        n = KANSUJI.get(s, 0)
    return n


def seiki(t):
    t = unicodedata.normalize("NFKC", t)
    t = re.sub(r"(?<=\d),(?=\d{3})", "", t)  # 2,000 → 2000
    return t.strip()


def bun_ni_wakeru(segments):
    """区間をつないで文（。？！で切る）にし、文の始まりの時刻を付ける。"""
    out, buf, t0 = [], "", None
    for sg in segments:
        txt = seiki(sg.get("text", ""))
        if not txt:
            continue
        if t0 is None:
            t0 = sg.get("start", 0.0)
        for ch in txt:
            buf += ch
            if ch in "。？！?!":
                if buf.strip("。？！?! "):
                    out.append((t0, buf.strip()))
                buf, t0 = "", sg.get("start", 0.0)
        if not buf:
            t0 = None
    if buf.strip():
        out.append((t0 or 0.0, buf.strip()))
    return out


KIMETA = re.compile(r"決定|決めます|決まりました")
HIDUKE = re.compile(r"([0-9〇一二三四五六七八九十]{1,3})月([0-9〇一二三四五六七八九十]{1,3})日までに")
SAN = re.compile(r"([一-龥々]{1,3})さん")


def nukidasu(bunlist):
    kimatta, shukudai = [], []
    for t, b in bunlist:
        if KIMETA.search(b):
            kimatta.append({"jikoku": t, "bun": b})
        m, n = HIDUKE.search(b), SAN.search(b)
        if m and n:
            kigen = f"{kansuji(m.group(1)):02d}-{kansuji(m.group(2)):02d}"
            naiyou = SAN.sub("", b, count=1).lstrip("、 ")
            shukudai.append({"jikoku": t, "tantou": n.group(1), "kigen": kigen, "bun": naiyou})
    return kimatta, shukudai


def au(go, bun):
    return all(re.search(g, bun) for g in go)


def kazoeru(kotae, kimatta, shukudai):
    k_hit, h_hit, used_k, used_h = [], [], set(), set()
    for k in kotae["kimatta"]:
        i = next((i for i, x in enumerate(kimatta) if i not in used_k and au(k["go"], x["bun"])), None)
        if i is not None:
            used_k.add(i)
        k_hit.append((k, i))
    for h in kotae["shukudai"]:
        i = next((i for i, x in enumerate(shukudai) if i not in used_h and au(h["go"], x["bun"])
                  and x["tantou"] == h["tantou"] and x["kigen"] == h["kigen"]), None)
        if i is not None:
            used_h.add(i)
        h_hit.append((h, i))
    yobun_k = [x for i, x in enumerate(kimatta) if i not in used_k]
    yobun_h = [x for i, x in enumerate(shukudai) if i not in used_h]
    return k_hit, h_hit, yobun_k, yobun_h


def chigai(daihon_text, moji_text, n=5):
    """台本と文字起こしを、句読点と空白を除いた字で並べ、違った所を数える。"""
    def kezuru(s):
        return re.sub(r"[\s、。，．,.？！?!「」]", "", seiki(s))
    a, b = kezuru(daihon_text), kezuru(moji_text)
    ops = [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o[0] != "equal"]
    rei = [(a[i1:i2] or "（無し）", b[j1:j2] or "（無し）") for _, i1, i2, j1, j2 in ops]
    kazu = {}
    for r in rei:
        kazu[r] = kazu.get(r, 0) + 1
    ooi = sorted(kazu.items(), key=lambda x: -x[1])[:n]
    return len(ops), len(a), ooi, rei


def mmss(t):
    t = int(t or 0)
    return f"{t // 60:02d}:{t % 60:02d}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("json", help="whisper の JSON（segments に start・text がある物）")
    p.add_argument("--daihon", default=str(KOKO / "daihon.json"))
    p.add_argument("--yougo", default=None, help="用語の直し表（誤った形→正しい語）。当てた数を出す")
    p.add_argument("-o", "--out", default=None, help="議事録の書き先（既定は JSON と同じ名前の .md を gijiroku/ に）")
    a = p.parse_args()

    try:
        moji = json.loads(pathlib.Path(a.json).read_text(encoding="utf-8"))
        segs = moji["segments"]
        daihon = json.loads(pathlib.Path(a.daihon).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"🔴 入力が読めない：{e}", file=sys.stderr)
        return 2

    naoshita = []
    if a.yougo:
        try:
            hyou = json.loads(pathlib.Path(a.yougo).read_text(encoding="utf-8"))["naoshi"]
        except Exception as e:
            print(f"🔴 用語の直し表が読めない：{e}", file=sys.stderr)
            return 2
        segs = [dict(s) for s in segs]
        for ayamari, tadashii in hyou:
            n = sum(s.get("text", "").count(ayamari) for s in segs)
            for s in segs:
                s["text"] = s.get("text", "").replace(ayamari, tadashii)
            naoshita.append((ayamari, tadashii, n))

    bunlist = bun_ni_wakeru(segs)
    kimatta, shukudai = nukidasu(bunlist)
    k_hit, h_hit, yobun_k, yobun_h = kazoeru(daihon["kotae"], kimatta, shukudai)

    stem = pathlib.Path(a.json).stem
    out = pathlib.Path(a.out) if a.out else KOKO / "gijiroku" / f"{stem}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    jikoku = out.with_suffix(".jikoku.txt")
    jikoku.write_text("".join(f"[{mmss(s.get('start'))}] {seiki(s.get('text', ''))}\n" for s in segs), encoding="utf-8")

    owari = max((s.get("end", 0) for s in segs), default=0)
    L = [f"# 議事録（見本・架空の会議）", "",
         "見本として作った物です。会議・会社・人の名前はすべて架空で、OS の読み上げの声で作った音声を文字起こしした物から、機械で作りました。", "",
         f"- 会議：{daihon['kaigi']}",
         f"- 出席：{'・'.join(daihon['koe'].keys())}（台本の登場人物・3人）",
         f"- 長さ：{mmss(owari)}",
         "", "## 決まったこと", "", "| # | 時刻 | 中身 |", "|---|---|---|"]
    for i, x in enumerate(kimatta, 1):
        L.append(f"| {i} | {mmss(x['jikoku'])} | {x['bun']} |")
    L += ["", "## 宿題", "", "| # | 担当 | 期限 | 中身 | 時刻 |", "|---|---|---|---|---|"]
    for i, x in enumerate(shukudai, 1):
        m, d = x["kigen"].split("-")
        L.append(f"| {i} | {x['tantou']} | {int(m)}月{int(d)}日 | {x['bun']} | {mmss(x['jikoku'])} |")
    jikai = [b for _, b in bunlist if "次回" in b]
    L += ["", "## 次回", "", *(f"- {b}" for b in jikai), ""]
    out.write_text("\n".join(L), encoding="utf-8")

    nk = sum(1 for _, i in k_hit if i is not None)
    nh = sum(1 for _, i in h_hit if i is not None)
    if a.yougo:
        print("用語の直し：" + "・".join(f"「{x}」→「{y}」{n}か所" for x, y, n in naoshita))
    else:
        print("用語の直し：当てていない（--yougo 無し）")
    print(f"文字起こし {len(segs)} 区間 → 文 {len(bunlist)} 本 ／ 抜き出し：決まったこと {len(kimatta)} 件・宿題 {len(shukudai)} 件")
    print(f"決まったこと {len(k_hit)} 個中 {nk} 個 拾えた")
    for k, i in k_hit:
        print(f"  {'✅' if i is not None else '🔴'} {k['id']} {k['naiyou']}")
    print(f"宿題 {len(h_hit)} 個中 {nh} 個 拾えた（中身・担当・期限が3つとも合った物だけ数える）")
    for h, i in h_hit:
        m, d = h["kigen"].split("-")
        print(f"  {'✅' if i is not None else '🔴'} {h['id']} {h['tantou']}・{int(m)}月{int(d)}日・{h['naiyou']}")
    print(f"正解に無いのに拾った物：決まったこと {len(yobun_k)} 件・宿題 {len(yobun_h)} 件")
    for x in yobun_k + yobun_h:
        print(f"  🟡 {x['bun']}")

    daihon_text = "".join(s["bun"] for s in daihon["serifu"])
    nchigai, nmoji, rei, _ = chigai(daihon_text, "".join(s.get("text", "") for s in segs))
    print(f"台本との違い：{nchigai} か所（台本 {nmoji} 字・句読点と空白を除いて字で並べた・多い順に5種）")
    for (x, y), c in rei:
        print(f"  台本「{x}」→ 文字起こし「{y}」 {c}か所")
    print(f"書いた物：{out.relative_to(KOKO) if out.is_relative_to(KOKO) else out}・{jikoku.name}")
    return 0 if nk == len(k_hit) and nh == len(h_hit) else 1


if __name__ == "__main__":
    sys.exit(main())
