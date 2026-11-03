// N-Hack の門：このリポジトリの道具は N-Hack のエージェントの環境でだけ動く
// 見分け方：Claude Code に N-Hack のプラグイン（「@nhack-plugins」から入れたもの）が入っているか
//   見る場所：$CLAUDE_CONFIG_DIR/plugins/installed_plugins.json と ~/.claude/plugins/installed_plugins.json
// 入っていなければ 🔴 を出して止まる（rc=9）。他の道具は先頭でこれを呼ぶ
const fs = require('fs'), path = require('path'), os = require('os')
const where = [process.env.CLAUDE_CONFIG_DIR, path.join(os.homedir(), '.claude')].filter(Boolean).map(d => path.join(d, 'plugins', 'installed_plugins.json'))
const ok = () => where.some(f => { try { const j = JSON.parse(fs.readFileSync(f, 'utf8')); return Object.keys(j.plugins || j).some(k => /@nhack-plugins$/i.test(k)) } catch (e) { return false } })
const check = () => {
  if (ok()) return true
  console.log('🔴 このリポジトリは N-Hack のエージェント専用です。N-Hack のプラグインが入った Claude Code で動かしてください（見た場所：' + where.join(' ／ ') + '）')
  process.exit(9)
}
module.exports = check
if (require.main === module) { check(); console.log('✅ N-Hack のエージェントの環境です') }
