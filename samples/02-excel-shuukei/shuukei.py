#!/usr/bin/env python3
# 見本として作った物：毎日の売上 CSV（架空の店と数字）から月次レポートの xlsx を作る
# 使い方:
#   python3 shuukei.py tsukuru         … data/ に架空の売上 CSV を30日分作る（乱数の種は固定・同じ物が毎回できる）
#   python3 shuukei.py                 … data/ の CSV を読み、report.xlsx を作り、最後に合計を突き合わせる
#   python3 shuukei.py kensa <xlsx>    … 作った xlsx の数式を読み直して計算し、CSV の合計と突き合わせる（合わなければ rc=1）
# 要る物: Python 3 と openpyxl（pip install openpyxl）
import csv, datetime, glob, os, random, re, sys
from decimal import Decimal, InvalidOperation
from openpyxl import Workbook, load_workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Font, PatternFill

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
OUT = os.path.join(HERE, 'report.xlsx')
MISE = ['見本店A', '見本店B', '見本店C']
SHOUHIN = [(f'商品{i:02d}', tanka) for i, tanka in enumerate([380, 450, 520, 680, 750, 980, 1200, 1480, 1980, 2500], 1)]
HEAD = ['日付', '店', '商品', '数量', '単価', '金額']

def tsukuru():
    os.makedirs(DATA, exist_ok=True)
    rnd = random.Random(20261106)
    for d in range(1, 31):
        with open(os.path.join(DATA, f'uriage_2026-09-{d:02d}.csv'), 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f); w.writerow(HEAD)
            for m in MISE:
                for s, tanka in rnd.sample(SHOUHIN, 5):
                    n = rnd.randint(1, 12)
                    w.writerow([f'2026-09-{d:02d}', m, s, n, tanka, n * tanka])
    print(f'✅ data/ に {d} 日分の CSV を作った（架空の店3つ・商品10個）')

def yomu_csv():
    """CSV を厳しく読む。金額が整数でない行・数量×単価と合わない行があれば、その場所を出して止める"""
    rows, ng = [], []
    files = sorted(glob.glob(os.path.join(DATA, '*.csv')))
    for p in files:
        with open(p, encoding='utf-8-sig', newline='') as f:
            for i, r in enumerate(csv.DictReader(f), 2):
                try:
                    n, t, k = (Decimal(r[c]) for c in ('数量', '単価', '金額'))
                except (InvalidOperation, TypeError):
                    ng.append(f'{os.path.basename(p)} {i}行目：数字として読めない（{r.get("金額")}）'); continue
                if n * t != k:
                    ng.append(f'{os.path.basename(p)} {i}行目：数量×単価 {n * t} と金額 {k} が違う')
                rows.append([datetime.date.fromisoformat(r['日付']), r['店'], r['商品'], int(n), int(t), int(k)])
    return files, rows, ng

def kaku(rows):
    wb = Workbook()
    ws = wb.active; ws.title = '明細'
    ws.append(HEAD)
    for r in rows: ws.append(r)
    last = ws.max_row
    for c in ws['A'][1:]: c.number_format = 'yyyy-mm-dd'  # 日付は文字でなく日付の値で持つ（SUMIFS の条件が型で外れないように）
    rng = lambda col: f"明細!${col}$2:${col}${last}"

    def hyou(title, key_col, keys, label):
        s = wb.create_sheet(title)
        s.append([label, '金額'])
        for k in keys:
            row = s.max_row + 1
            s.append([k, f'=SUMIFS({rng("F")},{rng(key_col)},A{row})'])
        s.append(['合計', f'=SUM(B2:B{s.max_row})'])
        return s

    hyou('店別', 'B', MISE, '店')
    hyou('商品別', 'C', [s for s, _ in SHOUHIN], '商品')
    days = sorted({r[0] for r in rows})
    sd = hyou('日別', 'A', days, '日付')
    for c in sd['A'][1:len(days) + 1]: c.number_format = 'yyyy-mm-dd'
    ch = LineChart(); ch.title = '日ごとの売上（架空）'; ch.y_axis.title = '円'; ch.height = 8; ch.width = 18
    ch.add_data(Reference(sd, min_col=2, min_row=1, max_row=len(days) + 1), titles_from_data=True)
    ch.set_categories(Reference(sd, min_col=1, min_row=2, max_row=len(days) + 1))
    sd.add_chart(ch, 'D2')

    sm = wb.create_sheet('集計', 0)
    sm.append(['項目', '値'])
    sm.append(['月の合計（明細）', f'=SUM({rng("F")})'])
    sm.append(['店別の合計', f"=店別!B{len(MISE) + 2}"])
    sm.append(['商品別の合計', f"=商品別!B{len(SHOUHIN) + 2}"])
    sm.append(['日別の合計', f"=日別!B{len(days) + 2}"])
    sm.append(['3つの表が明細と合うか', '=IF(AND(B3=B2,B4=B2,B5=B2),"合う","合わない")'])
    sm.append(['注', '見本として作った物です。店も数字も架空です'])
    for s in wb.worksheets:
        for c in s[1]:
            c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='1F4E79')
        s.column_dimensions['A'].width = 24; s.column_dimensions['B'].width = 16
    wb.save(OUT)

