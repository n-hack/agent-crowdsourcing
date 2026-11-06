#!/usr/bin/env python3
"""【返事の見張り】場から届くメール（メッセージ・スカウト・契約・選定・面談の招待）を受信箱で引き、前に見ていない1通があれば件名を出す（読むだけ）
入力: profile の「メールの見張り」（サービスアカウントの鍵・受信箱・送り元）。Google Workspace の受信箱を代理で読む形（gmail.readonly）
出力: 見た通数と新しい便の件名。選定・採用の便は本文を開き「落選／当選の可能性」を添える（題だけで「決まった」と読まない・docs/03）。見た印は <置き場>/.henji-seen.json
止まる条件: 新しい便あり rc=1／通信の失敗 rc=3／鍵・受信箱が未設定 rc=4（見張れていない＝0件と言わない）。初回は見た印を付けるだけで鳴らさない
呼び方: python3 tools/henji-mihari.py（要る部品: pip install google-auth requests）
"""
import base64, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settei as S
M = S.P.get('メールの見張り') or {}
KEY, BOX = os.path.expanduser(M.get('サービスアカウントの鍵') or ''), M.get('受信箱') or ''
if not KEY or not os.path.exists(KEY) or not re.match(r'[^@\s]+@[^@\s]+$', BOX):
    print('🟡 メールの見張りが未設定（profile の「メールの見張り」に鍵と受信箱）＝メールは見ていない'); sys.exit(4)
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
SEEN = S.DATA / '.henji-seen.json'
KEEP = re.compile(r'サービス外連絡|承認されました|メッセージ|スカウト|契約|相談|返信|気になる|オファー|面談|提案.*(採用|当選|選考)|選定|当選|落選|発注|仮払い|採用|依頼が届|招待|Invitation')
SENTEI = re.compile(r'選定|当選|落選|採用')
DROP = re.compile(r'ご応募いただきありがとう|会員登録|ガイド|キャンペーン|クーポン|お知らせ一覧|メルマガ|ニュース|はじめて|おすすめ|新着の仕事|電話確認|本人確認|公式】|応募・スカウトが辞退されました')
a = AuthorizedSession(service_account.Credentials.from_service_account_file(KEY, scopes=['https://www.googleapis.com/auth/gmail.readonly']).with_subject(BOX))
B = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'


def get(url, **q):
    try:
        x = a.get(url, params=q, timeout=40); x.raise_for_status(); return x.json()
    except Exception as e:
        print('通信の失敗（この回は飛ばす）:', type(e).__name__, str(e)[:120]); sys.exit(3)


def honbun(pp):
    if pp.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(pp['body']['data']).decode('utf-8', 'ignore')
    return ''.join(honbun(x) for x in pp.get('parts', []))


first = not SEEN.exists()
seen = set(json.loads(SEEN.read_text())) if not first else set()
moto = ' OR '.join('from:' + x for x in (M.get('送り元') or ['crowdworks.jp', 'lancers.co.jp', 'lancers.jp']))
q = f'(({moto}) OR meet.google.com OR from:calendar-notification@google.com) newer_than:3d'
r = get(B, q=q, maxResults=200, includeSpamTrash='true')
new = []
for m in r.get('messages', []):
    if m['id'] in seen:
        continue
    seen.add(m['id'])
    if first:
        continue
    g = get(f"{B}/{m['id']}", format='metadata', metadataHeaders=['From', 'Subject'])
    h = {x['name']: x['value'] for x in g['payload']['headers']}
    subj = h.get('Subject', '')
    if KEEP.search(subj) and (not DROP.search(subj) or re.search(r'要返信|要回答|ご回答|ご返信', subj)):
        if SENTEI.search(subj):
            body = honbun(get(f"{B}/{m['id']}", format='full')['payload'])
            subj += ' ／本文：' + ('落選（選ばれませんでした）' if re.search(r'選ばれませんでした|残念ながら|見送り', body) else '🔴 当選・採用の可能性（本文を開いて確かめる）')
        new.append((h.get('From', '')[:30], subj[:120]))
S.DATA.mkdir(parents=True, exist_ok=True)
SEEN.write_text(json.dumps(sorted(seen)))
n = len(r.get('messages', []))
print(f'見た {n} 通（3日・{"200で切れた" if n >= 200 else "全部"}）／ 新しい返事らしき便 {len(new)}' + ('（初回は見た印を付けただけ）' if first else ''))
for f, sj in new:
    print('  ', f, '|', sj)
sys.exit(1 if new else 0)
