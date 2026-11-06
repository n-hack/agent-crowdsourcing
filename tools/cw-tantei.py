#!/usr/bin/env python3
"""【門】巡回の候補（cw-junkai.py の tsv）の募集本文を開き、分野・できるか・勧誘・二重応募の門と、取らない条件の語を当てる（ログインなし・読むだけ）
入力: 巡回の tsv（引数・無ければ <置き場>/junkai/ の一番新しい巡回の結果）／応募の記録（記録にある ID は外す）
出力: 候補ごとに1行。頭が「★」＝🔴が1つも無く分野の門が✅（応募文に進む）／「☆」＝🔴なしで分野🟡（中身を読んで決める・<置き場>/junkai/kouho-kiiro.tsv に残す）／印なし＝落ちた理由つき。最後の行に数
止まる条件: 門が候補の数だけ答えないとき rc=3（照らせていないのに通さない）。開けない頁はその1件だけ飛ばす
呼び方: python3 tools/cw-tantei.py [巡回の tsv]
"""
import csv, html, json, os, pathlib, re, subprocess, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settei as S
S.mon()
D = S.DATA / 'junkai'
JUNKAI = re.compile(r'^20\d{6}-\d{4}\.tsv$')  # 巡回の結果だけ（同じ置き場の別の表を読まない）
if len(sys.argv) >= 2:
    f = pathlib.Path(sys.argv[1])
else:
    c = sorted(x for x in D.glob('*.tsv') if JUNKAI.match(x.name)) if D.exists() else []
    if not c:
        print('🔴 巡回の結果が無い（先に cw-junkai.py）'); sys.exit(3)
    f = c[-1]
# 取らない条件の語（本文）。🔴は落とす・🟡は知らせるだけ
R = [('🔴定例', r'定例|MTG|ミーティング|報告会|打ち合わせ.{0,6}参加|会議.{0,6}参加'), ('🔴出社', r'出社|来社|常駐'),
     ('🔴外連絡', r'サービス外連絡'), ('🔴営業', r'営業|テレアポ|架電|成約'), ('🔴現地', r'展示会|現地|撮影の実施'),
     ('🔴勧誘の型', r'(?s)(?=.*年齢)(?=.*性別)(?=.*現在の(?:お?仕事|職業))'),
     ('🔴勧誘', r'未経験|初心者|学べる|スキマ時間'),
     ('🔴勧誘の型', r'目標収入|副業での目標|★\s*5|星5|forms\.gle|docs\.google\.com/forms|画面オン|配偶者|お子様の有無|ご年齢|家族構成|実家暮らし'),
     ('🔴AI不可', r'生成AIの使用は避け|AI.{0,8}(使用)?(禁止|不可|NG)|文章作成ツール[^。]{0,20}自動生成|自動生成された(もの|物|文章)'),
     ('🔴CWテック', r'クラウドワークス テック事務局|受託企業さまへのお仕事の紹介はできません'),
     ('🟡URL必須', r'(URL|ポートフォリオ)[^。]{0,8}必須|必須[^。]{0,8}(URL|ポートフォリオ)')]
rows = [r for r in csv.reader(open(f, encoding='utf-8'), delimiter='\t')][1:]
done = S.kiroku_ids()
rows = [r for r in rows if len(r) >= 7 and r[1] not in done]
print(f'{f.name} の候補 {len(rows)} 件を開く（記録にある ID は外した）')
got = []
for r in rows:
    try:
        t = urllib.request.urlopen(urllib.request.Request(f'https://crowdworks.jp/public/jobs/{r[1]}', headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf-8', 'ignore')
    except Exception as e:
        print(r[1], '取れず', e); continue
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', t, flags=re.S)
    got.append((r, re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t)))))
    time.sleep(1.0)
mon = {}
if got:
    pr = subprocess.run(['node', str(pathlib.Path(__file__).with_name('mon-hantei.cjs'))], input=json.dumps([{'id': r[1], 'text': x} for r, x in got]),
                        capture_output=True, text=True, timeout=120)
    mon = {a[0]: a for a in (l.split('\t') for l in pr.stdout.splitlines()) if len(a) >= 2}
    if pr.returncode or len(mon) != len(got):
        print(f'🔴 門が {len(mon)}/{len(got)} 件しか答えていない（rc={pr.returncode}）', pr.stdout[-200:], pr.stderr[-200:]); sys.exit(3)
ok = aka = 0
for r, x in got:
    jid = r[1]
    i = x.find('仕事の詳細'); j = x.find('クライアント情報', i); body = x[i:j if j > i else i + 6000]
    k = body.rfind('この仕事の特徴'); body = body[:k] if k > len(body) - 200 else body  # 終わりに CW が自動で付ける札（スキマ時間歓迎 など）を外す
    marks = [n for n, rx in R if re.search(rx, body)]
    a = mon.get(jid, [jid, '?', '', ''])
    g = a[1]
    if g == '🔴': marks.append('🔴分野'); aka += 1
    elif g == '?': marks.append('🔴分野が照らせず')
    if len(a) > 2 and a[2]: marks.append('🔴できない:' + a[2][:40])
    if len(a) > 3 and a[3]: marks.append('🔴講座売りの印:' + a[3][:40])
    kouho = not any(m.startswith('🔴') for m in marks)
    m = re.search(r'応募した人\s*(\d+)\s*人', x)
    if kouho and g == '🟡':
        with open(D / 'kouho-kiiro.tsv', 'a', encoding='utf-8') as w:
            w.write('\t'.join([time.strftime('%Y-%m-%dT%H:%M'), jid, r[2], r[6][:60]]) + '\n')
    if kouho and g == '✅': ok += 1
    print(('★ ' if kouho and g == '✅' else '☆ ' if kouho else '') + jid, r[2], ' '.join(marks) or '✅', '|', '分野' + g, r[6][:50], f'| 応募{m.group(1) if m else "?"}人')
print(f'応募文へ進む（🔴無し・分野✅） {ok} / {len(rows)} ／ 分野の門で🔴 {aka} ／ 開けなかった {len(rows) - len(got)}')
