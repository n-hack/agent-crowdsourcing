#!/usr/bin/env python3
"""【出し漏れの検算】応募の記録と下書きの置き場を突き合わせ、「出すと決めたのに出ていない」案件を数える（読むだけ）
入力: <置き場>/oubo-kiroku.tsv・<置き場>/oubo-bun/（cw-ID・lancers-ID・teian-ID の .txt）・<置き場>/dashi-zumi.tsv（相手の表示で済・終了と確かめた ID・oubo-zumi-kakunin.cjs の出力）
出力: 出し漏れの一覧（ID ごとに一番新しい行が「止まった／保留」・または下書きがあるのに出した行も見送りの行も無い）と、「オーナー待ち」と書いた行（数えるが鳴らさない）
止まる条件: オーナー待ち以外の出し漏れが1件以上で rc=1
呼び方: python3 tools/dashi-more.py（相手のサイトに本当に届いたかは見ていない＝oubo-zumi-kakunin.cjs で照らす）
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settei as S
S.mon()
BUN = S.DATA / 'oubo-bun'; ZUMI = S.DATA / 'dashi-zumi.tsv'
zumi = {l.split('\t')[0] for l in open(ZUMI, encoding='utf-8') if l.count('\t') >= 2 and l.split('\t')[2] in ('済', '終了')} if ZUMI.exists() else set()
DETA = re.compile(r'^(応募|読み直し：応募|提案|興味|応募済)')
last, deta, ba = {}, set(), {}
for c in S.kiroku_rows():
    if len(c) < 7:
        continue
    for i in [x.strip() for x in c[2].split('・') if x.strip().isdigit()]:
        last[i] = (c[0], c[6]); ba[i] = c[1]
        if DETA.match(c[6]):
            deta.add(i)
more, matsu = [], []
for i, (t, s) in last.items():
    if i in deta or i in zumi or not (s.startswith('止まっ') or s.startswith('保留')):
        continue
    (matsu if re.search(r'オーナー.{0,6}待ち', s) else more).append((i, ba[i], t, s[:70]))
if BUN.exists():
    for f in BUN.glob('*.txt'):
        m = re.match(r'^(?:cw|lancers|teian)-(\d+)\.txt$', f.name)
        if not m:
            continue
        i = m.group(1)
        if i in deta or i in zumi or i in {x[0] for x in more + matsu}:
            continue
        s = last.get(i, ('', '記録なし'))[1]
        if re.search(r'見送|辞退|お断り|出さず|出さない|出せず', s):
            continue
        more.append((i, ba.get(i, '?'), last.get(i, ('', ''))[0], '下書きあり・未送信（' + s[:50] + '）'))
print(f'出し漏れ {len(more)} 件 ／ オーナー待ち {len(matsu)} 件 ／ 出した案件 {len(deta)} 件（記録の全期間）／ 相手の表示で済・終了と確かめた {len(zumi)} 件')
for x in sorted(more, key=lambda x: x[2], reverse=True):
    print('  🔴', *x)
for x in matsu:
    print('  🟡', *x)
sys.exit(1 if more else 0)
