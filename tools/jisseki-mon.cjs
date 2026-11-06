// 成果の言い方の門：裏づけの無い成果の一文を止める。出どころを確かめたら JISSEKI_OK=1 で通す
// 使い方 … require("./jisseki-mon.cjs")([本文ファイル…], go)
const fs = require('fs')
module.exports = (files, go) => {
  const kw = /(上が|増え|伸び|改善し|減り|下が|向上し|達成し|獲得し)(りました|ました)/
  const hits = files.filter(Boolean).flatMap(f => fs.readFileSync(f, 'utf8').split('\n')).filter(l => kw.test(l))
  if (!hits.length) return
  console.log('🟡 成果の言い方 ' + hits.length + '行（出どころを確かめる）\n' + hits.join('\n'))
  if (go === 'go' && process.env.JISSEKI_OK !== '1') { console.log('🔴 止めました：確かめたら JISSEKI_OK=1 を付けて打つ'); process.exit(2) }
}
if (require.main === module) {
  // 試し：止まるべき1（成果の言い方）・通るべき1
  const os = require('os'), p = require('path'), { execFileSync } = require('child_process')
  const d = fs.mkdtempSync(p.join(os.tmpdir(), 'jm-'))
  fs.writeFileSync(d + '/ng.txt', '前の会社で売上が上がりました'); fs.writeFileSync(d + '/ok.txt', '進め方は次のとおりです')
  const run = f => { try { execFileSync('node', ['-e', `require(${JSON.stringify(__filename)})([${JSON.stringify(f)}],'go')`], { stdio: 'pipe' }); return 0 } catch (e) { return e.status } }
  let bad = 0; if (run(d + '/ng.txt') !== 2) bad++; if (run(d + '/ok.txt') !== 0) bad++
  console.log(bad ? `🔴 ${bad}件ずれ` : '✅ 通るべき 1／止まるべき 1 全部合った'); process.exit(bad ? 1 : 0)
}
