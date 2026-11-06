#!/usr/bin/env python3
"""【門】巡回の候補（cw-junkai.py の tsv）の募集本文を開き、分野・できるか・勧誘・二重応募の門と、取らない条件の語を当てる（ログインなし・読むだけ）
入力: 巡回の tsv（引数・無ければ <置き場>/junkai/ の一番新しい巡回の結果）／応募の記録（記録にある ID は外す）
取らない条件: 定例・出社・営業・現地・勧誘の型・AI 不可・AI で書いた応募は不可・CW テック・納期が過ぎている・募集が終わっている・上限が千円に届かない額（本文と頁のどこでも）／年齢・地域・資格の保有・実機・経験年数・経験（年数なし）・実績の提示（作品の URL【必須】を含む）・外国語の会話や読み書きの条件・SES と再委託・副業不可（必須・条件の欄だけ。歓迎・尚可の欄は数えない。歓迎が括弧の中の言い添えだけの1文は必須として数える）
出力: 候補ごとに1行。頭が「★」＝🔴が1つも無く分野の門が✅（応募文に進む）／「☆」＝🔴なしで分野🟡（中身を読んで決める・<置き場>/junkai/kouho-kiiro.tsv に残す）／印なし＝落ちた理由つき。最後の行に数
止まる条件: 門が候補の数だけ答えないとき rc=3（照らせていないのに通さない）。開けない頁はその1件だけ飛ばす
呼び方: python3 tools/cw-tantei.py [巡回の tsv]
"""
import csv, datetime as dt, html, json, os, pathlib, re, subprocess, sys, time, urllib.request
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
     ('🟡URL必須', r'(URL|ポートフォリオ)[^。]{0,8}必須|必須[^。]{0,8}(URL|ポートフォリオ)'),
     # 11/06 再現の試し6：喫煙者本人が顔出し録画のインタビューに出る募集が★に来た（本文を読んで見送った）＝本人が出る調査は知らせる（誤って落とす数を測る本文が無いので🟡で始める）
     # 11/06 19:2x 再現の試し7の穴①：手の判定つき80件で 拾い27/57→53/57・誤り10/23→0/23、別の新着59件で 拾い3→9・誤り0（アンケートの回答者・モニター・体験談・実際に使った方・配信者を足し、「顔出し不要」「座談会の動画」「取材記事」「応募時のアンケート」を外した）
     ('🟡本人参加', r'顔出し(?![^。]{0,12}(?:ありません|不要|なし|無し|NG|一切|任意))|(?:オンライン|少人数|小規模|\d名[^。]{0,6})?座談会(?:を開催|にて|に(?:ご)?参加|に出席|形式の(?:インタビュー|調査))|(?:インタビュー|取材(?!記事)|モニター)[^。]{0,12}(?:にご?参加|に出演|にご協力|を受けて|回答者)|ご自身の(?:体験|経験談)|(?<!応募時の)(?<!以下の)(?<!下記の)(?<!下記)(?<!以下)(?<!プロフィール)アンケート(?:です|に(?:ご)?(?:回答|協力|お答え)|へのご?(?:回答|協力))(?![^。]{0,30}(?:応募|提案))|本アンケート|アンケートによる(?:市場)?調査|モニター様?(?:を|の)?募集|モニター調査|モニター体験|テスター(?:を|の)?募集|体験談(?:を|の)?(?:インタビュー|お聞き|お伺い|伺|募集|お寄せ)|実際に(?:ご?利用|ご?使用|購入|受講)(?:した|された|いただいた)方|お話を(?:伺|お?聞か)|インタビューさせて|(?:Liver|ライバー)として|配信(?:していただ|して頂)ける方|配信者(?:を|の)?募集|ライブ配信(?:に|を)(?:して|行って|ご?参加)|(?:この|本)アンケートは|オンラインで意見交換|意見交換[^。]{0,12}(?:いただける|できる)方|お顔写真')]
