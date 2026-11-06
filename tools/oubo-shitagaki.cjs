// 【応募文】門を通った候補の下書きを型（templates/oubo-kihon.txt）から作る。宛名・名乗り・署名だけ埋め、中身の穴（{…}）は残す＝埋めるまで送れない
// 入力: 場（cw|lancers）・案件ID・依頼主の表示名（分からなければ -）／config/profile.json の名乗り・署名
// 出力: <置き場>/oubo-bun/<場>-<ID>.txt（本文）と <場>-<ID>.json（{"金額":null,"納期":null,"日数":null,"題名":"",…}）。既にあれば上書きしない。最後にマナーの門の結果
// 止まる条件: 名乗り・署名が見本のまま（◯◯）か空 → rc=2（設定を先に直す）
// 呼び方: node tools/oubo-shitagaki.cjs cw <案件ID> <依頼主> [題名]
require('./nhack-mon.cjs')()
const fs = require('fs'), path = require('path'), S = require('./settei.cjs')
const [ba, id, aite, dai] = process.argv.slice(2)
if (!/^(cw|lancers)$/.test(ba || '') || !/^\d+$/.test(id || '')) { console.log('使い方: node tools/oubo-shitagaki.cjs cw|lancers <案件ID> <依頼主|-> [題名]'); process.exit(2) }
let nanori, shomei
try { nanori = S.kensa(S.P['名乗り'], '名乗り'); shomei = S.kensa(S.P['署名'], '署名') } catch (e) { console.log(e.message); process.exit(2) }
const D = path.join(S.DATA, 'oubo-bun'); fs.mkdirSync(D, { recursive: true })
const F = path.join(D, `${ba}-${id}.txt`), J = path.join(D, `${ba}-${id}.json`)
if (!fs.existsSync(F)) {
  const kata = fs.readFileSync(path.join(__dirname, '..', 'templates', 'oubo-kihon.txt'), 'utf8')
  fs.writeFileSync(F, kata.replace('{依頼主}', aite && aite !== '-' ? aite : 'ご担当者').replace('{名乗り}', nanori).replace('{署名}', shomei))
  console.log('下書きを作った', F)
} else console.log('下書きは既にある（上書きしない）', F)
if (!fs.existsSync(J)) fs.writeFileSync(J, JSON.stringify({ 場: ba, 案件ID: id, 題名: dai || '', 金額: null, 納期: null, 計画の題名: '', 計画: '', メモ: '金額は税抜・納期は YYYY-M-D。ランサーズは 計画の題名（20字以内）と 計画 も埋める' }, null, 1) + '\n')
const body = fs.readFileSync(F, 'utf8'), ana = body.match(/\{[^{}\n]{1,20}\}/g) || []
console.log(ana.length ? `🟡 埋める穴 ${ana.length}つ：${ana.join(' ')}（埋めるまで --go でも送らない）` : '✅ 穴は埋まっている')
require('./manner-mon.cjs')(body, 'oubo')
