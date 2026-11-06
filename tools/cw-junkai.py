#!/usr/bin/env python3
"""【巡回】クラウドワークスの公開の新着を語ごとに引き、前回の巡回より後に出た募集を残す（ログインなし・読むだけ）
入力: config/profile.json の「巡回の語」（"" は語なしの新着一覧）／前回の時刻 <置き場>/junkai/.last（無ければ48時間前から）／応募の記録（記録にある ID は出さない）
出力: <置き場>/junkai/YYYYMMDD-HHMM.tsv（1行目は見出し・報酬の列は「固定5000-10000」「時給1500-2000」「固定相談」「その他」）。画面には1行目にその tsv の道、最後の行に件数の内訳。勧誘の型の語・CWテック（題名が⭐）・自社の依頼主・同じ題名が別の相手で並ぶ物は外す
止まる条件: 語を1つも引けなかったとき rc=3（通信か頁の形が変わった）。1件も残らないのは rc=0（正常）
呼び方: python3 tools/cw-junkai.py ／ 語を変えるときは profile の「巡回の語」を直す（環境変数 CS_JUNKAI_GO="語,語" でその回だけ差し替え）
"""
import concurrent.futures, datetime as dt, html, json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settei as S

KWS = [x for x in os.environ['CS_JUNKAI_GO'].split(',')] if os.environ.get('CS_JUNKAI_GO') is not None else (S.P.get('巡回の語') or [''])
# 題名・要約にあれば外す語（副業の人集め・講座売りに多い言い方）。本文での判定は cw-tantei.py と門がする
NG = ['サービス外連絡', '定例MTG', '週1出社', '来社', '出社', '未経験OK', '未経験歓迎', '学びながら', '学べる', '初心者歓迎', '初心者OK',
      'スキマ時間', '実績作り', '主婦', '学生', '在宅ワーク初心者', 'サポート充実', 'メンバー募集', 'アシスタント募集', '挑戦', '仲間',
      '研修', '育成', '副業OK', '稼げる']
JISHA = [x for x in (S.P.get('自社の依頼主ID') or []) if x]
OUT = S.DATA / 'junkai'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'


def fetch(kw):
    url = ('https://crowdworks.jp/public/jobs/search?keep_search_criteria=true&order=new&hide_expired=true'
           '&search%5Bkeywords%5D=' + urllib.parse.quote(kw))
    t = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=30).read().decode('utf-8', 'ignore')
    m = re.search(r'id="vue-container"[^>]*data="([^"]*)"', t)
    if not m:
        return None
    return json.loads(html.unescape(m.group(1)))['searchResult']['job_offers']


def pay_of(p):
    """報酬の種類と帯（円・整数）。固定でも時給でもない物は「その他」（試し：「None0-0」が tsv に出ていた）"""
    en = lambda v: int(float(v or 0))  # 検索の頁は 5000.0 の形で返す → 「固定5000.0-10000.0」と出ていた
    if p.get('fixed_price_payment'):
        f = p['fixed_price_payment']; return '固定', en(f.get('min_budget')), en(f.get('max_budget'))
    if p.get('hourly_payment'):
        h = p['hourly_payment']; return '時給', en(h.get('min_hourly_wage')), en(h.get('max_hourly_wage'))
    return 'その他', 0, 0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    last_f = OUT / '.last'
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    since = last_f.read_text().strip() if last_f.exists() else (now - dt.timedelta(hours=48)).isoformat()
    done = S.kiroku_ids()  # 応募・見送りを記録した ID は出さない（途中で止めて .last が残らず同じ募集を2回出したため）
    seen, rows, titles = set(), [], {}
    n = {'語': 0, '取れなかった語': 0, '募集': 0, '期間内': 0, 'CWテックで外す': 0, '自社で外す': 0, '勧誘の型で外す': 0, '残った': 0}

    def fetch_ma(kw):  # 3本並べて取る。1本ごとに1.5秒あける（相手の頁への負荷を抑える）
        try:
            return fetch(kw)
        finally:
            time.sleep(1.5)
    pool = concurrent.futures.ThreadPoolExecutor(3)
    futs = {kw: pool.submit(fetch_ma, kw) for kw in dict.fromkeys(KWS)}
    for kw in dict.fromkeys(KWS):
        n['語'] += 1
        try:
            offers = futs[kw].result()
        except Exception as e:
            offers = None; print(f'取れなかった: {kw} ({e})', file=sys.stderr)
        if offers is None:
            n['取れなかった語'] += 1; continue
        for o in offers:
            jo, cl = o.get('job_offer') or {}, o.get('client') or {}
            if jo.get('id') in seen or str(jo.get('id')) in done:
                continue
            seen.add(jo.get('id')); n['募集'] += 1
            at = jo.get('last_released_at') or ''
            if at <= since:
                continue
            n['期間内'] += 1
            title = jo.get('title') or ''
            if title.lstrip().startswith('⭐'):  # CW テック事務局の紹介は個人限定・外の頁から応募（法人で回す形に合わない）
                n['CWテックで外す'] += 1; continue
            if JISHA and any(x in json.dumps(cl, ensure_ascii=False) for x in JISHA):
                n['自社で外す'] += 1; continue
            if any(w in title + (jo.get('description_digest') or '') for w in NG):
                n['勧誘の型で外す'] += 1; continue
            kind, lo, hi = pay_of(o.get('payment') or {})
            soudan = kind == '固定' and max(lo, hi) == 0
            pe = (o.get('entry') or {}).get('project_entry') or {}
            oubo, hope = pe.get('num_application_conditions'), pe.get('project_contract_hope_number') or 1
            titles.setdefault(title, set()).add(cl.get('username'))
            rows.append([at[:16], str(jo.get('id')), (f'{kind}相談' if soudan else kind if kind == 'その他' else f'{kind}{lo}-{hi}'), cl.get('username') or '',
                         '確' if cl.get('is_employer_certification') else '-', kw, title.replace('\t', ' '), '-' if oubo is None else f'{oubo}/{hope}'])
    pool.shutdown()
    dup = {t for t, us in titles.items() if len(us) >= 2}
    rows = sorted([r for r in rows if r[6] not in dup], reverse=True)
    n['残った'] = len(rows)
    f = OUT / (now.strftime('%Y%m%d-%H%M') + '.tsv')
    with f.open('w', encoding='utf-8') as w:
        w.write('出た時刻\tID\t報酬\t依頼主\t本人確認\t語\tタイトル\t応募/募集\n')
        for r in rows:
            w.write('\t'.join(r) + '\n')
    print(f)
    print(f'前回 {since[:16]} より後 ／ ' + ' ／ '.join(f'{k} {v}' for k, v in n.items()) + f' ／ 同じタイトルが別の相手で並ぶ物 {len(dup)}種を外した')
    if n['語'] and n['取れなかった語'] == n['語']:
        print('🔴 語を1つも引けなかった（通信か頁の形が変わった）・前回の時刻は進めない'); sys.exit(3)
    last_f.write_text(now.isoformat())


if __name__ == '__main__':
    main()
