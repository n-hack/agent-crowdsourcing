// 【応募】クラウドワークスの応募画面に本文・金額・納期（時給の募集なら時給と週の上限）を入れる。go のときだけ「応募する」を押す
// 入力: 案件ID・本文ファイル・税抜の金額（時給の募集なら時給）・納期 YYYY-M-D・添付（無ければ -）・go ／ ログイン済みのブラウザ（profile の CDP）
// 出力: 入れた値と受取の表示。go で送れたら <置き場>/oubo/<ID>.txt に本文の控え・oubo-kiroku.tsv に「応募」の1行・teian-jiten.tsv に出した時点の応募人数
// 止まる条件(rc=2): 記録に同じ ID の応募・応募済み一覧の控えに同じ依頼主の同じ題名・控えが10行未満で照らせない・自社の依頼主・分野/できるか/勧誘/成果の言い方/マナーの門・本文に穴（{…}）
// 呼び方: node tools/cwapply.cjs <ID> <本文> <金額> <YYYY-M-D> [添付|-] [go]（外す変数 DUP_OK・KANYU_OK・DEKIRU_OK は理由を記録に書いてから）
const fs = require('fs'), path = require('path'), S = require('./settei.cjs')
const [id, txtf, amount, dl, attach0, go] = process.argv.slice(2)
if (!/^\d+$/.test(id || '') || !txtf || !amount) { console.log('使い方: node tools/cwapply.cjs <ID> <本文> <金額> <YYYY-M-D> [添付|-] [go]'); process.exit(2) }
const honbun = fs.readFileSync(txtf, 'utf8').trim()
if (go === 'go' && /\{[^{}\n]{1,20}\}/.test(honbun)) { console.log('🔴 本文に埋めていない穴（{…}）がある・送らない'); process.exit(2) }
const attach = require('./mieru-mon.cjs')(attach0, go)
require('./jisseki-mon.cjs')([txtf], go); require('./manner-mon.cjs')(honbun, 'oubo', go)
if (go === 'go' && S.ouboZumi().has(String(id)) && process.env.DUP_OK !== '1') { console.log('🔴 止めました：応募の記録に同じ案件の応募行がある（並べて回したときの二重を防ぐ）'); process.exit(2) }
// 応募済み一覧の控え（<置き場>/cw-joutai-*.tsv）を10分より古ければ取り直す（二重応募の照合に使う）
const snapDir = S.DATA, snaps = () => (fs.existsSync(snapDir) ? fs.readdirSync(snapDir) : []).filter(f => /^cw-joutai-.*\.tsv$/.test(f)).sort()
if (go === 'go') { const last = snaps().pop()
  if (!last || Date.now() - fs.statSync(path.join(snapDir, last)).mtimeMs > 10 * 60 * 1000) { const d = new Date(), z = n => String(n).padStart(2, '0'), nf = path.join(snapDir, `cw-joutai-${d.getFullYear()}${z(d.getMonth() + 1)}${z(d.getDate())}-${z(d.getHours())}${z(d.getMinutes())}.tsv`)
    try { console.log(require('child_process').execFileSync('node', [path.join(__dirname, 'cw-oubo-joutai.cjs'), nf], { timeout: 180000 }).toString().trim()) } catch (e) { console.log('🟡 控えを取り直せなかった（古い控えで照らす）', String(e.stdout || e.message).slice(0, 120)) } } }
