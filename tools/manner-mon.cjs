// マナーの門：返事・応募の文を送る前に見る（決まりは docs/06-henji.md・出どころつき）
// 使い方: require('./manner-mon.cjs')(本文, 'henji'|'oubo', go)  … henji は宛名〜署名の形まで／oubo は言葉づかいだけ
// 止める: 🔴 があり go の時は rc=2（MANNER_OK=1 で通す）。🟡 は出すだけ
// AIっぽさ（絵文字・Markdown・穴埋め・英語の決まり文句・AI の自称・褒めすぎ・！の重ね・飾りの記号 ほか）も見る。出どころは docs/06-henji.md
// 第4引数 {aite: 相手の文} で相手の長さとの比べも見る。logs/okutta/*.txt（送った文の控え）があれば使い回しの行も見る
// 名乗りと署名は config/profile.json（無ければ config/profile.example.json）から読む
const fs = require('fs'), path = require('path')
const cfgDir = path.join(__dirname, '..', 'config')
const cfgFile = fs.existsSync(path.join(cfgDir, 'profile.json')) ? 'profile.json' : 'profile.example.json'
const P = JSON.parse(fs.readFileSync(path.join(cfgDir, cfgFile), 'utf8'))
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const m = module.exports = (body, mode, go, opt = {}) => {
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
  // ── AIっぽさ。「」『』（）の中（相手の文の引用）・宛名の1行目・相手の質問を写した行「(8)…！」・社名 Yahoo! は記号の検査から外す
  const AIR = [], AIY = [], cnt = (s, r) => (s.match(r) || []).length
  const u = L.slice(/(様|御中|さん)$/.test(L[0] || '') ? 1 : 0).filter(s => !/^[（(][0-9０-９]{1,2}[)）].*[！!？?]$/.test(s)).join('\n').replace(/Yahoo[!！]/g, 'Yahoo').replace(/「[^「」\n]{0,300}」|『[^『』\n]{0,300}』|（[^（）\n]{0,200}）|\([^()\n]{0,200}\)/g, '')
  if (/\p{Extended_Pictographic}/u.test(u)) AIR.push('絵文字がある')
  if (/^#{1,6}\s|\*\*[^*\n]+\*\*|^\s*[-*]\s|```|\[[^\]\n]+\]\(https?:/m.test(t)) AIR.push('Markdown の書き方（# 見出し・**太字**・- 箇条書き・[文字](URL)）が残っている')
  if (/\{[^{}\n]{1,20}\}|［[^］\n]{1,15}］|〇〇|◯◯|○○|ＸＸ|\bXX\b/.test(u)) AIR.push('型の穴埋めが残っている（{…}・〇〇・XX）')
  if (/\b(Let me|Certainly|Here's|Here is|I hope|Best regards|Absolutely|As an AI)\b|\bSure[,!]/i.test(t)) AIR.push('英語の決まり文句（AI の出力の残り）')
  const self = t.match(/(この|本|今回の)(メッセージ|文章|文面|ご提案文?|お返事|返信|応募文)は.{0,20}(AI|自動|生成|ChatGPT|Claude)|AI(アシスタント|エージェント)(として|です|である|の私)|私は\s?AI|言語モデル|自動(返信|応答|送信)(です|しています|されて|いたします)/)
  if (self) AIR.push('自分の文を AI・自動で書いた／自分が AI だと書いている「' + self[0] + '」')
  const praise = t.match(/素晴らしい(ご|プロジェクト|取り組み|案件|ビジョン|ご活動|事業|サービス)|大変興味深く|非常に興味深く|感銘を受け|心を打たれ|ワクワク|胸が躍|いかがでしたか|と言えるでしょう|まとめると、|総じて、/)
  if (praise) AIR.push('褒めすぎ・AI の定型句「' + praise[0] + '」')
  const bang = cnt(u, /[！!]/g); if (bang >= 2) AIR.push('「！」が' + bang + '回（仕事の文では使わない）'); else if (bang === 1) AIY.push('「！」が1回（できれば外す）')
  const arrow = cnt(u, /[→⇒➡]/g); if (mode === 'henji' && arrow) AIR.push('返事に「→」（文で書く）'); else if (arrow >= 3) AIY.push('「→」が' + arrow + '回')
  const sym = cnt(u, /[★☆✓✔✅]/g); if (sym) AIR.push('飾りの記号（★✓ など）が' + sym + '個')
  const head = cnt(u, /^\s*([■□◆◇●▼▶►]|【[^】\n]{1,20}】\s*$)/gm); if ((mode === 'henji' && head) || head >= 6) AIY.push('見出し（■◆▼・【】）が' + head + '個')
  if (/—|――|──/.test(u)) AIY.push('ダッシュ（——）がある（読点で書く）')
  const hot = cnt(t, /ぜひ|是非|心より|心から|誠に|非常に|大変|共感|魅力|光栄|何卒|情熱|全力で/g); if (hot >= 5) AIY.push('熱意・丁寧の語の重ね ' + hot + '個')
  const kata = t.match(/シームレス|ソリューション|ブラッシュアップ|ベストプラクティス|インサイト|レバレッジ|シナジー|エンゲージメント|アジャイル|ポテンシャル|パーソナライズ|コミット/g); if (kata) AIY.push('かたかなの業界語「' + [...new Set(kata)].join('・') + '」（日本語で言える物は日本語に）')
  if (/(することが|が)(重要|大切)です|重要なポイント|ポイントは以下/.test(t)) AIY.push('「〜が重要です」型の言い回し')
  const vague = t.match(/早めに|なるべく早く|できるだけ早く|幾つか|様々な|さまざまな|適切な|柔軟に|迅速に|スピーディー/g); if (vague && vague.length >= 2) AIY.push('ぼかした語「' + [...new Set(vague)].join('・') + '」（日付・数字で書く）')
  const mawari = t.match(/することができ|を実施(いた)?し|まず最初に|させていただくことが/); if (mawari) AIY.push('回りくどい形「' + mawari[0] + '」（「できる」「〜した」で足りる）')
  const ss = u.split(/[。！？\n]/).filter(s => s.trim().length >= 10)
  if (ss.length >= 5) { const rc = ss.reduce((a, s) => a + cnt(s, /、/g), 0) / ss.length; if (rc > 1.5) AIY.push('読点が1文に平均' + rc.toFixed(1) + '個（AI の文は読点が多い）') }
  const longS = u.split(/[。\n]/).filter(s => s.trim().length > 120).length; if (longS) AIY.push('120字を超える1文が' + longS + 'つ')
  if (mode === 'henji' && t.length > 800) AIY.push('返事が' + t.length + '字（返事は短く）')
  if (mode === 'oubo' && t.length > 1600) AIY.push('応募文が' + t.length + '字（長い）')
  if (opt.aite && t.length > Math.max(300, String(opt.aite).length * 3)) AIY.push('相手の文（' + String(opt.aite).length + '字）の3倍を超える長さ（' + t.length + '字）')
  try { // 送った文の控え（logs/okutta/*.txt）と同じ40字以上の行が3通以上 … 使い回しの跡
    const D = path.join(__dirname, '..', 'logs', 'okutta'), mine = new Set(L.filter(s => s.length >= 40)), hit = new Map()
    if (mine.size && fs.existsSync(D)) for (const f of fs.readdirSync(D).filter(f => /\.txt$/.test(f))) { const o = fs.readFileSync(path.join(D, f), 'utf8'); if (o.replace(/\r/g, '').trim() === t) continue
      for (const k of o.split('\n').map(s => s.trim())) if (mine.has(k)) hit.set(k, (hit.get(k) || new Set()).add(f)) }
    const many = [...hit].filter(([, v]) => v.size >= 3); if (many.length) AIY.push('送った文と同じ行が' + many.length + '行（3通以上で使い回し・例「' + many[0][0].slice(0, 24) + '…」）')
  } catch (e) { AIY.push('使い回しの検査が動かなかった（' + e.message + '）') }
  for (const r of AIR) red.push('AIっぽさ: ' + r)
  for (const y of AIY) yel.push('AIっぽさ: ' + y)
  for (const r of red) console.log('🔴 マナー: ' + r)
  for (const y of yel) console.log('🟡 マナー: ' + y)
  if (red.length && go === 'go' && process.env.MANNER_OK !== '1') { console.log('🔴 マナーの門で止めました（docs/06-henji.md）'); process.exit(2) }
  return { red, yel }
}
if (require.main === module) {
  // 試し：profile が見本のまま（◯◯）なら試しの名乗りに差し替える（◯◯は穴埋めとして 🔴 になるため）
  if (/[◯〇○]/.test(P['名乗り'] + P['署名'])) Object.assign(P, { '名乗り': '株式会社サンプルの佐藤', '署名': '株式会社サンプル 佐藤' })
  // 通るべき（ふつうの返事・応募文）・止まるべき（マナー3＋AIっぽさ）
  const ok = `山田様\n\nご連絡ありがとうございます。${P['名乗り']}です。\n承知しました。本日中にお送りします。\nよろしくお願いいたします。\n\n${P['署名']}`
  const oks = [ok, `山田様\n\nお世話になっております。${P['名乗り']}です。\n11月8日の17時までに見積もりをお送りします。\nよろしくお願いいたします。\n\n${P['署名']}`]
  const okOubo = ['はじめまして。スプレッドシートの集計を GAS で自動にする仕事を受けています。\n今回の転記は、1日目に手順を確かめ、3日目までに納品できます。', '募集を拝見しました。CSV の取り込みと月次の表づくりを Python で作れます。\n見積もりは2万円、納期は5日です。']
  const aiH = (x) => `山田様\n\nご連絡ありがとうございます。${P['名乗り']}です。\n${x}\nよろしくお願いいたします。\n\n${P['署名']}`
  const ngAi = [aiH('素晴らしいプロジェクトですね！ぜひご一緒させてください！'), aiH('**ご提案の内容**\n- 自動化の設計\n- 納品'), aiH('Certainly! 承知しました。'), aiH('この返信はAIアシスタントとして作成しました。'), aiH('{相手の名前}様の件、承知しました。'), aiH('本日中にお送りします🙏'), aiH('進め方 → 本日中にお送りします。')]
  const ng = [`ご連絡ありがとうございます。了解しました。\n${P['署名']}`, `◯◯様\n${P['名乗り']}です。資料を拝見させていただきました。\nよろしくお願いいたします。\n${P['署名']}`, `◯◯様\n${P['名乗り']}です。了解だよ！！\nよろしくお願いいたします。\n${P['署名']}`]
  const log = console.log; console.log = () => {}
  let bad = 0
  for (const s of oks) if (m(s, 'henji').red.length) bad++
  for (const s of okOubo) if (m(s, 'oubo').red.length) bad++
  for (const s of ng) if (!m(s, 'henji').red.length) bad++
  for (const s of ngAi) if (!m(s, 'henji').red.some(r => /^AIっぽさ/.test(r))) bad++
  console.log = log
  console.log(bad ? `🔴 ${bad}件ずれ` : `✅ 通るべき ${oks.length + okOubo.length}／止まるべき ${ng.length}＋AIっぽさ ${ngAi.length} 全部合った`); process.exit(bad ? 1 : 0)
}
