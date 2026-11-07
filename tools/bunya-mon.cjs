// 分野の門：募集の頁が「取る分野（既定は AI 導入・業務自動化・開発とその小口）」に入るかを3つの値で返す
// 使い方: require('./bunya-mon.cjs')(頁の文字, go, 案件ID) … 応募・提案の道具が募集の頁を読んだ直後に呼ぶ
//   🔴 … 題名の側に取らないジャンルがあり、題名の側に開発・自動化の印も小口の印も無い → go なら rc=2
//   ✅ … 題名の側に取らないジャンルが無く、強い印（題名か本文）か小口の印（題名）がある
//   🟡 … どちらとも言えない（取らないジャンルと開発の印が並ぶ／AI の語だけ／何の印も無い）→ 中身を読んで決める
//        go は BUNYA_HANDAN=「判断の理由（10字以上）」があれば通して logs/bunya-handan.log に残す・無ければ rc=2
//   🔴 を外して出すときは BUNYA_OK=1 と BUNYA_RIYUU=「理由（10字以上）」→ logs/bunya-soto.log（数えて見直す）
// 「AI使用可・ChatGPT使用OK」は道具として使ってよいという意味なので、開発の印に数えない（先に消してから照らす）
// 語は config/bunya.json（無ければ config/bunya.example.json）から読む
// 頁に本文の始まりが無いときは null を返す（照らせない＝🔴 と分ける。go なら rc=2）。読むだけの口（mon-hantei.cjs）は「?」として返す
// 題名の側から頁の分類の道しるべ（CW の「データ作成・入力の仕事・求人」「データ検索・データ収集 の仕事の依頼」）を消してから照らす（docs/04・試し：建築士の募集が道しるべの「データ作成・データ収集」で小口の ✅ になっていた）
const fs = require('fs'), path = require('path')
const B = path.join(__dirname, '..'), cfg = path.join(B, 'config', fs.existsSync(path.join(B, 'config', 'bunya.json')) ? 'bunya.json' : 'bunya.example.json')
const C = JSON.parse(fs.readFileSync(cfg, 'utf8')), R = k => new RegExp('(' + C[k] + ')', 'i')
const TSUYOI = R('強い印'), WADAI = new RegExp('^(' + C['題材になりうる印'] + ')$', 'i'), KOGUCHI = R('小口の印'), AIGO = R('AIの語'), TORANAI = new RegExp('(' + C['取らないジャンル'] + ')')
// ランサーズの道しるべも消す（頁の形：「仕事を探す ◯◯の仕事 ◯◯の仕事 … 題名の仕事・依頼 題名 [ ◯◯ の仕事 / 業種 ]」）。頭の並びと [ ] は「の仕事・依頼」がある頁だけで消す（CW の題名の頭の語を消さないため）
const MICHI = /[^\s。]+ ?の仕事(?:・求人|の依頼|・依頼)/g, MICHI_L = /^(?:\s*[^\s。]+の仕事(?=\s))+/, MICHI_K = /\[ ?[^\[\]]{0,80}? の仕事 ?\/[^\[\]]{0,80}\]/g, isL = s => /の仕事・依頼/.test(s)
const michiKesu = s => (isL(s) ? s.replace(MICHI_L, ' ').replace(MICHI_K, ' ') : s).replace(MICHI, ' ')
const kesu = s => C['先に消す書き方'].reduce((a, r) => a.replace(new RegExp(r, 'gi'), ' '), s)
const kiroku = (f, cols) => { const d = path.join(B, 'logs'); fs.mkdirSync(d, { recursive: true }); fs.appendFileSync(path.join(d, f), [new Date().toISOString(), ...cols].join('\t') + '\n') }
const mon = module.exports = (jobText, go, id) => {
  const t = jobText || '', s = C['本文の始まり'].map(k => t.indexOf(k)).filter(i => i >= 0).sort((a, b) => a - b)[0]
  if (s === undefined) { console.log('🔴 分野の門：本文の始まり（' + C['本文の始まり'].join('／') + '）が頁に見つからず照らせない＝頁の形が変わった'); if (go === 'go' && process.env.BUNYA_OK !== '1') process.exit(2); return null }
  const e = C['本文の終わり'].map(k => t.indexOf(k, s)).filter(i => i > s).sort((a, b) => a - b)[0] ?? s + 3000
  const ts = t.lastIndexOf(C['題名の側の始まり'], s), dai = kesu(michiKesu(t.slice(ts >= 0 && s - ts < 900 ? ts + C['題名の側の始まり'].length : Math.max(0, s - 600), s))), hon = kesu(t.slice(s, e))
  const m = (re, x) => [...new Set(x.match(new RegExp(re.source, re.flags + 'g')) || [])]
  const daiNg = m(TORANAI, dai), daiTs = m(TSUYOI, dai), daiKo = m(KOGUCHI, dai), daiAi = m(AIGO, dai), honTs = m(TSUYOI, hon), honNg = m(TORANAI, hon), honKo = m(KOGUCHI, hon)
  const daiTsJitsu = daiTs.filter(w => !WADAI.test(w))  // 「AI業務効率化の記事」のように題材として出る語は除く
  const kotae = (daiNg.length && !daiTsJitsu.length && !daiKo.length) ? '🔴' : (!daiNg.length && (daiTs.length || honTs.length || daiKo.length)) ? '✅' : '🟡'
  const j = a => a.join('・') || 'なし'
  const naka = '題名の側［取らない:' + j(daiNg) + '／強い:' + j(daiTs) + '／小口:' + j(daiKo) + '／AI:' + j(daiAi) + '］本文［強い:' + j(honTs) + '／小口:' + j(honKo) + '／取らない:' + j(honNg) + '］'
  if (kotae === '✅') { console.log('✅ 分野の門：取る分野に入る（' + naka + '）'); return true }
  if (kotae === '🟡') {
    console.log('🟡 分野の門：文脈で決める（' + naka + '）。依頼の中身が取る分野（とその小口）かを読んで決める')
    if (go !== 'go') return 'bunsyaku'
    const r = process.env.BUNYA_HANDAN || ''
    if (r.length >= 10) { kiroku('bunya-handan.log', [id || '', '🟡', naka, r]); console.log('🟡 判断の理由を logs/bunya-handan.log に残して通します：' + r); return true }
    console.log('🔴 止めました：🟡 は判断の理由が要る。BUNYA_HANDAN=「なぜ取る分野に入る／入らないと読んだか（10字以上）」を付けて出し直す'); process.exit(2)
  }
  console.log('🔴 分野の門：取らないジャンルで、開発・自動化の中身が無い（' + naka + '）')
  if (go !== 'go') return false
  if (process.env.BUNYA_OK === '1' && (process.env.BUNYA_RIYUU || '').length >= 10) { kiroku('bunya-soto.log', [id || '', process.env.BUNYA_RIYUU]); console.log('🟡 外して出します（理由を logs/bunya-soto.log に記録）：' + process.env.BUNYA_RIYUU); return false }
  console.log('🔴 止めました：出すなら BUNYA_OK=1 と BUNYA_RIYUU=「分野の外でも出す理由（10字以上）」を付ける'); process.exit(2)
}
if (require.main === module) {
  // 試し：🔴（AI使用可のライター・SNS）／✅（開発・小口）／🟡（印なし・AI の語だけ・取らないジャンルと開発が並ぶ）
  const pg = (dai, hon) => '仕事を探す ' + dai + ' 仕事の詳細 ' + hon + ' クライアント情報'
  const cases = [
    ['🔴', pg('SEO記事のライター募集', '生成AI使用可です。1記事3,000字・月10本の執筆をお願いします。')],
    ['🔴', pg('Instagram の SNS運用代行', 'ChatGPT使用OK。投稿の文と画像を週3回作ってください。')],
    ['🔴', pg('YouTube 動画の切り抜き編集', 'AI活用歓迎。ショート動画を月20本。')],
    ['✅', pg('GAS でスプレッドシートの集計を自動化', '毎朝 CSV を取り込み、月次の表を作るスクリプトを開発してください。')],
    ['✅', pg('Python で在庫データの取り込みツール作成', 'API から在庫を取り、Excel に書き出します。')],
    ['✅', pg('商品リスト作成（Excel）', 'Web で調べて表にまとめる作業です。')],
    ['🟡', pg('簡単なお手伝い', '詳細は面談でお伝えします。')],
    ['🟡', pg('AI に詳しい方', '社内で AI を使いたいので相談に乗ってください。')],
    ['🟡', pg('記事の自動生成ツールの開発', 'WordPress に記事を自動で投稿する仕組みを作ってください。')],
    // 道しるべ：分類の「データ作成・データ収集」は題名ではない（＜案件番号＞ の頁の形）
    ['🟡', '仕事を探す 事務・カンタン作業の仕事・求人 データ作成・入力の仕事・求人 データ検索・データ収集の仕事・求人 福岡在住の二級建築士有資格者募集 福岡在住の二級建築士有資格者募集 データ検索・データ収集 の仕事の依頼 仕事の概要 時間単価制 仕事の詳細 資格を持っていて今は使っていない方からのご連絡をお待ちしています クライアント情報'],
    ['✅', '仕事を探す 事務・カンタン作業の仕事・求人 リスト作成の仕事・求人 店舗の一覧をエクセルにまとめる リスト作成 の仕事の依頼 仕事の詳細 Web で調べて表にまとめる作業です。 クライアント情報'],
    // ランサーズの道しるべ：頭の「ライティング・記事作成の仕事」は題名ではない（開発の募集が ✅ のまま）
    ['✅', '仕事を探す ライティング・記事作成の仕事 Web制作・Webデザインの仕事 GAS でスプレッドシートの集計を自動化の仕事・依頼 GAS でスプレッドシートの集計を自動化 [ システム開発 の仕事 / IT・通信 ] 仕事の詳細 毎朝 CSV を取り込み、月次の表を作るスクリプトを開発してください。 クライアント情報'],
    ['🔴', '仕事を探す システム開発の仕事 SEO記事のライター募集の仕事・依頼 SEO記事のライター募集 [ ライティング の仕事 / メディア ] 仕事の詳細 生成AI使用可です。1記事3,000字・月10本の執筆をお願いします。 クライアント情報'],
    // 本文の始まりが無い頁＝照らせない（🔴 と分ける）
    ['?', '仕事を探す GAS でスプレッドシートの集計を自動化 依頼の内容 毎朝 CSV を取り込むスクリプトを開発 クライアント情報'],
  ]
  const log = console.log; console.log = () => {}
  const got = cases.map(([want, p]) => { const r = mon(p); return [want, r === true ? '✅' : r === false ? '🔴' : r === null ? '?' : '🟡'] })
  console.log = log
  const bad = got.filter(([w, g]) => w !== g)
  for (const [i, [w, g]] of got.entries()) if (w !== g) console.log('🔴 ずれ ' + (i + 1) + '本目：はず ' + w + ' ／ 出た ' + g)
  const n = k => cases.filter(c => c[0] === k).length
  console.log(bad.length ? `🔴 ${bad.length}件ずれ` : `✅ 🔴${n('🔴')}／✅${n('✅')}／🟡${n('🟡')}／照らせず${n('?')} 全部合った`); process.exit(bad.length ? 1 : 0)
}
