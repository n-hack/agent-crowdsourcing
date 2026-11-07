#!/usr/bin/env python3
# 見本として作った物：架空の会社リストの CSV を作り、列の型を確かめる（実在の会社・個人のデータは使わない）
# 使い方: python3 make_list.py            … 正常な回（rc=0）
#         python3 make_list.py --kowasu   … わざと型の外れた行を混ぜる回（確かめで止まって rc=1）
# 出てくる物: kaisha_list.csv（UTF-8）・kaisha_list_bom.csv（Excel 用の BOM 付き）・kazoekata.txt（件数の数え方）
import csv, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SHUTOKU_BI = '2026-11-06'
SHUTOKUMOTO = '見本用に作った架空のデータ'

# 元のデータ（架空）。わざと表記の揺れ（全角数字・余分な空白）と重なり（同じ会社ID）を入れてある
GEN = [
    ('K0001', '見本精機株式会社',       '愛知県', '製造業', '０００-０００１', '架空市見本町1-1',    'https://mihon-seiki.example.com/',   '45'),
    ('K0002', '架空金属工業株式会社',   '愛知県', '製造業', '000-0002',       '架空市見本町2-3',    'https://kakuu-kinzoku.example.com/', '120'),
    ('K0003', 'サンプル樹脂株式会社',   '岐阜県', '製造業', '000-0003',       '架空郡試し町4-5',    'https://sample-jushi.example.com/',  '38'),
    ('K0004', 'ためし電機株式会社',     '三重県', '製造業', '000-0004',       '架空市例え町6-7',    'https://tameshi-denki.example.com/', '210'),
    ('K0005', '見本部品製作所',         '愛知県', '製造業', '000-0005',       '架空市見本町8-9',    'https://mihon-buhin.example.com/',   '17'),
    ('K0006', '架空工機株式会社',       '静岡県', '製造業', '000-0006',       '架空市試し町1-2',    'https://kakuu-kouki.example.com/',   '64'),
    ('K0007', 'サンプル塗装株式会社',   '愛知県', '製造業', '000-0007',       '架空市例え町3-4',    'https://sample-tosou.example.com/',  '29'),
    ('K0008', 'ためし化成株式会社',     '岐阜県', '製造業', '000-0008',       '架空郡見本町5-6',    'https://tameshi-kasei.example.com/', '88'),
    ('K0009', '見本鋳造株式会社',       '三重県', '製造業', '000-0009',       '架空市試し町7-8',    'https://mihon-chuzou.example.com/',  '53'),
    ('K0010', '架空精密株式会社',       '静岡県', '製造業', '000-0010',       '架空市例え町9-10',   'https://kakuu-seimitsu.example.com/','140'),
    ('K0002', '架空金属工業株式会社',   '愛知県', '製造業', '000-0002',       '架空市見本町2-3',    'https://kakuu-kinzoku.example.com/', '120'),
    ('K0011', 'サンプル機械株式会社',   '愛知県', '製造業', '000-0011',       '架空市見本町11-1',   'https://sample-kikai.example.com/',  '76'),
    ('K0012', 'ためし製作所',           '岐阜県', '製造業', '000-0012',       '架空郡試し町12-2',   'https://tameshi-ss.example.com/',    '22'),
    ('K0013', '見本プレス工業株式会社', '三重県', '製造業', '000-0013',       '架空市例え町13-3',   'https://mihon-press.example.com/',   '95'),
    ('K0014', '架空ゴム株式会社',       '静岡県', '製造業', '000-0014',       '架空市見本町14-4',   'https://kakuu-gomu.example.com/',    '41'),
    ('K0015', 'サンプル溶接株式会社',   '愛知県', '製造業', '000-0015',       '架空市試し町15-5',   'https://sample-yousetsu.example.com/','33'),
    ('K0016', 'ためし金型株式会社',     '岐阜県', '製造業', '000-0016',       '架空郡例え町16-6',   'https://tameshi-kanagata.example.com/','58'),
    ('K0007', 'サンプル塗装株式会社',   '愛知県', '製造業', '000-0007',       '架空市例え町3-4',    'https://sample-tosou.example.com/',  '29'),
    ('K0017', '見本ばね製作所',         '三重県', '製造業', '000-0017',       '架空市見本町17-7',   'https://mihon-bane.example.com/',    '12'),
    ('K0018', '架空工業株式会社',       '静岡県', '製造業', '000-0018',       '架空市試し町18-8',   'https://kakuu-kougyou.example.com/', '180'),
    ('K0019', 'サンプル製缶株式会社',   '愛知県', '製造業', '000-0019',       '架空市例え町19-9',   'https://sample-seikan.example.com/',  '47'),
    ('K0020', 'ためし加工株式会社',     '岐阜県', '製造業', '000-0020',       '架空郡見本町20-1',   'https://tameshi-kakou.example.com/', '　６６ '),
    ('K0011', 'サンプル機械株式会社',   '愛知県', '製造業', '000-0011',       '架空市見本町11-1',   'https://sample-kikai.example.com/',  '76'),
]

