# PDF の議事録を原文どおりに行へ分けて CSV に書き、2通りの取り出しを1字ずつ突き合わせる（読むだけ・送らない）
# 使い方: python3 pdf2tenki.py <入力.pdf> <出力.csv>
# 取り出し① pdftotext -layout ／ ② pypdf。空白と改行を除いた文字の並びが一致すれば ✅、違えば食い違いの箇所を出す（人の目で原文を見る所）
# 文字が取れない（画像だけの PDF）は 🔴 で止める＝読み取り（OCR）が要る・依頼主の了承の後
import csv, difflib, re, subprocess, sys
from pypdf import PdfReader
src, dst = sys.argv[1], sys.argv[2]
import os
if not os.path.isfile(src): print('🔴 入力の PDF が無い:', src); sys.exit(2)
a = subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', src, '-'], capture_output=True, text=True).stdout
b = '\n'.join((p.extract_text() or '') for p in PdfReader(src).pages)
import unicodedata
# 7号 11/04：pypdf は「見・日・月」を形の似た部首の字（⾒・⽇・⽉）で返すことがある＝中身でなく符号の違い → 比べる前に NFKC でそろえる（CSV に書く①の本文はそろえない）
sq = lambda s: re.sub(r'\s+', '', unicodedata.normalize('NFKC', s))
if len(sq(a)) < 10:
    print('🔴 文字が取れない（画像だけの PDF の見込み）＝読み取り（OCR）が要る'); sys.exit(3)
lines = [l.rstrip() for l in a.replace('\f', '\n').split('\n')]
with open(dst, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['行', '本文'])
    for i, l in enumerate([l for l in lines if l.strip()], 1): w.writerow([i, l.strip()])
x, y = sq(a), sq(b)
# 日本語・英数・記号以外の字が多い側は文字の対応表が壊れている（11/04 試し：pypdf が日本語を別の文字に化けさせた）
ok = lambda s: sum(1 for c in s if ord(c) < 0x2000 and ord(c) < 0x0500 or 0x3000 <= ord(c) <= 0x9FFF or 0xFF00 <= ord(c) <= 0xFFEF) / max(1, len(s))
if ok(y) < 0.9 <= ok(x):
    print(f'文字数 ①{len(x)} ②{len(y)} ／ 行 {sum(1 for l in lines if l.strip())} → {dst}')
    print(f'🟡 ②（pypdf）は文字が化けている（正しい字の割合 {ok(y):.2f}）＝突き合わせに使えない。①だけで書いた → 原文と目で1字ずつ照合する'); sys.exit(1)
print(f'文字数 ①{len(x)} ②{len(y)} ／ 行 {sum(1 for l in lines if l.strip())} → {dst}')
if x == y: print('✅ 2通りの取り出しが1字も違わない'); sys.exit(0)
sm = difflib.SequenceMatcher(None, x, y, autojunk=False); bad = [o for o in sm.get_opcodes() if o[0] != 'equal']
print(f'🟡 食い違い {len(bad)} か所（一致率 {sm.ratio():.4f}）＝原文を目で見て決める')
for t, i1, i2, j1, j2 in bad[:20]: print(f'  {t} ①「{x[max(0,i1-8):i2+8]}」 ②「{y[max(0,j1-8):j2+8]}」')
sys.exit(1)
