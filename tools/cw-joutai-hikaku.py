#!/usr/bin/env python3
"""【返事の見張り】CW の応募一覧の控え2枚（cw-oubo-joutai.cjs の tsv）を比べ、状態が変わった行・増えた行・消えた行を出す（読むだけ）
入力: 前の tsv・後の tsv（突き合わせは 題名の末尾「のお仕事(…)」を外した題名＋クライアント）
出力: 変わった・増えた・消えた行。--naru のときは「応募・スカウト」「辞退」以外に変わった行・その状態で増えた行だけ（契約・条件交渉など）
止まる条件: --naru で1件でも出たら rc=1（お知らせ・メールが来なくても決まったことを拾う）
呼び方: python3 tools/cw-joutai-hikaku.py [--naru] <前の tsv> <後の tsv>
"""
import csv, re, sys
NARU = '--naru' in sys.argv; sys.argv = [x for x in sys.argv if x != '--naru']
if len(sys.argv) != 3:
    print(__doc__.strip().split('\n')[-1]); sys.exit(2)


def load(f):
    r = list(csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'))
    k = lambda x: (re.sub(r'のお仕事\(.*?\)$', '', x['タイトル']).strip(), x['クライアント'].strip())
    return {k(x): x for x in r}, len(r)


a, na = load(sys.argv[1]); b, nb = load(sys.argv[2])
if NARU:
    hit = [f'状態 {a[k]["状態"]} → {b[k]["状態"]} | {k[1]} | {k[0][:60]}' for k in a.keys() & b.keys() if a[k]['状態'] != b[k]['状態'] and b[k]['状態'] not in ('応募・スカウト', '辞退')]
    hit += [f'状態 （新しい行）→ {b[k]["状態"]} | {k[1]} | {k[0][:60]}' for k in b.keys() - a.keys() if b[k]['状態'] not in ('応募・スカウト', '辞退')]
    [print(x) for x in hit]; sys.exit(1 if hit else 0)
print(f'前 {na} 行（重複を除いて {len(a)}）／ 後 {nb} 行（重複を除いて {len(b)}）')
ch = [(k, a[k]['状態'], b[k]['状態']) for k in a.keys() & b.keys() if a[k]['状態'] != b[k]['状態']]
print(f'状態が変わった {len(ch)}'); [print(f'  {s1} → {s2} | {k[1]} | {k[0][:50]}') for k, s1, s2 in ch]
new = b.keys() - a.keys(); print(f'増えた {len(new)}'); [print(f'  {b[k]["状態"]} | {k[1]} | {k[0][:50]}') for k in new]
gone = a.keys() - b.keys(); print(f'消えた {len(gone)}'); [print(f'  {a[k]["状態"]} | {k[1]} | {k[0][:50]}') for k in gone]
