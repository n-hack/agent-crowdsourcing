// 契約の門：契約を受ける・進める文を送る前に、できると確信した記録があるかを見る（オーナーの決まり：できると確信した物だけ契約・分からなければ契約の前に相手へ聞く・docs/06）
// 見る物 … <置き場>/keiyaku/<部屋の番号>.md（①作業で使う画面・道具を自分で見た ②手順を最後まで読み自分で回せる ③分からない点と相手の答え）
// 🔴 … 契約の語があり、記録が無い／①②③の行が欠ける／「分からない・未確認・まだ聞いていない」が残っている
// 使い方: require('./keiyaku-mon.cjs')(本文, 部屋の番号, go) → 🔴 があり go なら止める（外す道は作らない）
const fs = require('fs'), path = require('path')
const KEIYAKU = /契約(させて|に進(め|ま)|を(お受け|承|進め)|いたします)|ご契約(いただき|を(お受け|承))|お引き受け(いた|させて)|お受けいたします|仮払い(を)?(お願い|いただ)/
module.exports = (body, id, go) => {
  if (!KEIYAKU.test(body)) return []
  const f = path.join(require('./settei.cjs').DATA, 'keiyaku', String(id).replace(/\//g, '_') + '.md')
  const red = []
  if (!fs.existsSync(f)) red.push(`契約の語があるのに記録 ${f} が無い（作業の画面を見た・手順を回せる・分からない点と相手の答え の3行を書いてから）`)
  else {
    const t = fs.readFileSync(f, 'utf8')
    for (const [k, w] of [['①', '画面'], ['②', '手順'], ['③', '分からない点']]) if (!t.includes(k)) red.push(`記録に ${k}（${w}）の行が無い`)
    const nokori = t.split('\n').filter(l => /分からない(まま|$)|わからない(まま|$)|未確認|まだ聞いていない|見えない|見ていない/.test(l) && !/答え[:：].+/.test(l))
    if (nokori.length) red.push('記録に分からない所が残っている → 契約せず、先に相手に聞く：' + nokori[0].slice(0, 80))
  }
  for (const r of red) console.log('🔴 契約の門: ' + r)
  if (red.length && go === 'go') process.exit(2)
  return red
}
