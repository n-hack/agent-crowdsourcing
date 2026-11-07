// 【返事の見張り・二重応募の控え】クラウドワークスの「相談・応募した」一覧を全頁読み、状態ごとに数える（読むだけ・送らない）
// 入力: 出し先の tsv（任意）／ログイン済みのブラウザ（profile の CDP）
// 出力: 「行 N ／ 状態ごとの数」。出し先を渡せば タイトル・方式・クライアント・状態・期限・最終更新・仕事番号・応募番号 の表（cwapply.cjs が二重応募の照合に使う）
// 止まる条件: 同じ置き場の前の控えの8割を切った（途中で切れた見込み）→ 控えにせず rc=3／ブラウザにつなげない rc=1
// 呼び方: node tools/cw-oubo-joutai.cjs [<置き場>/cw-joutai-YYYYMMDD-HHMM.tsv]
const fs = require('fs'), path = require('path'), S = require('./settei.cjs')
;(async () => {
  const b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 90000 }); const p = await S.tab(b, process.env.JOUTAI_TAB || 'cw-joutai')
  const rows = []
  // 上限20頁×20行＝400で切れていた（並びは最終更新の新しい順なので、400を超えた古い応募が一覧から落ち、古い募集への二重応募の確かめと返事の率の母数が欠ける）→ 80頁まで・上限に当たったら言う
  const MAXPG = 80; let atari = false
  for (let pg = 1; pg <= MAXPG; pg++) { if (pg === MAXPG) atari = true
    await p.goto(`https://crowdworks.jp/e/proposals?status=active&page=${pg}`, { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(2500)
    const r = await p.$$eval('tr', trs => trs.map(tr => { const c = [...tr.querySelectorAll('td')].map(td => td.innerText.replace(/\s+/g, ' ').trim()); const h = [...tr.querySelectorAll('a[href]')].map(a => a.getAttribute('href')).join(' '); c.push((h.match(/\/jobs\/(\d+)/) || [])[1] || '', (h.match(/\/proposals\/(\d+)/) || [])[1] || ''); return c }).filter(c => c.length >= 8))
    if (!r.length) break
    for (const c of r) rows.push({ title: c[1], kind: c[2], client: c[3], status: c[4], kigen: c[5], koushin: c[6], job: c[c.length - 2], prop: c[c.length - 1] })
    if (r.length < 10) break
  }
  if (atari) console.log(`🔴 上限 ${MAXPG} 頁まで読んだ＝まだ先がある見込み（行 ${rows.length}）`)
  const n = {}; for (const x of rows) n[x.status] = (n[x.status] || 0) + 1
  console.log(`行 ${rows.length} ／ ` + Object.entries(n).map(([k, v]) => `${k} ${v}`).join(' ／ '))
  const out = process.argv[2]
  if (out) { const dir = path.dirname(out); fs.mkdirSync(dir, { recursive: true }); const prev = fs.readdirSync(dir).filter(f => /^cw-joutai-.*\.tsv$/.test(f) && path.join(dir, f) !== path.resolve(out)).sort().pop()
    const pn = prev ? fs.readFileSync(path.join(dir, prev), 'utf8').split('\n').filter(Boolean).length - 1 : 0
    if (pn && rows.length < pn * 0.8) { console.log(`🔴 一覧が途中で切れた見込み（${rows.length}行・前の控え ${prev} は ${pn}行）＝控えにせず古い控えで照らす`); await b.close(); process.exit(3) }
    fs.writeFileSync(out, 'タイトル\t方式\tクライアント\t状態\t期限\t最終更新\t仕事番号\t応募番号\n' + rows.map(x => [x.title, x.kind, x.client, x.status, x.kigen, x.koushin, x.job, x.prop].join('\t')).join('\n') + '\n') }
  await b.close(); process.exit(0)
})().catch(e => { console.log('ERR', String(e.message || e).slice(0, 200)); process.exit(1) })
