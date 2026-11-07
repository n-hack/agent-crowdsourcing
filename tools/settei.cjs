// 設定の口：個人・会社の値は全部ここから読む（道具の中に名前・メール・パスを書かない）
// 入力: config/profile.json（無ければ profile.example.json）＋環境変数 CS_PROFILE・CS_DATA・CS_CDP_URL・CS_CDP_PORT・PLAYWRIGHT_PATH
// 出力: { P, DATA(置き場), kiroku(応募の記録), cdp(つなぐ先), kensa(値,名前), jibun(文字), playwright(), tab(b,名前), tsuika(道,行) }
// 止まる条件: kensa に文字列でない・空・[object・undefined を渡したとき（入れずに止める）／playwright が無いとき rc=5
// 呼び方: const S = require('./settei.cjs') ／ node tools/settei.cjs で今の値を出す
const fs = require('fs'), path = require('path'), os = require('os')
const R = path.join(__dirname, '..'), C = path.join(R, 'config')
const file = process.env.CS_PROFILE || path.join(C, fs.existsSync(path.join(C, 'profile.json')) ? 'profile.json' : 'profile.example.json')
const P = JSON.parse(fs.readFileSync(file, 'utf8'))
const home = s => String(s || '').replace(/^~(?=\/|$)/, os.homedir())
const DATA = home(process.env.CS_DATA || P['置き場'] || '~/cs-data')
const br = P['ブラウザ'] || {}
const cdp = process.env.CS_CDP_URL || br['CDPのURL'] || `http://127.0.0.1:${process.env.CS_CDP_PORT || br['CDPのポート'] || 9222}`
const kensa = (v, mei) => { if (typeof v !== 'string' || !v.trim() || /\[object|undefined|null|NaN|[◯〇○]/.test(v)) throw new Error(`🔴 ${mei} の値が崩れているか見本のまま（${String(v).slice(0, 30)}）・入れずに止める（${file}）`); return v }
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const shirushi = (P['自分の名前の印'] || []).filter(x => x && !/[◯〇○]/.test(x))
// 自分の便か：自分の名前の印で始まる（相手が「◯◯様」と宛名に書いた便は自分の便にしない）
const jibun = s => shirushi.some(x => new RegExp('^\\s*' + esc(x)).test(s || '') && !new RegExp(esc(x) + '\\s*様').test(s || ''))
const playwright = () => {
  for (const c of [process.env.PLAYWRIGHT_PATH, 'playwright']) { if (!c) continue; try { return require(c) } catch (e) {} }
  try { return require(path.join(require('child_process').execSync('npm root -g', { encoding: 'utf8' }).trim(), 'playwright')) } catch (e) {}
  console.log('🔴 playwright が見つからない（npm i -g playwright か PLAYWRIGHT_PATH=<置き場>）'); process.exit(5)
}
// 同じブラウザに何本もつなぐと、別の道具が先に確認の窓を閉じて「No dialog is showing」で落ちる → この1種類だけ流す
if (!global.__csDialogGuard) {
  global.__csDialogGuard = 1
  const nagasu = e => /No dialog is showing|Page\.handleJavaScriptDialog/.test(String(e && (e.message || e.method || e)))
  process.on('unhandledRejection', e => { if (nagasu(e)) return; console.log('ERR', String(e && e.message || e).slice(0, 300)); process.exit(1) })
}
// 道具ごとに自分のタブを1つ決めて使い回す（開いて閉じるを繰り返さない）。名前→タブの番号は <置き場>/run/tabs/<名前>.id
const tab = async (b, name) => {
  const D = path.join(DATA, 'run', 'tabs'); fs.mkdirSync(D, { recursive: true })
  const F = path.join(D, name + '.id'), ctx = b.contexts()[0]
  const want = fs.existsSync(F) ? fs.readFileSync(F, 'utf8').trim() : ''
  const tid = async pg => { const s = await ctx.newCDPSession(pg); const { targetInfo } = await s.send('Target.getTargetInfo'); await s.detach().catch(() => {}); return targetInfo.targetId }
  if (want) for (const pg of ctx.pages()) { try { if (await tid(pg) === want) return pg } catch (e) {} }
  const p = await ctx.newPage(); fs.writeFileSync(F, await tid(p)); return p
}
const tsuika = (f, line) => { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.appendFileSync(f, line) }
// 記録の3列目（案件ID・「・」で複数）にあり、7列目が 応募・提案 で始まる行の ID
const ouboZumi = (ba) => { const f = path.join(DATA, 'oubo-kiroku.tsv'); if (!fs.existsSync(f)) return new Set()
  return new Set(fs.readFileSync(f, 'utf8').split('\n').map(l => l.split('\t')).filter(c => c.length >= 7 && (!ba || c[1] === ba) && /^(応募|提案)/.test(c[6])).flatMap(c => c[2].split('・').map(x => x.trim()))) }
module.exports = { P, file, DATA, cdp, kensa, jibun, playwright, tab, tsuika, ouboZumi, kiroku: path.join(DATA, 'oubo-kiroku.tsv') }
if (require.main === module) console.log(JSON.stringify({ 設定: file, 置き場: DATA, つなぐ先: cdp, 自分の名前の印: shirushi }, null, 1))
