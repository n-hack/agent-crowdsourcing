// 【返事の見張り】CW の応募ごとのやり取りを全部開き、最後に書いたのが相手（自分でない）物を「要返信」で出す（読むだけ）
// 入力: ログイン済みのブラウザ（profile の CDP）／自分の便の見分けは profile の「自分の名前の印」／WAIT=ミリ秒（頁の待ち・既定3500）
// 出力: 「要返信 <応募番号> | 相手 | 時刻 | 頭 | 題名」の行と「開いた応募 N ／ 要返信 M」。--atarashii なら前に出した物（<置き場>/junkai/thread-seen.txt）を除いた新しい行だけ
// 止まる条件: 要返信が1件以上で rc=1／ブラウザ・頁が読めない rc=3。受信箱には出ず応募の頁にだけ届く便があるため、受信箱とは別に見る
// 呼び方: node tools/cw-thread-check.cjs [--atarashii]
const fs = require('fs'), path = require('path'), S = require('./settei.cjs')
const ATARASHII = process.argv.includes('--atarashii'), SEEN = path.join(S.DATA, 'junkai', 'thread-seen.txt')
// 返事の要らない終わりの便（不採用・見送りの知らせ）では鳴らさない
const OWARI = /検討させていただいた結果|検討した結果|契約を見送|見送りさせていただ|ご縁がありましたら|ご活躍.{0,8}(お祈り|祈念)/
;(async () => {
  const b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 90000 }); const p = await S.tab(b, process.env.TAB_NAME || 'cw-thread')
  p.on('dialog', d => d.dismiss().catch(() => {}))
  const need = []; let n = 0, rc = 0
  try {
    const ids = new Set()
    for (let pg = 1; pg < 15; pg++) {
      await p.goto('https://crowdworks.jp/e/proposals?status=active&page=' + pg, { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(2500)
      const got = await p.$$eval('a[href*="/proposals/"]', as => as.map(a => (a.href.match(/proposals\/(\d+)/) || [])[1]).filter(Boolean))
      const before = ids.size; got.forEach(x => ids.add(x)); if (ids.size === before) break
    }
    const seen = new Set(fs.existsSync(SEEN) ? fs.readFileSync(SEEN, 'utf8').split('\n') : [])
    for (const pid of ids) {
      n++; await p.goto('https://crowdworks.jp/proposals/' + pid, { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(+(process.env.WAIT || 3500))
      // 日付の行の後ろは先読み (?=\n) にする（改行を食べると本文の無い知らせの直後の自分の便を落とす）
      const r = await p.evaluate(() => { const t = document.body.innerText; const i = t.indexOf('メッセージ\nスクール'); const s = t.slice(i > 0 ? i : 0); const re = /\n([^\n]{1,40})\n(20\d\d)年(\d\d)月(\d\d)日 (\d\d):(\d\d)(?=\n)/g; let m, last = null; while ((m = re.exec(s))) { const k = m[2] + m[3] + m[4] + m[5] + m[6]; if (!last || k >= last.k) last = { k, who: m[1].trim(), head: s.slice(m.index + m[0].length, m.index + m[0].length + 60).replace(/\s+/g, ' ') } } return { last, ti: (document.title || '').slice(0, 40) } })
      if (!r.last || S.jibun(r.last.who) || /^問題報告/.test(r.last.who) || OWARI.test(r.last.head || '')) continue
      const key = pid + '|' + r.last.k
      if (ATARASHII && seen.has(key)) continue
      need.push(key); console.log('要返信', pid, '|', r.last.who, '|', r.last.k, '|', r.last.head, '|', r.ti)
    }
    if (ATARASHII && need.length) S.tsuika(SEEN, need.join('\n') + '\n')
    console.log('開いた応募', n, '／ 要返信', need.length + (ATARASHII ? '（新しい物だけ）' : ''))
    if (!S.jibun((S.P['自分の名前の印'] || [])[0] || '')) console.log('🟡 自分の名前の印が設定に無い（見本のまま）＝自分の便も要返信に数える')
    rc = need.length ? 1 : 0
  } catch (e) { console.log('ERR', String(e.message || e).slice(0, 150)); rc = 3 }
  await b.close().catch(() => {}); process.exit(rc)
})().catch(e => { console.log('ERR', String(e.message || e).slice(0, 150)); process.exit(3) })
