// マナーの門：返事・応募の文を送る前に見る（決まりは docs/06-henji.md・出どころつき）
// 使い方: require('./manner-mon.cjs')(本文, 'henji'|'oubo', go)  … henji は宛名〜署名の形まで／oubo は言葉づかいだけ
// 止める: 🔴 があり go の時は rc=2（MANNER_OK=1 で通す）。🟡 は出すだけ
// 名乗りと署名は config/profile.json（無ければ config/profile.example.json）から読む
require('./nhack-mon.cjs')()  // N-Hack のエージェント専用（docs/00-hajimeni-yomu.md）
const fs = require('fs'), path = require('path')
const cfgDir = path.join(__dirname, '..', 'config')
const cfgFile = fs.existsSync(path.join(cfgDir, 'profile.json')) ? 'profile.json' : 'profile.example.json'
const P = JSON.parse(fs.readFileSync(path.join(cfgDir, cfgFile), 'utf8'))
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const m = module.exports = (body, mode, go) => {
  const t = String(body || '').replace(/\r/g, '').trim(), L = t.split('\n').map(s => s.trim()).filter(Boolean)
  const red = [], yel = []
  const NG2 = /(おっしゃられ|ご覧になられ|お越しになられ|お見えになられ|お帰りになられ|拝見させていただ|お伺いさせていただ|伺わせていただ|申される|ご拝読)/g
  for (const x of t.match(NG2) || []) red.push('二重敬語「' + x + '」（敬語の指針：一般に適切ではない）')
  if (/了解(しました|です|いたしました)/.test(t)) red.push('「了解しました」→「承知しました」')
  if (/(だよ|だね|だよね)[。！!]?$|（笑）|\(笑\)|[^a-zA-Z]w{2,}|！！|!!/m.test(t)) red.push('くだけた語尾・記号')
  const sase = (t.match(/させていただ/g) || []).length; if (sase >= 3) yel.push('「させていただく」が' + sase + '回（許可と恩恵がある所だけに）')
  if (mode === 'henji') {
    if (!/(様|御中)$/.test(L[0] || '')) red.push('1行目に宛名（◯◯様）が無い')
    if (/御中\s*様|様\s*御中/.test(t)) red.push('御中と様を重ねている')
    if (!new RegExp(esc(P['名乗り'])).test(t)) red.push('名乗り（' + P['名乗り'] + '）が無い')
    if (!/(よろしくお願い(いた)?します|お願い申し上げます)/.test(t)) red.push('結びの挨拶が無い')
    if (!new RegExp(esc(P['署名']).replace(/ /g, '\\s*') + '$').test(L[L.length - 1] || '')) red.push('最後の行に署名（' + P['署名'] + '）が無い')
    if (!/(ありがとうございま|お世話になっております|恐れ入ります|お詫び)/.test(t)) yel.push('お礼・挨拶の1文が無い')
  }
  for (const r of red) console.log('🔴 マナー: ' + r)
  for (const y of yel) console.log('🟡 マナー: ' + y)
  if (red.length && go === 'go' && process.env.MANNER_OK !== '1') { console.log('🔴 マナーの門で止めました（docs/06-henji.md）'); process.exit(2) }
  return { red, yel }
}
if (require.main === module) {
  // 試し：通るべき1・止まるべき3（宛名なし＋了解／二重敬語／くだけた語尾）
  const ok = `◯◯様\n\nご連絡ありがとうございます。${P['名乗り']}です。\n承知しました。本日中にお送りします。\nよろしくお願いいたします。\n\n${P['署名']}`
  const ng = [`ご連絡ありがとうございます。了解しました。\n${P['署名']}`, `◯◯様\n${P['名乗り']}です。資料を拝見させていただきました。\nよろしくお願いいたします。\n${P['署名']}`, `◯◯様\n${P['名乗り']}です。了解だよ！！\nよろしくお願いいたします。\n${P['署名']}`]
  const log = console.log; console.log = () => {}
  let bad = 0
  if (m(ok, 'henji').red.length) bad++
  for (const s of ng) if (!m(s, 'henji').red.length) bad++
  console.log = log
  console.log(bad ? `🔴 ${bad}件ずれ` : `✅ 通るべき 1／止まるべき ${ng.length} 全部合った`); process.exit(bad ? 1 : 0)
}
