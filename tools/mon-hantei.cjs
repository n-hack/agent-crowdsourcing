// 【門】分野・できるか・勧誘の門を、止めずに読むだけで当てる口（cw-tantei.py が呼ぶ）
// 入力: 標準入力に JSON の配列 [{"id":"…","text":"頁の本文"}]
// 出力: 1件1行「ID<TAB>分野(✅|🟡|🔴|?)<TAB>できない条件（空なら通る）<TAB>勧誘の印（空なら通る）」
// 「?」＝頁に本文の始まりが無く分野を照らせない（頁の形が変わった見込み・🔴 と分ける：cw-tantei が rc=3 で止める）
// 止まる条件: 入力が JSON でないとき rc=1。go は渡さない＝門は止めず、記録も書かない
// 呼び方: echo '[{"id":"1","text":"…"}]' | node tools/mon-hantei.cjs
const bunya = require('./bunya-mon.cjs'), dekiru = require('./dekiru-mon.cjs'), kanyu = require('./kanyu-mon.cjs')
const items = JSON.parse(require('fs').readFileSync(0, 'utf8'))
const orig = console.log, out = []
for (const { id, text } of items) {
  console.log = () => {}
  let r
  try { r = bunya(text, undefined, id) } finally { console.log = orig }
  const k = kanyu(text)
  out.push([id, r === true ? '✅' : r === false ? '🔴' : r === null ? '?' : '🟡', dekiru(text).join('／'), k.kanyu ? k.hits.join('／') : ''].join('\t'))
}
console.log(out.join('\n'))