;(async () => {
  const b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 90000 }); const p = await S.tab(b, process.env.TAB_NAME || 'cwapply')
  p.setDefaultTimeout(15000); p.on('dialog', d => d.accept().catch(() => {}))
  const owari = async rc => { await b.close().catch(() => {}); process.exit(rc) }
  // 案件の公開頁を全部読み、門を当てる（応募画面の下見は「続きを読む」で切れるため）
  await p.goto(`https://crowdworks.jp/public/jobs/${id}`, { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(2000)
  const jt = (await p.locator('body').innerText()).replace(/\s+/g, ' ')
  for (const x of (S.P['自社の依頼主ID'] || []).filter(Boolean)) if (jt.includes(x)) { console.log('🔴 止めました：発注者が自社の募集'); return owari(2) }
  require('./bunya-mon.cjs')(jt, go, id)
  const ky = require('./kanyu-mon.cjs')(jt); if (ky.kanyu) { console.log('🔴 講座を売る型の印が重なった（' + ky.hits.join('／') + '）'); if (go === 'go' && process.env.KANYU_OK !== '1') return owari(2) }
  const dk = require('./dekiru-mon.cjs')(jt); if (dk.length) { console.log('🔴 エージェントだけではやり切れない条件（' + dk.join('／') + '）'); if (go === 'go' && process.env.DEKIRU_OK !== '1') return owari(2) }
  const n = (jt.match(/応募した人\s*(\d+)\s*人/) || [])[1], m = jt.match(/掲載日\s*(\d{4})年(\d{2})月(\d{2})日/), jiten = [n ?? '', m ? `${m[1]}-${m[2]}-${m[3]}` : '', '']
  console.log('出す時点 応募した人', n ?? '（取れず）', '／ 掲載日', jiten[1] || '（取れず）'); if (+n > 20) console.log(`🟡 応募した人 ${n}人（20人以下のうちに出す目安・docs/05）`)
  await p.goto(`https://crowdworks.jp/proposals/new?job_offer_id=${id}`, { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(4000)
  // 同じ依頼主の同じ題名の出し直しに二重応募しない：応募済み一覧の控えと題名＋依頼主で照らす。控えが空・要約だけなら照合が黙って0件になるので止める
  { const snap = snaps().pop(); const rows = snap ? fs.readFileSync(path.join(snapDir, snap), 'utf8').split('\n').slice(1).map(l => l.split('\t')).filter(c => c.length > 3) : []
    if (rows.length < 10 && go === 'go' && process.env.DUP_OK !== '1') { console.log('🔴 止めました：応募済み一覧の控え', snap || '（無い）', 'の行が', rows.length, '＝照らせない（応募が10件未満のうちは DUP_OK=1 で）'); return owari(2) }
    const t = (await p.locator('body').innerText()).replace(/\s+/g, ' ')
    const hit = rows.filter(c => c[0].length > 6 && t.includes(c[0].replace(/のお仕事\(.*?\)$/, '').trim()) && t.includes(c[2].trim()))
    console.log('二重応募の照合', snap || '（控えなし）', '当たり', hit.length); hit.forEach(c => console.log('  🟡', c[3], '|', c[2], '|', c[0].slice(0, 50)))
    if (hit.length && go === 'go' && process.env.DUP_OK !== '1') { console.log('🔴 止めました：同じ依頼主の同じ題名に応募済み。続けるなら DUP_OK=1'); return owari(2) } }
  await p.locator('input[name=without_condition][value=false]').check({ force: true }).catch(() => {})
  // 時給の募集は固定の金額欄が隠れ、時給と週の上限時間だけが出る → 金額を時給として入れる（上限は HOURS・無ければ10）
  const jikyu = await p.locator('input[name="hourly_wage_dummy[]"]').first().isVisible().catch(() => false)
  const amt = p.locator(jikyu ? 'input[name="hourly_wage_dummy[]"]' : 'input[name="amount_dummy[]"]').first(); await amt.fill(''); await amt.type(String(amount), { delay: 20 })
  if (jikyu) { const hl = p.locator('input[name="proposal[conditions_attributes][0][hours_limit]"]'); await hl.fill(''); await hl.type(String(process.env.HOURS || 10), { delay: 20 }); console.log('時給の画面：時給', amount, '／週の上限', process.env.HOURS || 10, '時間') }
  else { const [y, mo, d] = String(dl || '').split('-'); const base = 'proposal[conditions_attributes][0][milestones_attributes][0][deadline'
    await p.selectOption(`select[name="${base}(1i)]"]`, y).catch(e => console.log('年', e.message.slice(0, 60)))
    await p.selectOption(`select[name="${base}(2i)]"]`, String(Number(mo))).catch(e => console.log('月', e.message.slice(0, 60)))
    await p.selectOption(`select[name="${base}(3i)]"]`, String(Number(d))).catch(e => console.log('日', e.message.slice(0, 60))) }
  await p.fill('textarea[name="proposal[conditions_attributes][0][message_attributes][body]"]', honbun)
  if (attach && attach !== '-') await p.setInputFiles('input[name="proposal[conditions_attributes][0][message_attributes][attachments_attributes][][file]"]', attach)
  await p.waitForTimeout(1000)
  console.log('金額', await amt.inputValue(), '| 受取の表示', (await p.locator('body').innerText()).replace(/\s+/g, ' ').match(/(受取金額|メンバー報酬)[^円]{0,30}円/)?.[0])
  if (go !== 'go') { console.log('go なし：入れただけで送っていない（下書き）'); return owari(0) }
  await p.locator('input[name=commit][value=応募する]').click(); await p.waitForTimeout(6000)
  const t = (await p.locator('body').innerText({ timeout: 60000 }).catch(e => '（送信後の頁が読めず・押した後）' + e.message.slice(0, 60))).replace(/\s+/g, ' ')
  const kanryo = /応募が完了|応募しました/.test(t) || /\/proposals\/\d/.test(p.url())
  console.log('送信後', p.url(), (t.match(/.{0,30}(応募が完了|応募しました|エラー|入力してください).{0,40}/g) || []).slice(0, 3))
  const dst = path.join(S.DATA, 'oubo', id + '.txt'); fs.mkdirSync(path.dirname(dst), { recursive: true }); if (path.resolve(txtf) !== dst) fs.copyFileSync(txtf, dst)
  const ima = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString()
  S.tsuika(path.join(S.DATA, 'teian-jiten.tsv'), [ima.slice(0, 19), 'クラウドワークス', id, ...jiten].join('\t') + '\n')
  if (!fs.existsSync(S.kiroku)) S.tsuika(S.kiroku, '日付\t場\t案件ID\t中身\t提示額\t月額\t状態\n')
  S.tsuika(S.kiroku, [ima.slice(0, 10), 'クラウドワークス', id, (jt.match(/^(.{0,40}?)の仕事/) || [, ''])[1].replace(/\t/g, ' '), amount, '', kanryo ? '応募' : '止まった：送信後の頁で完了を確かめられず'].join('\t') + '\n')
  return owari(kanryo ? 0 : 3)
})().catch(e => { console.log('ERR', String(e.message || e).slice(0, 300)); process.exit(1) })