# ── 応募できない条件（必須・条件の欄の語。docs/05「応募できない募集の見分け方」）。本文を見出し（【…】・＜…＞・■◆▼●□◇◎✅▮◤）で区切り、
#    見出しか1文に「歓迎・尚可・あれば・優遇・不問…」がある所は数えない（その1文に「必須」があれば数える）。🔴は落とす
HISSU = [('🔴年齢・地域', r'\d{2}\s*歳\s*(?:[〜~～\-－]|から)\s*\d{2}\s*歳|\d{2}\s*(?:代|歳)?\s*[〜~～\-－ー]\s*\d{2}\s*(?:代|歳)[^。]{0,6}(?:の方|まで|限定)'
                       r'|(?:2[5-9]|[3-9]\d)\s*歳以上[^。]{0,6}の方|\d{2}\s*歳(?:以下|まで|未満)[^。]{0,6}の方|\d{2}代(?:限定|の方のみ)|日本国籍'
                       r'|(?:東京|大阪|名古屋|福岡|札幌|京都|神戸|横浜|都内|関東|関西|首都圏|[一-龥]{2,3}[都府県市])[^。]{0,8}(?:在住|を拠点|拠点に|にお住まい|近郊|へ通え|に通え)'),
         ('🔴資格必須', r'(?:資格|免許)[^。]{0,16}(?:必須|保有者|お持ちの方|を持っている方|をお持ち|現在保有|を保有し|保有している方)'
                       r'|(?:行政書士|税理士|社労士|社会保険労務士|司法書士|弁護士|公認会計士|看護師|薬剤師|宅建士|宅地建物取引士|中小企業診断士|弁理士|一級建築士|二級建築士)(?:の(?:方|先生)|を募集|募集|資格|登録済|として登録)'),
         ('🔴実機', r'実機[^。]{0,15}(?:必須|お持ち|所有|が必要|が要|をご用意|で(?:の)?(?:確認|テスト|検証|動作))|(?:iPhone|Android|Mac|Windows\s?PC)[^。]{0,10}(?:をお持ちの方|の所有|必須)'),
         ('🔴経験年数', r'(?:経験|実務|開発)[^。]{0,12}\d+\s*年以上|\d+\s*年以上の[^。]{0,8}経験'),
         ('🔴SES・再委託', r'SES|スキルシート|[0-9０-９.]+\s*人月|人月単価|二次請け|三次請け|再委託(?:案件|での参画|先として)'),
         ('🔴副業不可', r'副業(?:不可|NG|禁止|はご遠慮|の方は不可)|専業の方|専任の方(?:のみ)?|本業として'),
         ('🔴経験必須', r'(?<!未)経験(?:者)?[^。]{0,4}[（(]必須|(?<!未)経験(?:者|が|は)?必須|(?<!未)経験者(?:のみ|限定)|(?<!未)経験[^。]{0,6}方を対象'
                       r'|(?:応募条件|応募資格|必須条件|必須スキル|必須の経験|必須要件|＜必須＞|MUST)[】）>\]\s:：]*[^。【]{0,40}?(?<!未)(?<!使用)(?<!利用)経験(?!談|不問|は問|の有無|がなくても|がない方も|に応じ)'),
         ('🔴言語', r'(?:英語|中国語|韓国語|ベトナム語|タイ語|スペイン語|フランス語|ドイツ語|ポルトガル語|[一-龥]{1,3}弁)[^。]{0,20}(?:必須|ネイティブ|ビジネスレベル|日常会話|堪能|話せる方|会話ができる)'
                   r'|(?:英語|中国語|韓国語|ベトナム語|タイ語|スペイン語|フランス語|ドイツ語|ポルトガル語)で(?:の)?[^。]{0,20}(?:できる|可能な|が取れる)方'
                   r'|(?:ネイティブ|ビジネスレベル|日常会話レベル)[^。]{0,8}(?:英語|中国語|韓国語)'),
         ('🔴実績必須', r'(?:実績|(?<!ビジネス)ポートフォリオ|作品)[^。]{0,15}必須|(?:実績|(?<!ビジネス)ポートフォリオ|作品)[^。]{0,8}URL[^。]{0,20}[【\[（(]必須[】\]）)]|必須[^。]{0,4}(?:実績|(?<!ビジネス)ポートフォリオ)|(?:実績|(?<!ビジネス)ポートフォリオ)[^。]{0,10}(?:のある|がある|をお持ちの)方(?:のみ|限定)'
                       r'|(?:実績|(?<!ビジネス)ポートフォリオ)[^。]{0,10}(?:ない|無い)方[^。]{0,10}(?:不可|ご遠慮|お断り|対象外|採用しません)')]
# 必須の欄（見出しか、短い1文の小見出し）の中で、経験・実績を書いた1文は年数が無くても落とす（「使用経験」は型F＝見本を作って出せるので落とさない）
HISSU_RAN = r'必須|応募条件|応募資格|MUST|対象者|求める方'
TOU = r'ご回答|ご記載|ご記入|お答え|教えて|お知らせ|ますか|[？?]'
RAN_KEIKEN = [('🔴経験必須', r'(?<!未)(?<!使用)(?<!利用)経験(?!談|不問|は問|の有無|がなくても|がない方も|に応じ|があれば)'), ('🔴実績必須', r'実績|(?<!ビジネス)ポートフォリオ')]
# 本文のどこでも見る：AI で書いた応募は取らない／納期が今日より前（年が無い日付は、今日より前で半年以内なら今年・それより前なら来年と読む）
HON = [('🔴AI応募不可', r'(?:AI|ＡＩ|Bot|bot|ChatGPT)[^。]{0,12}(?:使用|利用|使っ|作成|生成)[^。]{0,6}(?:と思われる|が疑われる|と判断(?:した|される))'
                     r'|(?:AI|ＡＩ|Bot|bot|ChatGPT)[^。]{0,15}(?:応募|提案|応募文)[^。]{0,12}(?:不可|お断り|ご遠慮|採用(?:致|いた)?しかね|採用しません|対象外|NG|禁止|無効)')]
