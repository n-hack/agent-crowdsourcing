// 【巡回】ランサーズの募集を語ごとに新しい順で引き、記録に無い物の頁を開いて、依頼主の評価・発注率がよく提案できる物だけ「★」で出す（読むだけ）
// 入力: 語（引数・1つ以上）／応募の記録と <置き場>/junkai/l-seen.txt（前に見た ID は出さない）／ブラウザ（profile の CDP）
// 出力: 「見る N件」と、★ の行（ID | 題名 | 報酬 | 評価 | 発注率 | 提案数）。★ の線＝評価5以上・低評価が1割以下・発注率50%以上・提案の制限や AI 不可の指定が無い
// 止まる条件: 語が無い rc=2／ブラウザにつなげない rc=1
// 呼び方: node tools/l-junkai.cjs <語> [語…]（★ の候補は teian.cjs の前に門と本文を読んで決める）
require('./nhack-mon.cjs')()
const fs = require('fs'), path = require('path'), S = require('./settei.cjs')
const kws = process.argv.slice(2); if (!kws.length) { console.log('使い方: node tools/l-junkai.cjs <語> [語…]'); process.exit(2) }
const SF = path.join(S.DATA, 'junkai', 'l-seen.txt'), KF = S.kiroku
const seen = new Set([...((fs.existsSync(KF) ? fs.readFileSync(KF, 'utf8') : '').match(/\d{7}/g) || []), ...(fs.existsSync(SF) ? fs.readFileSync(SF, 'utf8').split('\n') : [])])
;(async () => {
  const b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 90000 }); const p = await S.tab(b, 'l-junkai'); p.on('dialog', d => d.dismiss().catch(() => {}))
  const ids = new Map()
  for (const k of kws) {
    await p.goto('https://www.lancers.jp/work/search?open=1&sort=started&keyword=' + encodeURIComponent(k), { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(3500)
    const r = await p.evaluate(() => [...document.querySelectorAll('a[href*="/work/detail/"]')].filter(a => a.innerText.trim().length > 8).map(a => [a.href.match(/detail\/(\d+)/)[1], a.innerText.trim().replace(/\s+/g, ' ').slice(0, 45)]))
    for (const [i, t] of r.slice(0, 20)) if (!seen.has(i)) ids.set(i, t)
  }
  console.log('見る', ids.size, '件（記録に無いもの）'); if (ids.size) S.tsuika(SF, [...ids.keys()].join('\n') + '\n')
  for (const [id, ti] of ids) {
    await p.goto('https://www.lancers.jp/work/detail/' + id, { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(1500)
    const t = await p.evaluate(() => document.body.innerText), c = t.slice(t.indexOf('依頼をしたい'))
    const ev = c.match(/評価\s*\n\s*([\d.]+)\s*\n\s*([\d.]+)/), hr = c.match(/発注率\s*\n\s*(\d+)%\s*\n\s*(\d+)\s*\/\s*(\d+)/)
    const pay = (t.match(/(プロジェクト|タスク|コンペ)\n\s*([\d,]+円[^\n]*)/) || [])[2], pr = (t.match(/提案数\n\s*(\d+)/) || [])[1]  // 報酬は円の付いた行だけ（上の別の行を拾わない）
    const good = ev && +ev[1] >= 5 && (+ev[2]) <= (+ev[1]) * 0.1 && hr && +hr[1] >= 50
    const ng = t.includes('提案できません') || /AI.{0,8}(使用)?(禁止|不可|NG)|生成AIの使用は避け/.test(t.split('この仕事に似ている')[0])
    if (good && !ng) console.log('★', id, '|', ti, '|', pay, '| 評価', ev[1] + '/' + ev[2], '| 発注', hr[1] + '% ' + hr[2] + '/' + hr[3], '| 提案', pr)
  }
  await b.close(); process.exit(0)
})().catch(e => { console.log('ERR', String(e.message || e).slice(0, 200)); process.exit(1) })
