#!/usr/bin/env python3
# 見本として作った物：架空の歯科医院の FAQ（faq.json・20問）から問い合わせの返事の下書きを作り、危ない下書きを止める
# 使い方:
#   python3 henji.py "問い合わせの文"   … 下書きと判定（緑＝人が確かめて送ってよい ／ 赤＝送らずに人へ回す）
#   python3 henji.py tameshi            … 試しの問い合わせ10通（赤になるはず3通・緑になるはず7通）を流して数える
# 止める印は AI ではなく式（文字の照らし合わせ）で当てる。下書きは FAQ の答えの文だけを使う
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FAQ = json.load(open(os.path.join(HERE, 'faq.json'), encoding='utf-8'))['faq']
KINGAKU = re.compile(r'\d[\d,]*円')
IIKIRI = re.compile(r'必ず|絶対|治ります|保証|確実|100%|１００％')     # 下書きに出たら止める語
IIKIRI_TOI = re.compile(r'必ず|絶対|保証|確実|治りますか|100%|１００％')  # 問い合わせが言い切りを求めている
KINGAKU_TOI = re.compile(r'料金|費用|いくら|値段|何円|金額')
FAQ_KINGAKU = {k for f in FAQ for k in KINGAKU.findall(f['a'])}

def erabu(toi):
    """当たった語の字数の合計がいちばん大きい FAQ を選ぶ。どの語も当たらなければ None"""
    best, best_score = None, 0
    for f in FAQ:
        score = sum(len(k) for k in f['kw'] if k in toi)
        if score > best_score:
            best, best_score = f, score
    return best

def kensa(toi, shitagaki):
    """赤の理由の一覧を返す（空なら緑）。下書きは人や AI が手直しした物でも同じ検査を通す"""
    riyuu = []
    if shitagaki is None:
        return ['どの FAQ にも当たらない']
    for k in KINGAKU.findall(shitagaki):
        if k not in FAQ_KINGAKU:
            riyuu.append(f'FAQ に無い金額「{k}」が下書きにある')
    if KINGAKU_TOI.search(toi) and not KINGAKU.search(shitagaki):
        riyuu.append('金額を聞かれているが FAQ に金額が無い')
    for m in IIKIRI.finditer(shitagaki):
        riyuu.append(f'言い切りの語「{m.group()}」が下書きにある')
    m = IIKIRI_TOI.search(toi)
    if m:
        riyuu.append(f'言い切り（「{m.group()}」）を求める問い合わせ')
    return riyuu

def kotaeru(toi):
    f = erabu(toi)
    shitagaki = None if f is None else f"お問い合わせありがとうございます。\n{f['a']}\nほかにご不明な点があれば、お気軽にお尋ねください。"
    riyuu = kensa(toi, shitagaki)
    return f, shitagaki, riyuu

def dasu(toi):
    f, s, riyuu = kotaeru(toi)
    print(f'問い合わせ：{toi}')
    print(f'使った FAQ：{"No." + str(f["no"]) if f else "なし"}')
    print('下書き：' + (s.replace('\n', ' ') if s else '（作らない）'))
    print('判定：' + ('緑（人が確かめて送ってよい）' if not riyuu else '赤（送らずに人へ回す）… ' + '／'.join(riyuu)))
    return riyuu

TAMESHI = [
    ('土曜日は何時まで診療していますか？', '緑'),
    ('車で行きたいのですが駐車場はありますか', '緑'),
    ('明日の予約をキャンセルしたいです', '緑'),
    ('クレジットカードで払えますか', '緑'),
    ('5歳の子どもを連れて行っても大丈夫ですか', '緑'),
    ('初めて行くのですが、何を持っていけばいいですか', '緑'),
    ('クリーニングだけでも予約できますか', '緑'),
    ('ホワイトニングの料金はいくらですか', '赤'),
    ('ホワイトニングをすれば必ず白くなりますか', '赤'),
    ('近くでおすすめのランチのお店はありますか', '赤'),
]

def tameshi():
    hit = {'赤': [0, 0], '緑': [0, 0]}
    for i, (toi, hazu) in enumerate(TAMESHI, 1):
        print(f'--- {i}（{hazu}になるはず）')
        deta = '赤' if dasu(toi) else '緑'
        hit[hazu][1] += 1
        hit[hazu][0] += deta == hazu
    # 下書きの検査が生きているか（人や AI が下書きを手直しして危ない語を足した場合）
    kowashi = [
        ('ホワイトニングはしていますか', 'ホワイトニングを行っています。必ず白くなります。'),
        ('ホワイトニングはしていますか', 'ホワイトニングを行っています。料金は5,000円です。'),
    ]
    tomatta = sum(1 for toi, s in kowashi if kensa(toi, s))
    print('=== 数')
    print(f"赤になるはずの問い合わせ … {hit['赤'][0]}／{hit['赤'][1]} が赤")
    print(f"緑になるはずの問い合わせ … {hit['緑'][0]}／{hit['緑'][1]} が緑")
    print(f'手直しで危ない語を足した下書き … {tomatta}／{len(kowashi)} が赤')
    ok = hit['赤'][0] == hit['赤'][1] and hit['緑'][0] == hit['緑'][1] and tomatta == len(kowashi)
    print('✅ 全部はずの通り' if ok else '🔴 はずと違う結果がある')
    return 0 if ok else 1

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        print('使い方: python3 henji.py "問い合わせの文" ／ python3 henji.py tameshi'); sys.exit(2)
    if a[0] == 'tameshi':
        sys.exit(tameshi())
    sys.exit(1 if dasu(' '.join(a)) else 0)
