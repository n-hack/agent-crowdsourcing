// 【下書きの確かめ】埋めた応募の下書きを、送る段（オーナーの OK と --go）の前に1本ずつ確かめる（docs/05 の手順6・読むだけ）
// 入力: 下書きの .txt（引数・複数可・無ければ <置き場>/oubo-bun/ の全部）と同じ名前の .json（金額＝税抜・納期）／<置き場>/junkai/ の巡回の tsv（予算の帯と依頼主の表示名）／templates/oubo-kihon.txt
// 見る物: ①穴の残り {…} ②型の行の残り（型の「進め方」の固定の行がそのまま）③宛名の崩れ ④ .json の金額・納期
//        ④-2 納期：本文の締切・日数（「◯日以内」「◯月◯日まで」）より後でないか／既定（契約の当日〜2日後）を超えるなら .json の「納期の理由」があるか／下書きの「◯日以内」「◯月◯日」と .json が合うか
//        ⑤金額が本文の予算の帯の中か（帯は税込）・帯の無い募集なら .json の「金額の根拠」（tools/cw-souba.py の1行）があるか
//        ⑥本文の「◯円（税込）／（税抜）」と .json の金額が合うか ⑦マナー・AI 臭さの門（manner-mon.cjs oubo）⑧成果の言い方の門（jisseki-mon.cjs）
// 出力: 下書きごとに ✅ か、🔴 の理由の行。最後に「通った N ／ 止めた M」
// 止まる条件: 🔴 が1本でもあれば rc=2（直してから打ち直す）。帯は tsv に無ければ公開頁を読む。読めなければ「帯を照らせず」の 🔴（照らせていない物を通さない）
// 呼び方: node tools/shitagaki-kakunin.cjs [<置き場>/oubo-bun/cw-<ID>.txt …]
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process'), S = require('./settei.cjs')
const T = __dirname, BUN = path.join(S.DATA, 'oubo-bun'), JK = path.join(S.DATA, 'junkai')
let files = process.argv.slice(2).length ? process.argv.slice(2) : (fs.existsSync(BUN) ? fs.readdirSync(BUN).filter(f => /^(cw|lancers)-\d+\.txt$/.test(f)).sort().map(f => path.join(BUN, f)) : [])
// 試し10回目：引数なしで打つと、見送りを記録した下書きも 🔴 のまま残り ✅ にならなかった → 記録の状態が「見送」の ID は外す（dashi-more.py と同じ見方・引数で名指しした物は外さない）
if (!process.argv.slice(2).length && fs.existsSync(S.kiroku)) {
  const mio = new Set(fs.readFileSync(S.kiroku, 'utf8').split('\n').map(l => l.split('\t')).filter(c => c.length >= 7 && /見送/.test(c[6])).flatMap(c => c[2].split('・').map(x => x.trim())))
  const mae = files.length; files = files.filter(f => !mio.has((path.basename(f).match(/-(\d+)\.txt$/) || [])[1]))
  if (mae > files.length) console.log(`見送りを記録した下書き ${mae - files.length} 本は外した（記録の状態が「見送」）`)
}
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
// 公開頁（1件1回だけ読む）。読めなければ null
const PEJI = {}
const peji = async id => {
  if (id in PEJI) return PEJI[id]
  try { PEJI[id] = (await (await fetch('https://crowdworks.jp/public/jobs/' + id, { headers: { 'User-Agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(30000) })).text()).replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ') }
  catch (e) { PEJI[id] = null }
  return PEJI[id]
}
const obi = async (id, r) => {
  if (r && r[2]) { const m = r[2].match(/^固定([\d.]+)-([\d.]+)$/); return m && (+m[1] > 0 || +m[2] > 0) ? { min: +m[1], max: +m[2] || Infinity, doko: '巡回の tsv' } : null }
  {
    const t = await peji(id); if (t === null) return undefined
    // 頁の書き方は4通り（2026-11-06 の実物）：「30,000円 〜 50,000円」「〜 5,000円」「5,000円 〜」「82,500円」（1つだけ＝上限。巡回の tsv では 0-82500）
    const g = t.match(/固定報酬制\s*(?:([\d,]+)\s*円\s*)?(〜\s*(?:([\d,]+)\s*円)?)?/)
    if (g && (g[1] || g[3])) return { min: g[2] ? yen(g[1] || 0) : 0, max: g[3] ? yen(g[3]) : g[2] ? Infinity : yen(g[1]), doko: '公開頁' }
    if (/固定報酬制\s*(?:ワーカーと相談|相談)|時間単価制/.test(t)) return null
    return undefined  // 書き方が読めない＝照らせず（黙って通さない）
  }
}
// 本文の納期（募集の本文の「仕事の詳細」から「クライアント情報」まで）：日付（「納期 11月20日」「11月20日まで」）と日数（「納品まで5日以内」「1週間以内に納品」）。
// 一番早い日を返す（{hi: Date, go: 当たった語} ／ 書いていなければ null）。応募・募集の締切は納期に数えない
const DAY = 864e5
const honbunNouki = (t, kyou) => {
  const i = t.indexOf('仕事の詳細'), j = t.indexOf('クライアント情報', i), b = i < 0 ? t : t.slice(i, j > i ? j : i + 6000)
  const c = []
  const hiduke = (y, mo, d) => {
    if (!(mo >= 1 && mo <= 12)) return null
    let yy = y ? +y : kyou.getFullYear(), dd = d === '末' ? new Date(yy, mo, 0).getDate() : +d
    let h = new Date(yy, mo - 1, dd)
    if (!y && h < kyou && (kyou - h) / DAY > 183) h = new Date(yy + 1, mo - 1, dd)  // 年が無く半年より前＝来年
    return h
  }
  for (const m of b.matchAll(/(?<!応募|募集|応募の|募集の)(?:納期|納品日|納品希望日|納品期限|締切|締め切り|〆切|完成|公開日|リリース|提出日|提出期限)[】\]）)\s:：は日]{0,4}(?:初稿提出日|初稿|提出日)?[\s:：]{0,3}(?:(20\d{2})\s*[年\/.\-]\s*)?(\d{1,2})\s*[月\/]\s*(\d{1,2}|末)/g)) { const h = hiduke(m[1], +m[2], m[3]); if (h) c.push({ hi: h, go: m[0] }) }
  for (const m of b.matchAll(/(?:(20\d{2})\s*年\s*)?(\d{1,2})\s*月\s*(\d{1,2}|末)\s*日?\s*(?:[（(][^）)]{1,3}[）)])?\s*(?:まで|迄|までに)(?:[^。]{0,12})(?:納品|完成|仕上げ|公開|納め|ご提出|提出)/g)) { const h = hiduke(m[1], +m[2], m[3]); if (h) c.push({ hi: h, go: m[0] }) }
  const nichi = (n, tani) => tani === '週間' ? n * 7 : tani === 'ヶ月' || tani === 'か月' || tani === 'カ月' ? n * 30 : tani === '営業日' ? Math.ceil(n * 7 / 5) : n
  for (const m of b.matchAll(/(?<!応募|募集)(?:納期|納品|完成|仕上げ|作業期間|期限)[^。]{0,16}?(\d{1,3})\s*(日|営業日|週間|ヶ月|か月|カ月)\s*(?:以内|程度|程|ほど|前後|で|まで)/g)) c.push({ hi: new Date(+kyou + nichi(+m[1], m[2]) * DAY), go: m[0] })
  for (const m of b.matchAll(/(\d{1,3})\s*(日|営業日|週間|ヶ月|か月|カ月)\s*以内[^。]{0,6}(?:納品|完成|仕上げ|ご対応いただける|対応できる)/g)) c.push({ hi: new Date(+kyou + nichi(+m[1], m[2]) * DAY), go: m[0] })
  return c.length ? c.sort((x, y) => x.hi - y.hi)[0] : null
}
const ymd = d => `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
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
    // ④-2 納期の日数（docs/05 共通の決まり：既定は契約の当日〜2日後・本文の締切いっぱいにしない・下書きの日数と .json を合わせる）
    if (d) {
      const nd = new Date(+d[1], +d[2] - 1, +d[3]), riyuu = String(J['納期の理由'] || '').trim()
      if (ba === 'cw') {
        const t = await peji(id)
        if (t === null) red.push('納期を照らせず（公開頁が読めない）')
        else { const h = honbunNouki(t, kyou); if (h && nd > h.hi) red.push(`.json の納期 ${nou} が本文の「${h.go.trim().slice(0, 30)}」（〜${ymd(h.hi)}）より後`) }
      }
      const kitei = new Date(+kyou + 2 * DAY)
      if (nd > kitei && !riyuu) red.push(`.json の納期 ${nou} が既定（契約の当日〜2日後＝〜${ymd(kitei)}）より長い：日付を前に寄せるか、.json に「納期の理由」を1行（例「全20頁のため最初の5頁を翌日・全体は5日後」）`)
      for (const m of txt.matchAll(/(\d{1,3})\s*日以内/g)) { const sa = Math.round((nd - kyou) / DAY); if (Math.abs(sa - +m[1]) > 1) red.push(`下書きの「${m[0]}」と .json の納期 ${nou}（今日から ${sa} 日）が合わない`) }
      for (const m of txt.matchAll(/(\d{1,2})\s*月\s*(\d{1,2})\s*日[^。\n]{0,8}(?:まで|納品)/g)) { if (+m[1] !== +d[2] || +m[2] !== +d[3]) red.push(`下書きの「${m[0].slice(0, 16)}」と .json の納期 ${nou} が合わない`) }
    }
    // ⑤ 予算の帯（帯は税込・.json の金額は税抜）
    if (kin > 0 && ba === 'cw') {
      const b = await obi(id, r)
      if (b === undefined) red.push('帯を照らせず（巡回の tsv に無く、公開頁も読めない）')
      else if (b === null && !String(J['金額の根拠'] || '').trim()) red.push('帯の無い募集（相談）なのに .json に「金額の根拠」が無い：python3 tools/cw-souba.py --id ' + id + ' <何を> <どの道具で> の最後の1行を写す（docs/04 の「5 値段」）')
      else if (b === null && /帯のある募集の額：/.test(String(J['金額の根拠'] || ''))) red.push('帯の無い募集（相談）なのに「金額の根拠」が --obi の1行（帯のある募集の額）：帯は作らず、python3 tools/cw-souba.py --id ' + id + ' <何を> <どの道具で> の最後の1行に打ち直す')  // 試し9の穴：帯の無い募集に作った帯で --obi を打っても通っていた
      else if (b) {
        const zei = Math.round(kin * 1.1); if (zei < b.min || zei > b.max) red.push(`金額が予算の帯の外：税込 ${zei.toLocaleString()}円 ／ 帯 ${b.min.toLocaleString()}〜${b.max.toLocaleString()}円（${b.doko}）`)
        // 試し8回目：帯ありの募集で道具を打たずに 50,000円と書き、根拠が空のまま ✅ で通った → 帯ありも cw-souba.py --obi の1行を要る
        const nk = String(J['金額の根拠'] || '').match(/帯のある募集の額：([\d,]+)円/)
        if (!nk) red.push(`帯のある募集なのに .json の「金額の根拠」に cw-souba.py --obi の1行が無い：python3 tools/cw-souba.py --id ${id} --obi ${b.min}-${b.max} の最後の1行を写す`)
        else if (yen(nk[1]) !== kin) red.push(`.json の金額 ${kin} が「金額の根拠」の帯のある募集の額 ${nk[1]}円 と合わない`)
        else { const lo = Math.floor(b.min * 10 / 11 / 1000) * 1000, hi = Math.floor(b.max * 10 / 11 / 1000) * 1000, motome = Math.min(Math.max(Math.floor(Math.floor(b.max * 6 / 10) * 10 / 11 / 1000) * 1000, lo), hi); if (kin !== motome) red.push(`帯のある募集の額は 上限×0.6 で ${motome.toLocaleString()}円（帯 ${b.min.toLocaleString()}〜${b.max.toLocaleString()}円）。.json の ${kin.toLocaleString()}円 と違う：cw-souba.py --obi を打ち直して写す`) }  // 11/06 試し9の直し：額は帯だけで決まるので、根拠の1行を手で書き換えても照らせる
      }
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