KIGEN = r'(?:納期|締切|締め切り|〆切|納品日|納品希望日)[】\]）)\s:：は]{0,4}(?:(20\d{2})\s*[年/.\-]\s*)?(\d{1,2})\s*[月/]\s*(\d{1,2}|末)'
def kigen_kire(body, kyou):
    """本文の納期・締切の日付が kyou（datetime.date）より前なら印を返す"""
    import datetime as dt
    for m in re.finditer(KIGEN, body):
        y, mo, d = m.group(1), int(m.group(2)), m.group(3)
        if not 1 <= mo <= 12: continue
        yy = int(y) if y else kyou.year
        try:
            dd = (dt.date(yy + mo // 12, mo % 12 + 1, 1) - dt.timedelta(days=1)).day if d == '末' else int(d)
            hi = dt.date(yy, mo, dd)
        except ValueError: continue
        if not y and hi < kyou and (kyou - hi).days > 183: continue  # 年が無く半年より前＝来年の日付と読む
        if hi < kyou: return f'🔴納期切れ:{m.group(0)[:20]}'
    return None
def gokushou(yosan, body):
    """固定報酬の上限（巡回の tsv の「固定0-110.0」・税込）か本文の契約金額が千円に届かないなら印を返す"""
    m = re.match(r'固定[\d.]+-([\d.]+)', yosan or '')
    if m and 0 < float(m.group(1)) < 1000: return f'🔴極小額:上限{float(m.group(1)):.0f}円'
    m = re.search(r'契約金額[^。\d]{0,12}?([1-9]\d{0,2})\s*円', body)
    if m and not re.search(r'時給|件|あたり|につき|文字|[/／]', body[max(0, m.start() - 10):m.end() + 12]): return f'🔴極小額:{m.group(0)[:20]}'  # 1件◯円・1文字◯円の単価は数えない
    return None
YURUI = r'歓迎|尚可|あれば|優遇|望まし|なくても|不問|不要|問いません|未満の方も|でなくても|以外の方も|必須で(?:は|も)(?:ありません|ない|なく)|必要(?:ありません|ない|はありません)'
HISSU_DE_NAI = r'必須で(?:は|も)(?:ありません|ない|なく)'
SOE = r'[（(][^（）()]{6,}[）)]'  # 6字以上の括弧＝言い添え（「（歓迎）」「（あれば尚可）」のような短い括弧は1文全体にかかるので外さない）
MIDASHI = r'(【[^】]{1,24}】|(?<!「)＜[^＞]{1,24}＞|[■◆▼●□◇◎✅▮◤]\s?[^\s。]{1,24})'
def hissu(body):
    """本文から、応募できない条件の印（🔴…:読んだ語）を返す。歓迎・尚可の欄の語は数えない"""
    marks, h = [], ''
    body = re.sub(r'【\s*(必須|任意)\s*】', r'（\1）', body)  # 項目の後ろの【必須】は見出しでなく、その項目の言い添え（見出しにすると前の1文から外れる）
    def put(n, m, bun=None):
        if m and not any(x.startswith(n) for x in marks): marks.append(f'{n}:{(bun or m.group(0)).strip()[:20]}')
    for p in re.split(MIDASHI, body):
        if re.fullmatch(MIDASHI, p or ''): h = p; continue
        if re.search(YURUI, h): continue
        ran = bool(re.search(HISSU_RAN, h))  # 見出しが必須の欄
        kangei = False  # 「⚫︎歓迎条件」のような短い1文の小見出しの後（言語の条件だけに使う。前からの規則の数は変えない）
        for s in re.split(r'。|\s[・※★\-－]\s?|\s[0-9０-９][\.．)）]\s', p):
            if len(s.strip()) <= 20 and re.search(HISSU_RAN, s) and not re.search(YURUI, s): ran = True; kangei = False  # 「＜必須＞」「■必須条件」のような短い小見出し
            sy = re.sub(SOE, '', s)  # 「◯◯の実務経験がある方（税理士…など歓迎）」＝歓迎は括弧の中の言い添えだけ。言い添えを外して見る
            if re.search(YURUI, sy) and '必須' not in re.sub(HISSU_DE_NAI, '', sy): ran = False; kangei = kangei or len(s.strip()) <= 20 or bool(re.search(r'(?:歓迎|尚可|優遇)\S{0,6}$', s.strip())); continue  # 歓迎の1文から後は必須の欄として読まない
            for n, rx in HISSU:
                if not (n == '🔴言語' and kangei): put(n, re.search(rx, s))
            if ran and not re.search(TOU, s):  # 「ご回答ください」「ありますか？」＝聞いているだけの1文は除く
                for n, rx in RAN_KEIKEN: put(n, re.search(rx, s), s)  # 印には当たった1文の頭を出す
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
    marks += [n for n, rx in HON if re.search(rx, body)]
    marks += [k for k in (kigen_kire(body, dt.date.today()), gokushou(r[2], body)) if k]
    if 'このお仕事の募集は終了しています' in x: marks.append('🔴募集終了')
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
