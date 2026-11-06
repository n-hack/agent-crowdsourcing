// 【応募】ランサーズの提案画面に本文・計画の題名（20字以内）・計画・税抜の金額・納期を入れ、確認の画面まで進める。go のときだけ「提案する」を押す
// 入力: 案件ID・本文ファイル・題名・計画・税抜・YYYY/MM/DD・go ／ NDA=1（秘密保持の同意）・ATTACH=添付 ／ ログイン済みのブラウザ（profile の CDP）
// 出力: 入れた値・確認の画面の手がかり・<置き場>/shot/teian-<ID>.png。go で送れたら本文の控え・oubo-kiroku.tsv に「提案」の1行・teian-jiten.tsv に提案数
// 止まる条件(rc=2): 題名20字超・提案一覧／送る直前の記録／記録に同じ案件・同じ依頼主の同じ題名・分野/勧誘/できるか/成果の言い方/マナーの門・本文に穴（{…}）／rc=3 依頼主の型で本文が上書きされた／rc=4 提案の鍵が10分空かない
// 呼び方: node tools/teian.cjs <ID> <本文> <題名> <計画> <税抜> <YYYY/MM/DD> [go]（提案画面は1つの入口で1件しか持てないので、鍵で1件ずつにする）
require('./nhack-mon.cjs')()
const fs = require('fs'), path = require('path'), S = require('./settei.cjs')
const [id, txtf, title, plan, amount, deadline, go] = process.argv.slice(2)
if (!/^\d+$/.test(id || '') || !txtf || !title || !plan || !amount || !deadline) { console.log('使い方: node tools/teian.cjs <ID> <本文> <題名> <計画> <税抜> <YYYY/MM/DD> [go]'); process.exit(2) }
if ([...title].length > 20) { console.log('🔴 計画の題名が20字を超えています（' + [...title].length + '字）→ ランサーズが受け付けません'); process.exit(2) }
const honbun = fs.readFileSync(txtf, 'utf8').trim()
if (go === 'go' && /\{[^{}\n]{1,20}\}/.test(honbun)) { console.log('🔴 本文に埋めていない穴（{…}）がある・送らない'); process.exit(2) }
require('./jisseki-mon.cjs')([txtf], go); require('./manner-mon.cjs')(honbun, 'oubo', go)
const YF = path.join(S.DATA, 'teian-yoyaku.tsv'), rd = f => { try { return fs.readFileSync(f, 'utf8') } catch (e) { return '' } }
;(async () => {
  // 鍵：照合→送信→送る直前の記録までを1件ずつ（同じ案件に2本が同時に照らすと両方通るため・鍵は5分で古いとみなす）
  const L = path.join(S.DATA, '.teian-lock'), t0 = Date.now(); fs.mkdirSync(S.DATA, { recursive: true })
  for (;;) { try { fs.mkdirSync(L); fs.writeFileSync(L + '/who', id + ' ' + process.pid); break } catch (e) { let age = 0; try { age = Date.now() - fs.statSync(L).mtimeMs } catch (_) {} if (age > 300000) { fs.rmSync(L, { recursive: true, force: true }); continue } if (Date.now() - t0 > 600000) { console.log('🔴 提案の鍵が10分空かない'); process.exit(4) } await new Promise(r => setTimeout(r, 1500)) } }
  process.on('exit', () => { try { if (fs.readFileSync(L + '/who', 'utf8').startsWith(id + ' ' + process.pid)) fs.rmSync(L, { recursive: true, force: true }) } catch (_) {} })
  const b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 90000 }); const p = await S.tab(b, process.env.TAB_NAME || 'teian'); p.on('dialog', d => d.accept().catch(() => {}))
  const owari = async rc => { await b.close().catch(() => {}); process.exit(rc) }
  await p.goto('https://www.lancers.jp/mypage/proposals', { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(3000)
  const mine = await p.evaluate(() => { const L = document.body.innerText.split('\n').map(x => x.trim()).filter(Boolean); return [...document.querySelectorAll('a[href*="/work/detail/"]')].map(a => { const t = a.innerText.trim(); let k = L.indexOf(t), c = ''; if (k >= 0) for (let m = k + 1; m < Math.min(L.length, k + 12); m++) if (/^\d+$/.test(L[m])) { c = L[m + 1] || ''; break } return [(a.href.match(/detail\/(\d+)/) || [])[1], t, c] }) })
  await p.goto(`https://www.lancers.jp/work/detail/${id}`, { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(2500)
  const jt = (await p.locator('body').innerText()).replace(/\s+/g, ' ')
  const jtHon = jt.split(/この仕事に似ている|さんにおすすめの似ている仕事/)[0]  // 頁の下の「似ている仕事」の欄に自分が出した仕事が並ぶ → 本文の側だけで照らす
  require('./bunya-mon.cjs')(jt, go, id)
  const why = []
  if (mine.some(([jid]) => jid === id)) why.push('提案一覧に同じ案件')
  if (rd(YF).split('\n').some(l => l.split('\t')[2] === id)) why.push('送る直前の記録に同じ案件')
  if (S.ouboZumi('ランサーズ').has(id)) why.push('応募の記録に提案の行')
  if (why.length && process.env.DUP_OK !== '1') { console.log('🔴 同じ案件に提案済み（' + why.join('／') + '）→ 止めます'); return owari(2) }
  const hit = mine.filter(([jid, t, c]) => jid !== id && t && t.length > 6 && c && jtHon.includes(t) && jtHon.includes(c))
  console.log('二重提案の照合 提案一覧', mine.length, '件 ／ 当たり', hit.length); hit.forEach(h => console.log('  🟡', h.join(' | ')))
  if (hit.length && go === 'go' && process.env.DUP_OK !== '1') { console.log('🔴 止めました：同じ依頼主の同じ題名に提案済み。続けるなら DUP_OK=1'); return owari(2) }
  const ky = require('./kanyu-mon.cjs')(jtHon); if (ky.kanyu) { console.log('🔴 講座を売る型の印が重なった（' + ky.hits.join('／') + '）'); if (go === 'go' && process.env.KANYU_OK !== '1') return owari(2) }
  const dk = require('./dekiru-mon.cjs')(jtHon); if (dk.length) { console.log('🔴 エージェントだけではやり切れない条件（' + dk.join('／') + '）'); if (go === 'go' && process.env.DEKIRU_OK !== '1') return owari(2) }
  const n = (jt.match(/提案数\s*(\d+)\s*件/) || [])[1], m = jt.match(/開始：\s*(\d{4})年(\d{2})月(\d{2})日(?:\s*(\d{2}):(\d{2}))?/)
  const jiten = [n ?? '', m ? `${m[1]}-${m[2]}-${m[3]} ${m[4] ?? '--'}:${m[5] ?? '--'}` : '', m && m[4] ? ((Date.now() - new Date(`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:00+09:00`)) / 36e5).toFixed(1) : '']
  console.log('出す時点 提案数', jiten[0] || '（取れず）', '／ 掲載', jiten[1] || '（取れず）', '／ 経過h', jiten[2] || '（時刻なし）'); if (+jiten[0] > 20) console.log(`🟡 提案数 ${jiten[0]}件（20件以下のうちに出す目安・docs/05）`)
  await p.goto(`https://www.lancers.jp/work/propose_start/${id}?proposeReferer=`, { waitUntil: 'domcontentloaded' })
  // 依頼主が提案文の型を置いている頁では、型が後から入って本文を上書きする → 入りきるのを待ってから入れ、送る前に自分の本文か確かめる
  await p.waitForSelector('textarea[name="data[Proposal][description]"]', { timeout: 20000 }); await p.waitForTimeout(3000)
  await p.fill('textarea[name="data[Proposal][description]"]', honbun)
  if (process.env.ATTACH) { const at = require('./mieru-mon.cjs')(process.env.ATTACH, go); await p.locator('input[type=file]').first().setInputFiles(at); await p.waitForTimeout(4000); console.log('添付:', at.split('/').pop(), '→ 画面に名前', (await p.locator('body').innerText()).includes(at.split('/').pop())) }
  const ai = p.locator('label').filter({ hasText: '生成AIを使用している' }).first(); if (await ai.count()) { await ai.click(); console.log('生成AI: 使用している を選択') }
  if (process.env.NDA) { await p.locator('label').filter({ hasText: '秘密保持契約書の内容を確認した上で同意します' }).first().click(); console.log('秘密保持の同意を押した') }
  const tIn = p.locator('fieldset').filter({ hasText: 'タイトル' }).first().locator('input'), dIn = p.locator('.react-datepicker__input-container input').first()
  const ta = p.locator('textarea:not([name])'), num = p.locator('input[type=number]:not([name])')
  await tIn.fill(title); await ta.nth(0).fill(plan); await num.nth(0).fill(String(amount))
  await dIn.click(); await dIn.fill(deadline); await p.keyboard.press('Enter'); await p.waitForTimeout(500); await p.keyboard.press('Escape')
  console.log('入れた値', await tIn.inputValue(), '|', await dIn.inputValue(), '|', await num.nth(0).inputValue())
  if ((await p.inputValue('textarea[name="data[Proposal][description]"]')).trim() !== honbun || (await tIn.inputValue()) !== title) { console.log('🔴 本文か題名が入れた物と違う（依頼主の型で上書きされた）→ 送らずに止めます'); return owari(3) }
  await p.locator('input[name=send]').click(); await p.waitForTimeout(5000)
  console.log('次の頁', p.url(), '|', ((await p.locator('body').innerText()).replace(/\s+/g, ' ').match(/.{0,40}(エラー|入力してください|確認|手数料|受取).{0,60}/g) || []).slice(0, 6))
  const shot = path.join(S.DATA, 'shot', `teian-${id}.png`); fs.mkdirSync(path.dirname(shot), { recursive: true }); await p.screenshot({ path: shot, fullPage: true })
  if (go !== 'go') { console.log('go なし：確認の画面までで止めた（下書き）', shot); return owari(0) }
  S.tsuika(YF, [new Date().toISOString(), 'ランサーズ', id, process.pid].join('\t') + '\n')
  await p.getByRole('button', { name: /提案する|この内容で提案/ }).or(p.locator('input[type=submit][value*=提案]')).first().click(); await p.waitForTimeout(5000)
  const kanryo = /propose_finish/.test(p.url())
  if (!kanryo) console.log('🔴 完了の頁に進んでいない（送れていない）:', ((await p.locator('body').innerText()).replace(/\s+/g, ' ').match(/.{0,60}(エラー|できません|してください|上限|制限|不正|失敗).{0,60}/g) || []).slice(0, 6))
  const dst = path.join(S.DATA, 'oubo', id + '.txt'); fs.mkdirSync(path.dirname(dst), { recursive: true }); if (path.resolve(txtf) !== dst) fs.copyFileSync(txtf, dst)
  const ima = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString()
  S.tsuika(path.join(S.DATA, 'teian-jiten.tsv'), [ima.slice(0, 19), 'ランサーズ', id, ...jiten].join('\t') + '\n')
  if (!fs.existsSync(S.kiroku)) S.tsuika(S.kiroku, '日付\t場\t案件ID\t中身\t提示額\t月額\t状態\n')
  S.tsuika(S.kiroku, [ima.slice(0, 10), 'ランサーズ', id, title.replace(/\t/g, ' '), amount, '', kanryo ? '提案' : '止まった：完了の頁に進まず'].join('\t') + '\n')
  console.log('送信後', p.url()); return owari(kanryo ? 0 : 3)
})().catch(e => { console.log('ERR', String(e.message || e).slice(0, 400)); process.exit(1) })
