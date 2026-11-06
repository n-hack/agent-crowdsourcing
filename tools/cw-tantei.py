#!/usr/bin/env python3
"""【門】巡回の候補（cw-junkai.py の tsv）の募集本文を開き、分野・できるか・勧誘・二重応募の門と、取らない条件の語を当てる（ログインなし・読むだけ）
入力: 巡回の tsv（引数・無ければ <置き場>/junkai/ の一番新しい巡回の結果）／応募の記録（記録にある ID は外す）
取らない条件: 定例・出社・営業・現地・勧誘の型・AI 不可・CW テック（本文のどこでも）／年齢・地域・資格の保有・実機・経験年数・SES と再委託・副業不可（必須・条件の欄だけ。歓迎・尚可の欄は数えない）
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
# ── 応募できない条件（必須・条件の欄の語。docs/05「応募できない募集の見分け方」）。本文を見出し（【…】・■◆▼●□◇◎）で区切り、
#    見出しか1文に「歓迎・尚可・あれば・優遇・不問…」がある所は数えない（その1文に「必須」があれば数える）。🔴は落とす
HISSU = [('🔴年齢・地域', r'\d{2}\s*歳\s*(?:[〜~～\-－]|から)\s*\d{2}\s*歳|\d{2}\s*(?:代|歳)?\s*[〜~～\-－ー]\s*\d{2}\s*(?:代|歳)[^。]{0,6}(?:の方|まで|限定)'
                       r'|(?:2[5-9]|[3-9]\d)\s*歳以上[^。]{0,6}の方|\d{2}\s*歳(?:以下|まで|未満)[^。]{0,6}の方|\d{2}代(?:限定|の方のみ)|日本国籍'
                       r'|(?:東京|大阪|名古屋|福岡|札幌|京都|神戸|横浜|都内|関東|関西|首都圏|[一-龥]{2,3}[都府県市])[^。]{0,8}(?:在住|を拠点|拠点に|にお住まい|近郊|へ通え|に通え)'),
         ('🔴資格必須', r'(?:資格|免許)[^。]{0,16}(?:必須|保有者|お持ちの方|を持っている方|をお持ち|現在保有|を保有し|保有している方)'
                       r'|(?:行政書士|税理士|社労士|社会保険労務士|司法書士|弁護士|公認会計士|看護師|薬剤師|宅建士|宅地建物取引士|中小企業診断士|弁理士|一級建築士|二級建築士)(?:の(?:方|先生)|を募集|募集|資格|登録済|として登録)'),
         ('🔴実機', r'実機[^。]{0,15}(?:必須|お持ち|所有|が必要|が要|をご用意|で(?:の)?(?:確認|テスト|検証|動作))|(?:iPhone|Android|Mac|Windows\s?PC)[^。]{0,10}(?:をお持ちの方|の所有|必須)'),
         ('🔴経験年数', r'(?:経験|実務|開発)[^。]{0,12}\d+\s*年以上|\d+\s*年以上の[^。]{0,8}経験'),
         ('🔴SES・再委託', r'SES|スキルシート|[0-9０-９.]+\s*人月|人月単価|二次請け|三次請け|再委託(?:案件|での参画|先として)'),
         ('🔴副業不可', r'副業(?:不可|NG|禁止|はご遠慮|の方は不可)|専業の方|専任の方(?:のみ)?|本業として')]
YURUI = r'歓迎|尚可|あれば|優遇|望まし|なくても|不問|不要|問いません|未満の方も|でなくても|以外の方も'
MIDASHI = r'(【[^】]{1,24}】|[■◆▼●□◇◎]\s?[^\s。]{1,24})'
def hissu(body):
    """本文から、応募できない条件の印（🔴…:読んだ語）を返す。歓迎・尚可の欄の語は数えない"""
    marks, h = [], ''
    for p in re.split(MIDASHI, body):
        if re.fullmatch(MIDASHI, p or ''): h = p; continue
        if re.search(YURUI, h): continue
        for s in re.split(r'。|\s[・※★\-－]\s?|\s[0-9０-９][\.．)）]\s', p):
            if re.search(YURUI, s) and '必須' not in s: continue
            for n, rx in HISSU:
                m = re.search(rx, s)
                if m and not any(x.startswith(n) for x in marks): marks.append(f'{n}:{m.group(0)[:20]}')
    return marks
# ── ここまで
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
    marks += hissu(body)
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
