// 【出し漏れの検算】案件の頁を開き、こちらが応募・提案済みかを相手のサイトの表示で確かめる（読むだけ）。記録ではなく相手の表示で照らす
// 入力: ID の一覧ファイル（7桁以下＝ランサーズ・それより長い＝CW）・出し先 tsv・CW の応募一覧の題名 tsv（cw-oubo-ids.cjs の出力・CW の頁には「応募済み」が出ないため題名で照らす）
// 出力: 1行1件「ID<TAB>場<TAB>済|未|終了|不明<TAB>題名<TAB>頁の手がかり」。済・終了の行は dashi-more.py が漏れから外す（出し先を <置き場>/dashi-zumi.tsv にする）
// 止まる条件: 引数が足りない rc=2／ブラウザにつなげない rc=1
// 呼び方: node tools/oubo-zumi-kakunin.cjs <ID の一覧> <置き場>/dashi-zumi.tsv <置き場>/cw-oubo-ids.tsv
require('./nhack-mon.cjs')()
const fs = require('fs'), S = require('./settei.cjs')
const [idf, outf, titf] = process.argv.slice(2)
if (!idf || !outf) { console.log('使い方: node tools/oubo-zumi-kakunin.cjs <ID の一覧> <出し先> [<CW の応募一覧の題名>]'); process.exit(2) }
;(async () => {
  const b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 90000 }); const p = await S.tab(b, 'oubo-zumi')
  const ids = fs.readFileSync(idf, 'utf8').split(/\s+/).filter(Boolean), out = []
  const nz = s => s.replace(/[\s　【】\[\]（）()「」・、。!！?？\/／|｜~〜ー-]/g, '').slice(0, 22)
  const titles = new Set((titf && fs.existsSync(titf) ? fs.readFileSync(titf, 'utf8') : '').split('\n').map(l => nz(l.split('\t')[1] || '')).filter(Boolean))
  for (const id of ids) {
    const lan = id.length <= 7, url = lan ? `https://www.lancers.jp/work/detail/${id}` : `https://crowdworks.jp/public/jobs/${id}`
    let t = ''
    try { await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 }); await p.waitForTimeout(1500); t = (await p.innerText('body')).replace(/\s+/g, ' ') } catch (e) { t = 'ERR ' + e.message }
    const h1 = lan ? '' : await p.$eval('h1', e => e.innerText).catch(() => '')
    const zumi = (h1 && titles.has(nz(h1.replace(/の仕事$/, '').replace(/\s+/g, ' ')))) || /応募済み|提案済み|提案内容を確認|あなたの提案/.test(t)
    const owari = /募集終了|募集は終了|掲載終了|締め切りました|この仕事は削除|ページが見つかりません|存在しません/.test(t)
    const han = zumi ? '済' : owari ? '終了' : /応募する|提案する|この仕事に応募/.test(t) ? '未' : '不明'
    const m = (t.match(/.{0,20}(応募済み?|提案済み?|募集終了|応募する|提案する).{0,20}/) || [''])[0]
    out.push([id, lan ? 'ランサーズ' : 'CW', han, h1.slice(0, 40), m].join('\t')); console.log(id, han, h1.slice(0, 40), m)
  }
  fs.writeFileSync(outf, out.join('\n') + '\n'); await b.close(); process.exit(0)
})().catch(e => { console.log('ERR', String(e.message || e).slice(0, 200)); process.exit(1) })