# 列の型（README の表と同じ）。確かめはこの式だけで当てる
KATA = [
    ('会社ID',   r'K\d{4}',                                   '「K」＋数字4桁・重なりなし'),
    ('会社名',   r'.+',                                       '空でない文字'),
    ('都道府県', r'(愛知|岐阜|三重|静岡)県',                 '絞った4県のどれか'),
    ('業種',     r'製造業',                                   '絞った業種の語'),
    ('郵便番号', r'\d{3}-\d{4}',                              '半角の 3桁-4桁'),
    ('所在地',   r'.+',                                       '空でない文字'),
    ('WebサイトURL', r'https://[a-z0-9-]+\.example\.com/',    'https://〜.example.com/ だけ（見本用のドメイン）'),
    ('従業員数', r'[1-9]\d{0,4}',                             '半角の整数'),
    ('取得元',   r'.+',                                       '空でない文字'),
    ('取得日',   r'\d{4}-\d{2}-\d{2}',                        'YYYY-MM-DD'),
]
COLS = [k[0] for k in KATA] + ['確かめ']

def soroeru(s):
    # 全角の英数字と記号を半角へ・前後の空白（全角も）を消す
    return unicodedata.normalize('NFKC', s).strip()

def tashikame(row):
    ng = [name for (name, pat, _), v in zip(KATA, row) if not re.fullmatch(pat, v)]
    return 'OK' if not ng else 'NG:' + '/'.join(ng)

def main():
    kowasu = '--kowasu' in sys.argv
    gen = list(GEN)
    if kowasu:
        # わざと壊す：ドメインが example.com でない・郵便番号の桁が足りない行を1つ混ぜる
        gen.append(('K0021', '壊した行の会社', '愛知県', '製造業', '000-001', '架空市見本町21-1', 'https://kowashita.example.net/', '10'))

    moto = len(gen)
    mita, kasanari, rows = set(), 0, []
    for r in gen:
        r = [soroeru(x) for x in r] + [SHUTOKUMOTO, SHUTOKU_BI]
        if r[0] in mita:
            kasanari += 1
            continue
        mita.add(r[0])
        rows.append(r + [tashikame(r)])

    ng = [r for r in rows if r[-1] != 'OK']
    for enc, name in (('utf-8', 'kaisha_list.csv'), ('utf-8-sig', 'kaisha_list_bom.csv')):
        if ng:
            break  # NG の行がある回は CSV を書かない（前の正常な CSV をそのまま残す）
        with open(os.path.join(HERE, name), 'w', encoding=enc, newline='') as f:
            w = csv.writer(f); w.writerow(COLS); w.writerows(rows)

    kazoe = [
        f'元の行数 {moto}',
        f'重なりで消した行 {kasanari}（同じ会社IDの2行目以降）',
        f'残った行 {len(rows)} ＝ {moto} − {kasanari}',
        f'確かめ OK {len(rows) - len(ng)} 行 ／ NG {len(ng)} 行',
        '数え方：会社IDを見分けの列にし、出てきた順で最初の1行を残す。表記は NFKC で全角を半角にそろえ、前後の空白を消してから確かめる',
    ]
    if not ng:
        with open(os.path.join(HERE, 'kazoekata.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(kazoe) + '\n')
    print('\n'.join(kazoe))
    for r in ng:
        print(f'🔴 {r[0]} {r[-1]}')
    if ng:
        print('🔴 確かめで止めた（NG の行がある CSV は渡さない）')
        return 1
    print('✅ 全行が列の型どおり')
    return 0

if __name__ == '__main__':
    sys.exit(main())
