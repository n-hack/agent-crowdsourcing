# CW の部屋の見張り（mawasu.sh の5段）が開く応募を選ぶ：応募一覧の「最終更新」が今日の行＋前の周の控えから日付が変わった行・前の控えに無い行（辞退は除く）
# 全部開くと1周約10分（返事に最大11分遅れ）だった。日単位なので日をまたいだ取りこぼしは mawasu.sh が6回に1回の全部開きで拾う
# 使い方: python3 cw-thread-erabu.py <前の控え> <いまの一覧>  出力: 番号のカンマ区切り（空なら開く物なし）
import csv, sys, datetime
def yomu(f):
    try: return {r['応募番号']: r for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t') if r.get('応募番号')}
    except FileNotFoundError: return {}
mae, ima = yomu(sys.argv[1]), yomu(sys.argv[2])
kyou = datetime.date.today().strftime('%Y年%m月%d日')
out = [k for k, r in ima.items() if '辞退' not in (r.get('状態') or '') and ((r.get('最終更新') or '').startswith(kyou) or k not in mae or (mae[k].get('最終更新') or '') != (r.get('最終更新') or ''))]
print(','.join(out))
