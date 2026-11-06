"""設定の口（Python 側）：個人・会社の値は全部ここから読む（道具の中に名前・メール・パスを書かない）
入力: config/profile.json（無ければ profile.example.json）＋環境変数 CS_PROFILE・CS_DATA
出力: P（設定）・DATA（置き場）・KIROKU（応募の記録）・kiroku_ids()・kiroku_tsuika(列)・mon()（門を通す）
止まる条件: tools/nhack-mon.cjs が通らないとき rc=9／tsuika の列が7つでないとき rc=2
呼び方: import settei as S ／ python3 tools/settei.py tsuika 日付 場 案件ID 中身 提示額 月額 状態
"""
import json, os, pathlib, subprocess, sys
R = pathlib.Path(os.path.abspath(__file__)).parent.parent
_c = R / 'config'
FILE = pathlib.Path(os.environ.get('CS_PROFILE') or (_c / ('profile.json' if (_c / 'profile.json').exists() else 'profile.example.json')))
P = json.loads(FILE.read_text(encoding='utf-8'))
DATA = pathlib.Path(os.path.expanduser(os.environ.get('CS_DATA') or P.get('置き場') or '~/cs-data'))
KIROKU = DATA / 'oubo-kiroku.tsv'
MIDASHI = ['日付', '場', '案件ID', '中身', '提示額', '月額', '状態']


def mon():
    r = subprocess.run(['node', str(R / 'tools' / 'nhack-mon.cjs')], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout.strip()); sys.exit(9)


def kiroku_rows():
    """記録の行（見出しを除く）。字の壊れた行があっても落ちない"""
    if not KIROKU.exists():
        return []
    return [l.rstrip('\n').split('\t') for l in open(KIROKU, encoding='utf-8', errors='replace')][1:]


def kiroku_ids():
    """記録の3列目（案件ID・「・」で複数）を全部"""
    return {x.strip() for c in kiroku_rows() if len(c) >= 3 for x in c[2].split('・') if x.strip()}


def kiroku_tsuika(cols):
    """記録に1行足す（printf で書かない：本文の % で途中まで書いて壊れるため）。タブ・改行は空白にする"""
    DATA.mkdir(parents=True, exist_ok=True)
    new = not KIROKU.exists()
    with open(KIROKU, 'a', encoding='utf-8') as w:
        if new:
            w.write('\t'.join(MIDASHI) + '\n')
        w.write('\t'.join(str(x).replace('\t', ' ').replace('\n', ' ') for x in cols) + '\n')


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'tsuika':
        if len(sys.argv) != 9:
            print('🔴 列は7つ（' + '・'.join(MIDASHI) + '）'); sys.exit(2)
        kiroku_tsuika(sys.argv[2:]); print('記録に1行', KIROKU); sys.exit(0)
    print(json.dumps({'設定': str(FILE), '置き場': str(DATA), '記録': str(KIROKU)}, ensure_ascii=False, indent=1))
