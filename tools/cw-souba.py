#!/usr/bin/env python3
"""【相場】予算の帯の無い募集（「ワーカーと相談する」）の金額を、同じ種類の募集の帯から決める（ログインなし・公開の検索を読むだけ）
入力: 語（引数・1つ以上。募集の題名から「何を・どの道具で」の2語を取る：例「Shopify 保守」）／--id <募集の ID>（その募集自身を外す）
      ／--obi <下限>-<上限>（その募集に帯があるとき・税込の円。目安をその帯の中に収めた額を出す：11/06 再現の試し7で同じ帯 0〜82,500円の募集が 60,000円→30,000円と倍ぶれたため）
出力: 題名に語が1つ以上ある、帯のある固定報酬の募集を並べ（終わった募集も含む・検索の新しい順に最大50件・同じ題名の出し直しは1件）、
      上限の中央値・下限の中央値・件数（契約のあった募集が5件以上ならそれだけで出す）と、
      .json の「金額の根拠」にそのまま写す1行（「相場 <語>：<帯のある|契約のあった> N 件・上限の中央値 ◯円（税込）・<日付>」）。
      目安の税抜は「上限の中央値 ÷1.1」の千円切り捨て（docs/04 の「5 値段」）
止まる条件: 帯のある募集が5件に届かないとき rc=4（語を1つ減らして打ち直す・5件未満で決めない）。検索の頁が読めないとき rc=3
呼び方: python3 tools/cw-souba.py --id 13585056 Shopify 保守 ／ 帯のある募集は python3 tools/cw-souba.py --id 13538763 --obi 0-82500 FAQ サイト
"""
import datetime as dt, html, json, os, re, statistics, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settei as S
S.mon()
a = sys.argv[1:]
skip = ''
obi = None
if '--obi' in a:
    i = a.index('--obi'); obi = [int(x) for x in a[i + 1].replace(',', '').split('-')]; a = a[:i] + a[i + 2:]
    if len(obi) != 2 or obi[1] <= 0 or obi[0] > obi[1]:  # 試し8回目：帯の無い募集に --obi 0-0 を付けて「0円を使う」と出た
        sys.exit(f'🔴 --obi {"-".join(map(str, obi))} は帯になっていない（上限が0以下か下限が上限より上）。帯の無い（相談の）募集なら --obi を付けずに打つ')
if '--id' in a:
    i = a.index('--id'); skip = a[i + 1]; a = a[:i] + a[i + 2:]
if not a or a[0] in ('-h', '--help'):
    print(__doc__); sys.exit(2)
