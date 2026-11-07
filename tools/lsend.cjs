// 【返事】ランサーズのメッセージの部屋（/mypage/message?boardId=）へ返事を1通入れる。go のときだけ送り、頁を開き直して本文の真ん中20字が載ったかを見る
// 入力: boardId・本文ファイル・go ／ログイン済みのブラウザ（profile の CDP）
// 出力: 入力欄の数・送信の釦の状態・載ったか。<置き場>/henji/lsend.log に1行（頁の「メッセージの送信に失敗しました」は送る前から出ている固定の文＝判定に使わない）
// 止まる条件: マナーの門 rc=2／送信の釦が開かない rc=3／載っていない rc=2
// 呼び方: node tools/lsend.cjs <boardId> <本文> [go]
const fs = require('fs'), path = require('path'), S = require('./settei.cjs')
const [bid, f, go] = process.argv.slice(2)
if (!/^\d+$/.test(bid || '') || !f) { console.log('使い方: node tools/lsend.cjs <boardId> <本文> [go]'); process.exit(2) }
const body = fs.readFileSync(f, 'utf8').trim(); require('./jisseki-mon.cjs')([f], go); require('./manner-mon.cjs')(body, 'henji', go)
;(async () => {
  const b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 90000 }); const p = await S.tab(b, process.env.TAB_NAME || 'lsend'); p.setDefaultTimeout(20000)
  const owari = async rc => { await b.close().catch(() => {}); process.exit(rc) }
  const url = 'https://www.lancers.jp/mypage/message?boardId=' + bid
  await p.goto(url, { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(5000)
  const ta = p.locator('textarea[placeholder="メッセージを入力してください"]').first(); console.log('入力欄', await ta.count())
  if (go !== 'go') { console.log('go なし：書き込まずに止めます（本文', body.length, '字）'); return owari(0) }
  for (const t of ['今後表示しない', '閉じる']) { const c = p.locator('.MuiDialog-root button', { hasText: t }).first(); if (await c.count() && await c.isVisible().catch(() => false)) { await c.click().catch(() => {}); await p.waitForTimeout(800) } }  // お知らせの窓が欄に重なることがある
  await ta.click(); await p.keyboard.insertText(body); await p.waitForTimeout(1200)  // fill だけでは送信の釦が開かない（打ち込みの合図で開く作り）
  const btn = p.locator('button', { hasText: /^送信$/ }).first(); if (await btn.isDisabled()) { console.log('🔴 送信の釦が開かないので送らずに止めます'); return owari(3) }
  await btn.click(); await p.waitForTimeout(6000); await p.goto(url, { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(5000)
  // 頭20字は宛名と挨拶で毎回同じ＝前の便が残っていれば載らなくても当たる → 真ん中20字で見る
  const t = (await p.evaluate(() => document.body.innerText)).replace(/\s+/g, ''), x = body.replace(/\s+/g, ''), head = x.slice(Math.max(0, Math.floor(x.length / 2) - 10), Math.floor(x.length / 2) + 10), ok = t.includes(head)
  console.log('載ったか', ok, '（真ん中20字：', head, '）')
  S.tsuika(path.join(S.DATA, 'henji', 'lsend.log'), `${new Date().toISOString()}\t${bid}\t${f}\t載った=${ok}\n`)
  return owari(ok ? 0 : 2)
})().catch(e => { console.log('ERR', String(e.message || e).slice(0, 200)); process.exit(1) })