# ---- 数式を読み直して計算する（表計算ソフトが無くても数式の中身を確かめるため。この見本で使う形だけを読む）
def keisan(wb):
    meisai = list(wb['明細'].iter_rows(min_row=2, values_only=True))
    col = {c: i for i, c in enumerate('ABCDEF')}
    out = {}
    for name in ('店別', '商品別', '日別'):
        ws = wb[name]; vals = []
        for a, b in ws.iter_rows(min_row=2, max_col=2, values_only=True):
            m = re.fullmatch(r'=SUMIFS\(明細!\$([A-F])\$(\d+):\$[A-F]\$(\d+),明細!\$([A-F])\$(\d+):\$[A-F]\$(\d+),A\d+\)', str(b))
            if m:
                sc, s1, s2, kc = m.group(1), m.group(2), m.group(3), m.group(4)
                vals.append(sum(r[col[sc]] for r in meisai[int(s1) - 2:int(s2) - 1] if r[col[kc]] == a))
            elif re.fullmatch(r'=SUM\(B2:B\d+\)', str(b)):
                out[name] = (sum(vals), len(vals))
            else:
                raise SystemExit(f'🔴 {name} に読めない数式：{b}')
    m = re.fullmatch(r'=SUM\(明細!\$F\$(\d+):\$F\$(\d+)\)', wb['集計']['B2'].value)
    out['明細'] = (sum(r[5] for r in meisai[int(m.group(1)) - 2:int(m.group(2)) - 1]), len(meisai))
    return out

def kensa(path):
    files, rows, ng = yomu_csv()
    for x in ng: print('🔴', x)
    moto = sum(r[5] for r in rows)
    out = keisan(load_workbook(path))
    print(f'元の CSV {len(files)} 本・{len(rows)} 行の金額の合計 … {moto:,} 円')
    bad = bool(ng)
    for name, (v, n) in out.items():
        ok = v == moto
        bad |= not ok
        print(f'{"✅" if ok else "🔴"} {name} の合計（数式を読み直して計算・{n} 行） … {v:,} 円' + ('' if ok else f'（差 {v - moto:+,} 円）'))
    if bad:
        print('🔴 合計が合わないので止めた（このレポートは渡さない）'); return 1
    print('✅ 4つの合計が元の CSV と1円も違わない'); return 0

def main():
    a = sys.argv[1:]
    if a[:1] == ['tsukuru']: return tsukuru()
    if a[:1] == ['kensa']: return kensa(a[1] if len(a) > 1 else OUT)
    files, rows, ng = yomu_csv()
    if ng:
        for x in ng: print('🔴', x)
        print('🔴 CSV に読めない行があるので止めた（レポートは作らない）'); return 1
    kaku(rows)
    print(f'report.xlsx を作った（明細 {len(rows)} 行・シート 集計／明細／店別／商品別／日別と折れ線グラフ）')
    return kensa(OUT)

if __name__ == '__main__':
    sys.exit(main())
