// 【出し漏れの検算】CW の「応募した仕事」一覧を3つの絞り（ふつう・非表示・スカウト）全頁で読み、応募の番号と題名を集める（読むだけ）
// 入力: 出し先の tsv ／ログイン済みのブラウザ（profile の CDP）
// 出力: 1行1件「応募番号<TAB>題名」（一覧に案件 ID は出ないので、oubo-zumi-kakunin.cjs が題名で照らす）と「頁 N ／ 応募 M」
// 止まる条件: 出し先が無い rc=2／ブラウザ・頁が読めない rc=1
// 呼び方: node tools/cw-oubo-ids.cjs <置き場>/cw-oubo-ids.tsv
const fs = require('fs'), S = require('./settei.cjs')
if (!process.argv[2]) { console.log('使い方: node tools/cw-oubo-ids.cjs <出し先>'); process.exit(2) }
;(async () => {
  const b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 90000 }); const p = await S.tab(b, 'cw-oubo-ids')
  const ids = new Set(); let pages = 0
  for (const st of ['', 'filter=archived', 'type=invitation']) {
    for (let pg = 1; pg <= 40; pg++) {
      await p.goto(`https://crowdworks.jp/e/proposals?${st ? st + '&' : ''}page=${pg}`, { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(2000)
      const r = await p.$$eval('a[href^="/proposals/"]', as => as.filter(a => /^\/proposals\/\d+$/.test(a.getAttribute('href'))).map(a => a.getAttribute('href').split('/')[2] + '\t' + a.innerText.replace(/\s+/g, ' ').trim()))
      const before = ids.size; r.forEach(x => ids.add(x)); pages++
      if (!r.length || ids.size === before) break
    }
  }
  fs.writeFileSync(process.argv[2], [...ids].join('\n') + '\n'); console.log(`頁 ${pages} ／ 応募 ${ids.size}`)
  await b.close(); process.exit(0)
})().catch(e => { console.log('ERR', String(e.message || e).slice(0, 200)); process.exit(1) })
