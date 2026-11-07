#!/usr/bin/env node
// 【確かめ】初期構築（docs/15）の段が済んだかを、ログイン済みのブラウザで場の頁を開いて見る（読むだけ・押さない・書かない）
// 入力: 場の名前（cw ／ lancers ／ sokudan ／ workship ／ skillshift ／ aicw ／ fiverr ／ upwork ／ all）・ブラウザのつなぐ先（settei.cjs と同じ）
// 出力: 場ごとに1行「✅ ログイン済み」か「🔴 ログインの頁に戻された」と、頁の文から拾った本人確認・口座の語（CW・ランサーズは自分の公開プロフィールも開いて拾う。見つからなければ「─ 頁の文に無い」＝未提出とは限らない）
// 止まる条件: ブラウザにつなげない rc=3（「未ログイン」と同じにしない）／1つでも 🔴 なら rc=1／全部 ✅ なら rc=0
// 呼び方: node tools/shoki-kakunin.cjs cw   （全部は all）
const S = require('./settei.cjs')
const BA = {
  cw:       { mei: 'クラウドワークス', url: 'https://crowdworks.jp/dashboard', login: /crowdworks\.jp\/login/, prof: 'https://crowdworks.jp/profile' },
  lancers:  { mei: 'ランサーズ', url: 'https://www.lancers.jp/mypage', login: /lancers\.jp\/(user\/login|login)/, prof: /lancers\.jp\/profile\/[^/?#]+$/ },
  sokudan:  { mei: 'SOKUDAN', url: 'https://sokudan.work/project_chat_rooms', login: /sokudan\.work\/(login|sign_in|users\/sign_in)/ },
  workship: { mei: 'Workship', url: 'https://goworkship.com/like/initiative', login: /goworkship\.com\/(login|signin|sign_in)/ },
  skillshift: { mei: 'スキルシフト', url: 'https://www.skill-shift.com/member/message-list', login: /skill-shift\.com\/(login|member\/login|signin|sign_in)/ },
  aicw:     { mei: 'AIクラウドワークス', url: 'https://crowdworks.jp/aicw/project_interests', login: /crowdworks\.jp\/login/ },
  fiverr:   { mei: 'Fiverr', url: 'https://www.fiverr.com/users/me/manage_gigs', login: /fiverr\.com\/(login|join)/ },
  upwork:   { mei: 'Upwork', url: 'https://www.upwork.com/nx/find-work/', login: /upwork\.com\/(ab\/account-security\/login|nx\/signup|login)/ },
}
const GO = /(本人確認[^。\n]{0,12}|口座[^。\n]{0,12}|identity verif[^.\n]{0,20}|ID verif[^.\n]{0,20}|Get paid[^.\n]{0,20})/gi
const arg = process.argv[2]
const names = arg === 'all' ? Object.keys(BA) : [arg]
if (!arg || names.some(n => !BA[n])) { console.log('使い方: node tools/shoki-kakunin.cjs <' + Object.keys(BA).join('|') + '|all>'); process.exit(2) }
;(async () => {
  let b
  try { b = await S.playwright().chromium.connectOverCDP(S.cdp, { timeout: 20000 }) }
  catch (e) { console.log('🔴 ブラウザ（' + S.cdp + '）につなげない＝ログインは見ていない。ログイン済みの Chrome を --remote-debugging-port で起こす（docs/15）'); process.exit(3) }
  const p = await S.tab(b, 'shoki-kakunin'); let aka = 0
  for (const n of names) {
    const s = BA[n]
    try {
      await p.goto(s.url, { waitUntil: 'domcontentloaded', timeout: 45000 }); await p.waitForTimeout(2500)
      const u = p.url()
      if (s.login.test(u)) { aka++; console.log(`🔴 ${s.mei} ログインの頁に戻された（${u.slice(0, 80)}）＝このブラウザでは未ログイン`); continue }
      const t = await p.evaluate(() => document.body ? document.body.innerText : '')
      let go = [...new Set((t.match(GO) || []).map(x => x.replace(/\s+/g, ' ').trim()))].slice(0, 4), pu = ''
      if (s.prof) {  // 自分のプロフィールを開き、本人確認・NDA・口座などの済み／未を読む
        const h = typeof s.prof === 'string' ? s.prof : await p.evaluate(re => [...document.querySelectorAll('a[href]')].map(a => a.href).find(x => new RegExp(re).test(x)) || '', s.prof.source)
        if (h) { await p.goto(h, { waitUntil: 'domcontentloaded', timeout: 45000 }); await p.waitForTimeout(2000); pu = p.url()
          const j = await p.evaluate(() => {
            const r = []
            // ランサーズ：見出しの印。緑のチェックが付いていれば済み
            document.querySelectorAll('li.p-profile-header__status').forEach(li => r.push(li.textContent.trim() + (li.querySelector('.c-icon--green') ? ' 済' : ' 未（緑の印なし）')))
            // クラウドワークス：プロフィールの項目名の次の数行に「未登録／登録済み」などが出る
            const L = (document.body ? document.body.innerText : '').split('\n').map(x => x.trim())
            L.forEach((l, i) => { if (/^(本人確認書類提出|NDA（秘密保持契約）|振込先口座登録|インボイス)$/.test(l)) { const st = L.slice(i + 1, i + 5).find(x => /未登録|未提出|登録済|提出済|締結済|確認済|審査中/.test(x)); r.push(l + ' ' + (st || '─（状態の語が出ていない）')) } })
            return r })
          if (j.length) go = j }
        else pu = '（自分のプロフィールへの道が頁に無かった）' }
      console.log(`✅ ${s.mei} ログイン済み（開いた頁 ${u.slice(0, 60)}${pu ? ' → ' + pu.slice(0, 70) : ''}）／確認の状態：${go.length ? go.join('／') : '─ 頁の文に無い（設定の頁を docs/15 の手順で開いて目で見る）'}`)
    } catch (e) { aka++; console.log(`🔴 ${s.mei} 開けなかった（${String(e.message).split('\n')[0].slice(0, 80)}）`) }
  }
  process.exit(aka ? 1 : 0)
})()