if skip:  # 試し9回目：帯の無い募集に作った帯（--obi 0-82500）を付けても止まらなかった → 公開頁の帯と --obi を照らす
    try:
        pj = urllib.request.urlopen(urllib.request.Request('https://crowdworks.jp/public/jobs/' + skip, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf-8', 'ignore')
        pj = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', ' ', pj))).replace('&nbsp;', ' ')
    except Exception as e:
        pj = None; print('🟡 公開頁が読めず、帯は照らせない', e)
    if pj is not None:
        g = re.search(r'固定報酬制\s*(?:([\d,]+)\s*円\s*)?(〜\s*(?:([\d,]+)\s*円)?)?', pj)
        y = lambda v: int(v.replace(',', ''))
        if g and (g.group(1) or g.group(3)):
            pobi = [y(g.group(1)) if g.group(2) and g.group(1) else 0, y(g.group(3)) if g.group(3) else (y(g.group(1)) if not g.group(2) else 0)]
            if pobi[1] == 0: pobi = None  # 「5,000円 〜」（上限なし）は帯として使わない
        else:
            pobi = None
        if pobi and not obi:
            sys.exit(f'🔴 {skip} は帯のある募集（公開頁 {pobi[0]:,}〜{pobi[1]:,}円）。--obi {pobi[0]}-{pobi[1]} を付けて打ち直す')
        if obi and not pobi:
            sys.exit(f'🔴 {skip} の公開頁に帯が無い（相談・時給・上限なし）。--obi を外して打ち直す')
        if obi and pobi and obi != pobi:
            sys.exit(f'🔴 --obi {obi[0]}-{obi[1]} が公開頁の帯 {pobi[0]}-{pobi[1]} と違う。頁の帯で打ち直す')
a = [w for x in a for w in x.split()]  # 「Shopify 保守」を1つで渡されても語に分ける
kw = ' '.join(a)
url = ('https://crowdworks.jp/public/jobs/search?keep_search_criteria=true&order=new&hide_expired=false&search%5Bkeywords%5D=' + urllib.parse.quote(kw))
try:
    t = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf-8', 'ignore')
    jo = json.loads(html.unescape(re.search(r'id="vue-container"[^>]*data="([^"]*)"', t).group(1)))['searchResult']['job_offers']
except Exception as e:
    print('🔴 検索の頁が読めない', e); sys.exit(3)
rows = []
for o in jo:
    j, f = o['job_offer'], (o.get('payment') or {}).get('fixed_price_payment')
    if str(j['id']) == skip or not f: continue
    lo, hi = f.get('min_budget') or 0, f.get('max_budget') or 0
    if not hi or hi < 1000: continue  # 帯の無い物・千円に届かない物（体験・選考の型）は相場に入れない
    if not any(w.lower() in j['title'].lower() for w in a): continue  # 題名に語が1つも無い物は外す（検索は本文でも当たり、別の種類が混ざる）
    if any(r[5] == j['title'][:40] for r in rows): continue  # 同じ題名の出し直しは1件に数える（同じ依頼主の連投で中央値が寄る）
    rows.append((j['id'], int(lo), int(hi), j['status'], (o.get('entry') or {}).get('project_entry', {}).get('num_contracts') or 0, j['title'][:40]))
print(f'語「{kw}」：検索 {len(jo)} 件 ／ 題名に語があり帯のある固定報酬 {len(rows)} 件（自分の募集・帯なし・千円未満・同じ題名の出し直しを外した）')
for r in rows: print(f'  {r[0]} {r[1]:>9,}〜{r[2]:>9,}円 {r[3]:<8} 契約{r[4]} {r[5]}')
if len(rows) < 5:
    print(f'🔴 帯のある募集が {len(rows)} 件（5件未満で決めない）。語を1つ減らすか広い語にして打ち直す'); sys.exit(4)
kei = [r for r in rows if r[4] > 0]
use, dore = (kei, '契約のあった') if len(kei) >= 5 else (rows, '帯のある')  # 契約まで行った募集が5件あればそちらを使う（決まった帯に近い）
print(f'契約のあった募集 {len(kei)} 件 → 中央値は「{dore}」{len(use)} 件で出す')
hi = int(statistics.median(r[2] for r in use)); lo = int(statistics.median(r[1] for r in use))
zei = hi * 10 // 11 // 1000 * 1000  # 整数で割る（82,500÷1.1 を浮動小数で切ると 74,000 になる）
print(f'上限の中央値 {hi:,}円（税込）／下限の中央値 {lo:,}円 ／ 目安の税抜 {int(zei):,}円（上限の中央値÷1.1 の千円切り捨て）')
print(f'金額の根拠（.json に写す1行）：相場 {kw}：{dore} {len(use)} 件・上限の中央値 {hi:,}円（税込）・下限の中央値 {lo:,}円・{dt.date.today():%Y-%m-%d}')
if obi:  # 帯のある募集：目安を相手の帯（税抜の千円切り捨て）の中に収める。帯の上なら上限、下なら下限
    olo, ohi = (x * 10 // 11 // 1000 * 1000 for x in obi)
    kin = int(min(max(zei, olo), ohi))
    print(f'帯のある募集の額：{kin:,}円（税抜）＝目安 {int(zei):,}円 を相手の帯 {obi[0]:,}〜{obi[1]:,}円（税込）の中に収めた値。これだけを使う')
    print(f'金額の根拠（帯のある募集・.json に写す1行）：帯のある募集の額：{kin:,}円（税抜）・帯 {obi[0]:,}〜{obi[1]:,}円（税込）・相場 {kw} の目安 {int(zei):,}円・{dt.date.today():%Y-%m-%d}')
