// 【下書きの確かめ】埋めた応募の下書きを、送る段（オーナーの OK と --go）の前に1本ずつ確かめる（docs/05 の手順6・読むだけ）
// 入力: 下書きの .txt（引数・複数可・無ければ <置き場>/oubo-bun/ の全部）と同じ名前の .json（金額＝税抜・納期）／<置き場>/junkai/ の巡回の tsv（予算の帯と依頼主の表示名）／templates/oubo-kihon.txt
// 見る物: ①穴の残り {…} ②型の行の残り（型の「進め方」の固定の行がそのまま）③宛名の崩れ ④ .json の金額・納期 ⑤金額が本文の予算の帯の中か（帯は税込）
//        ⑥本文の「◯円（税込）／（税抜）」と .json の金額が合うか ⑦マナー・AI 臭さの門（manner-mon.cjs oubo）⑧成果の言い方の門（jisseki-mon.cjs）
// 出力: 下書きごとに ✅ か、🔴 の理由の行。最後に「通った N ／ 止めた M」
// 止まる条件: 🔴 が1本でもあれば rc=2（直してから打ち直す）。帯は tsv に無ければ公開頁を読む。読めなければ「帯を照らせず」の 🔴（照らせていない物を通さない）
// 呼び方: node tools/shitagaki-kakunin.cjs [<置き場>/oubo-bun/cw-<ID>.txt …]
require('./nhack-mon.cjs')()
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process'), S = require('./settei.cjs')
const T = __dirname, BUN = path.join(S.DATA, 'oubo-bun'), JK = path.join(S.DATA, 'junkai')
const files = process.argv.slice(2).length ? process.argv.slice(2) : (fs.existsSync(BUN) ? fs.readdirSync(BUN).filter(f => /^(cw|lancers)-\d+\.txt$/.test(f)).sort().map(f => path.join(BUN, f)) : [])
if (!files.length) { console.log('🔴 確かめる下書きが無い（' + BUN + '）'); process.exit(2) }
// 型の「進め方」の固定の行（穴の無い番号つきの行）＝この募集に合わせて書き直す行
const KATA = fs.readFileSync(path.join(T, '..', 'templates', 'oubo-kihon.txt'), 'utf8').split('\n').map(s => s.trim()).filter(s => /^\d+．/.test(s) && !/\{/.test(s))
// 巡回の tsv から ID の行（新しい tsv を先に）
const tsvRow = id => {
  if (!fs.existsSync(JK)) return null
  for (const f of fs.readdirSync(JK).filter(f => /^20\d{6}-\d{4}\.tsv$/.test(f)).sort().reverse()) {
    const r = fs.readFileSync(path.join(JK, f), 'utf8').split('\n').map(l => l.split('\t')).find(c => c[1] === id)
    if (r) return r
  }
  return null
}
// 予算の帯（税込）：tsv の「固定0-82500.0」／公開頁の「固定報酬制 30,000円 〜 50,000円」。帯の無い募集（相談・時給）は null
const obi = async (id, r) => {
  if (r && r[2]) { const m = r[2].match(/^固定([\d.]+)-([\d.]+)$/); return m && (+m[1] > 0 || +m[2] > 0) ? { min: +m[1], max: +m[2] || Infinity, doko: '巡回の tsv' } : null }
  try {
    const t = (await (await fetch('https://crowdworks.jp/public/jobs/' + id, { headers: { 'User-Agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(30000) })).text()).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ')
    // 頁の書き方は4通り（2026-11-06 の実物）：「30,000円 〜 50,000円」「〜 5,000円」「5,000円 〜」「82,500円」（1つだけ＝上限。巡回の tsv では 0-82500）
    const g = t.match(/固定報酬制\s*(?:([\d,]+)\s*円\s*)?(〜\s*(?:([\d,]+)\s*円)?)?/)
    if (g && (g[1] || g[3])) return { min: g[2] ? yen(g[1] || 0) : 0, max: g[3] ? yen(g[3]) : g[2] ? Infinity : yen(g[1]), doko: '公開頁' }
    if (/固定報酬制\s*(?:ワーカーと相談|相談)|時間単価制/.test(t)) return null
    return undefined  // 書き方が読めない＝照らせず（黙って通さない）
  } catch (e) { return undefined }
}
const yen = s => +String(s).replace(/,/g, '')
;(async () => {
  let ok = 0, ng = 0
  for (const f of files) {
    const red = [], txt = fs.readFileSync(f, 'utf8'), L = txt.split('\n'), j = f.replace(/\.txt$/, '.json')
    const ba = (path.basename(f).match(/^(cw|lancers)-/) || [])[1], id = (path.basename(f).match(/(\d+)\.txt$/) || [])[1]
    // ① 穴の残り
    const ana = txt.match(/\{[^{}\n]{1,20}\}/g) || []; if (ana.length) red.push(`穴が ${ana.length} つ残っている：${ana.join(' ')}`)
    // ② 型の行の残り
    for (const k of KATA) if (L.some(l => l.trim() === k)) red.push(`型の行がそのまま：「${k}」（この募集に合う1文に直す・docs/05 手順5）`)
    // ③ 宛名（1行目）
    const a = (L[0] || '').trim(), r = ba === 'cw' ? tsvRow(id) : null, mei = r && r[3] && r[3] !== '-' ? r[3] : ''
    if (/様の\s*(ご)?担当者|様\s*(ご)?担当者様|御中\s*(様|ご担当者様)|様\s*御中|様様/.test(a)) red.push(`宛名が崩れている：「${a}」（docs/05 の宛名の決め方）`)
    else if (/^(株式会社|有限会社|合同会社|一般社団法人|一般財団法人|\(株\)|（株）)\s*(様|ご担当者様)$|^\s*様$/.test(a)) red.push(`宛名に名前が無い：「${a}」（表示名をそのまま写す）`)
    else if (/(株式会社|有限会社|合同会社|社団法人|財団法人|\(株\)|（株）)[^\s]*様$/.test(a)) red.push(`会社名に直接「様」：「${a}」（会社・屋号は「<表示名> ご担当者様」）`)
    else if (!/(様|御中)$/.test(a)) red.push(`1行目に宛名が無い：「${a.slice(0, 20)}」`)
    else if (mei && !a.startsWith(mei) && !/^ご担当者様$/.test(a)) red.push(`宛名が表示名「${mei}」と違う：「${a}」`)
    // ④ .json の金額・納期
    let J = {}; try { J = JSON.parse(fs.readFileSync(j, 'utf8')) } catch (e) { red.push('.json が読めない（' + path.basename(j) + '）') }
    const kin = Number(J['金額']), nou = String(J['納期'] || '')
    if (!(kin > 0)) red.push('.json の金額（税抜の数字）が空')
    const d = nou.match(/^(20\d{2})-(\d{1,2})-(\d{1,2})$/), kyou = new Date(new Date().toDateString())
    if (!d) red.push('.json の納期が YYYY-M-D でない：' + (nou || '空'))
    else if (new Date(+d[1], +d[2] - 1, +d[3]) < kyou) red.push('.json の納期が今日より前：' + nou)
    // ⑤ 予算の帯（帯は税込・.json の金額は税抜）
    if (kin > 0 && ba === 'cw') {
      const b = await obi(id, r)
      if (b === undefined) red.push('帯を照らせず（巡回の tsv に無く、公開頁も読めない）')
      else if (b) { const zei = Math.round(kin * 1.1); if (zei < b.min || zei > b.max) red.push(`金額が予算の帯の外：税込 ${zei.toLocaleString()}円 ／ 帯 ${b.min.toLocaleString()}〜${b.max.toLocaleString()}円（${b.doko}）`) }
    }
    // ⑥ 本文の金額と .json
    if (kin > 0) {
      for (const m of txt.matchAll(/([\d,]+)\s*円\s*[（(]税込[)）]/g)) if (Math.abs(yen(m[1]) - Math.round(kin * 1.1)) > 1) red.push(`本文の税込 ${m[1]}円 が .json の金額 ${kin}（税抜）×1.1 と合わない`)
      for (const m of txt.matchAll(/([\d,]+)\s*円\s*[（(]税抜[)）]/g)) if (yen(m[1]) !== kin) red.push(`本文の税抜 ${m[1]}円 が .json の金額 ${kin} と合わない`)
    }
    // ⑦ マナー・AI 臭さ ⑧ 成果の言い方（どちらも何も出さなければ通る）
    const mm = require('./manner-mon.cjs'), log = console.log; let out = []
    console.log = (...x) => out.push(x.join(' '))
    let res; try { res = mm(txt, 'oubo') } finally { console.log = log }
    for (const x of (res && res.red) || []) red.push('マナー: ' + x)
    const yel = ((res && res.yel) || []).map(x => '🟡 マナー: ' + x)  // 🟡 は止めない（出すだけ）
    try { const o = execFileSync('node', ['-e', `require(${JSON.stringify(path.join(T, 'jisseki-mon.cjs'))})([${JSON.stringify(f)}])`], { encoding: 'utf8' }).trim(); if (o) red.push('成果の言い方: ' + o.replace(/\n/g, ' ／ ')) } catch (e) { red.push('jisseki-mon が落ちた rc=' + e.status) }
    if (red.length) { ng++; console.log(`🔴 ${path.basename(f)}`); for (const x of red) console.log('   ' + x) }
    else { ok++; console.log(`✅ ${path.basename(f)}（金額 ${kin.toLocaleString()}円 税抜 ／ 納期 ${nou}）`) }
    for (const y of yel) console.log('   ' + y)
  }
  console.log(`通った ${ok} ／ 止めた ${ng}`); process.exit(ng ? 2 : 0)
})()
