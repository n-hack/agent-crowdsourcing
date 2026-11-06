// 表の門：添付が .xlsx / .csv なら、送る前に xlsx-mieru.py で見出しの色・固定・絞り込み・列の幅・リンクを付けて上書きする（csv は同じ名前の .xlsx を作り、添付をそちらに差し替える）
// 使い方: const p = require('./mieru-mon.cjs')(添付のパス, go) → 実際に添付するパスを返す。🔴 なら go で止める
// 要る物: python3 と openpyxl（pip install openpyxl）。経歴なしでも再現：する
const { execFileSync } = require('child_process'), path = require('path')
module.exports = (f, go) => {
  if (!f || !/\.(xlsx|csv)$/i.test(f)) return f
  const out = f.replace(/\.csv$/i, '.xlsx')
  try {
    const r = execFileSync(process.env.PYTHON || 'python3', [path.join(__dirname, 'xlsx-mieru.py'), f, out], { encoding: 'utf8' })
    console.log('📊 表の門：' + r.trim().split('\n').join(' ／ '))
    return out
  } catch (e) {
    console.log('🔴 表の門：見やすい形に整えられなかった ' + String(e.stdout || e.message).slice(0, 200))
    if (go === 'go') process.exit(2)
    return f
  }
}
