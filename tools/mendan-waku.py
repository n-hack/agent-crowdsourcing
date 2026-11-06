#!/usr/bin/env python3
"""【返事】面談・打ち合わせの打診が来たとき、オーナーの予定の空きから一番早い3枠を出す（予定の中身は読まない・空きだけ）
入力: profile の「面談の予定」（サービスアカウントの鍵・カレンダーのメール・平日の時間・何時間後から）
出力: 「11月6日（金）15:00〜15:30」の形で3行（同じ日は2枠まで・1時間以上空ける）。8日以内に無ければ「空き枠なし」
止まる条件: 鍵・カレンダーが未設定 rc=4／予定が取れない rc=3
呼び方: python3 tools/mendan-waku.py（要る部品: pip install google-auth requests）
"""
import datetime as dt, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settei as S
M = S.P.get('面談の予定') or {}
KEY, CAL = os.path.expanduser(M.get('サービスアカウントの鍵') or ''), M.get('カレンダーのメール') or ''
if not KEY or not os.path.exists(KEY) or not re.match(r'[^@\s]+@[^@\s]+$', CAL):
    print('🟡 面談の予定が未設定（profile の「面談の予定」に鍵とカレンダーのメール）'); sys.exit(4)
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
h0, h1 = (M.get('平日の時間') or [10, 19])[:2]
JST = dt.timezone(dt.timedelta(hours=9)); now = dt.datetime.now(JST); start = now + dt.timedelta(hours=M.get('何時間後から', 2)); end = now + dt.timedelta(days=8)
cr = service_account.Credentials.from_service_account_file(KEY, scopes=['https://www.googleapis.com/auth/calendar.readonly']).with_subject(CAL)
try:
    r = AuthorizedSession(cr).post('https://www.googleapis.com/calendar/v3/freeBusy', json={'timeMin': now.isoformat(), 'timeMax': end.isoformat(), 'timeZone': 'Asia/Tokyo', 'items': [{'id': 'primary'}]}, timeout=30).json()
    busy = [(dt.datetime.fromisoformat(x['start'].replace('Z', '+00:00')), dt.datetime.fromisoformat(x['end'].replace('Z', '+00:00'))) for x in r['calendars']['primary']['busy']]
except Exception as e:
    print('🔴 予定が取れない', type(e).__name__, str(e)[:120]); sys.exit(3)
W = '月火水木金土日'; out = []; d = now.date(); last = None
while d < end.date() and len(out) < 3:
    if d.weekday() < 5:
        for hh in range(h0, h1):
            for mm in (0, 30):
                st = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=JST); en = st + dt.timedelta(minutes=30)
                if st < start or any(bs < en and st < be for bs, be in busy):
                    continue
                if sum(1 for o in out if o[0].date() == d) >= 2 or (last and last.date() == d and st - last < dt.timedelta(hours=1)):
                    continue
                out.append((st, en)); last = st
                if len(out) >= 3:
                    break
            if len(out) >= 3:
                break
    d += dt.timedelta(days=1)
for st, en in out:
    print(f'{st.month}月{st.day}日（{W[st.weekday()]}）{st:%H:%M}〜{en:%H:%M}')
if not out:
    print('空き枠なし（8日以内）')
