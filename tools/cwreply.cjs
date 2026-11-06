// 【返事】CW のメッセージ（応募・相談・契約の部屋）に返事を1通入れる。go のときだけ投稿し、頁を開き直して載ったかを見る
// 入力: 部屋（messages の番号か proposals/<番号>）・本文ファイル・go ／ ATTACH=添付 ／ 相手ごとの台帳 <置き場>/aite/<部屋>.md（決まったこと・約束・期限）
// 出力: 台帳の中身・入れた字数・載ったか。本文に約束の語（本日中・までに・お送りいたします 等）があれば <置き場>/yakusoku.tsv に「未」で積む
// 止まる条件(rc=2): 台帳が無いのに go（AITE_OK=1 で外す）・マナー／成果の言い方の門・本文の欄が1つでない・送った後に頁に載っていない
// 呼び方: [ATTACH=ファイル] node tools/cwreply.cjs <部屋> <本文> [go]
const fs = require('fs'), path = require('path'), S = require('./settei.cjs')
const [id, f, go] = process.argv.slice(2)
if (!id || !f) { console.log('使い方: node tools/cwreply.cjs <部屋> <本文> [go]'); process.exit(2) }
const A = path.join(S.DATA, 'aite', id.replace(/\//g, '_') + '.md')
if (fs.existsSync(A)) console.log('📒 台帳 ' + A + '\n' + fs.readFileSync(A, 'utf8'))
else { console.log('🔴 台帳がありません：' + A + '（決まったこと・約束・期限を書いてから送る）'); if (go === 'go' && process.env.AITE_OK !== '1') process.exit(2) }
const body = fs.readFileSync(f, 'utf8').trim(); require('./jisseki-mon.cjs')([f], go); require('./manner-mon.cjs')(body, 'henji', go); require('./keiyaku-mon.cjs')(body, id, go)  // 契約を受ける文は、できると確かめた記録（<置き場>/keiyaku/<部屋>.md）があるときだけ送る（docs/06）
;(async () => {
  const b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 90000 }); const p = await S.tab(b, process.env.TAB_NAME || 'cwreply'); p.on('dialog', d => d.accept().catch(() => {}))
  let rc = 0
  try {
    const u = 'https://crowdworks.jp/' + (id.includes('/') ? id : 'messages/' + id); await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(4000)
    // 頁に同じ名前の欄が複数（隠れた納品完了報告など）ある → 見える欄だけ数える。欄の取り違えで空の投稿をしないため
    const ta = p.locator('textarea[name="message[body]"]:visible')
    if (await ta.count() !== 1) { console.log('🔴 本文の欄が', await ta.count(), '個'); rc = 2; throw 0 }
    await ta.fill(body); console.log('入れた', (await ta.inputValue()).length, '字')
    if (process.env.ATTACH) { const at = require('./mieru-mon.cjs')(process.env.ATTACH, go); await ta.locator('xpath=ancestor::form').locator('input[type=file]').first().setInputFiles(at); await p.waitForTimeout(4000); console.log('添付の名前が画面に', (await p.evaluate(() => document.body.innerText)).includes(at.split('/').pop())) }
    if (go !== 'go') { console.log('go なし：送りません'); throw 0 }
    await p.getByRole('button', { name: 'メッセージを投稿する' }).first().click(); await p.waitForTimeout(6000)
    await p.goto(u, { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(3500); const t = await p.evaluate(() => document.body.innerText)
    const ok = t.includes(body.split('\n').filter(l => l.length > 15)[0] || body.slice(0, 20)); console.log(ok ? '✅ 頁に載った' : '🔴 頁に載っていない'); rc = ok ? 0 : 2
    if (ok) { const ys = body.split('\n').filter(l => /本日中|明日中|今日中|当日中|その日のうちに|までに|お知らせいたします|ご連絡いたします|お送りいたします|お答えいたします/.test(l))
      if (ys.length) { const nm = fs.existsSync(A) ? fs.readFileSync(A, 'utf8').split('\n')[0].replace(/^#\s*/, '').split('（')[0].trim() : ''
        S.tsuika(path.join(S.DATA, 'yakusoku.tsv'), ys.map(l => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16) + '\t' + id + '\t未\t' + (nm ? nm + '：' : '') + l.trim()).join('\n') + '\n')
        console.log('📌 約束 ' + ys.length + '件を yakusoku.tsv へ（果たしたら「未」→「済」）') } }
  } catch (e) { if (e !== 0) { console.log('ERR', String(e.message || e).slice(0, 200)); rc = 1 } }
  await b.close().catch(() => {}); process.exit(rc)
})()
