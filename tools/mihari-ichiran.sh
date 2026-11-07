#!/bin/bash
# 【見張りの見張り】回しが本当に回っているか・記録が壊れていないか・果たしていない約束を1枚で出す（読むだけ）。起こし直しの後と報告の前に打つ
# 入力: <置き場>/mawasu.log（最後に書かれた時刻）・oubo-kiroku.tsv（字の壊れた行）・yakusoku.tsv（「未」の約束）／上限の分 MAWASU_JOUGEN（既定 30）
# 出力: ✅／🔴 の行と、まだ果たしていない約束の一覧（プロセスが生きていても回っているとは限らない＝記録の新しさで見る）
# 止まる条件: 🔴 の数を rc で返す（0 なら全部 ✅）
# 呼び方: bash tools/mihari-ichiran.sh
T="$(cd "$(dirname "$0")" && pwd)"
DATA=$(python3 -c "import sys;sys.path.insert(0,'$T');import settei as S;print(S.DATA)") || exit 9
n=0; LIM=${MAWASU_JOUGEN:-30}
if [ -f "$DATA/mawasu.log" ]; then age=$(( ($(date +%s) - $(stat -f %m "$DATA/mawasu.log" 2>/dev/null || stat -c %Y "$DATA/mawasu.log")) / 60 ))
  if [ $age -gt "$LIM" ]; then echo "🔴 mawasu.log が ${age}分 書かれていない（上限 ${LIM}分）＝回っていない見込み"; n=$((n+1)); else echo "✅ mawasu.log ${age}分前 ／ $(tail -1 "$DATA/mawasu.log")"; fi
  oc=$(tail -50 "$DATA/mawasu.log" | grep -c '🔴 段'); if [ "$oc" -gt 0 ]; then echo "🔴 直近50行で段の止まり $oc 回：$(grep '🔴 段' "$DATA/mawasu.log" | tail -1)"; n=$((n+1)); else echo "✅ 直近50行で段の止まり 0"; fi
else echo "🔴 mawasu.log が無い（まだ1度も回していない）"; n=$((n+1)); fi
if [ -f "$DATA/oubo-kiroku.tsv" ]; then
  bad=$(python3 -c "
import sys
n=0
for l in open(sys.argv[1],'rb'):
  try: l.decode('utf-8')
  except UnicodeDecodeError: n+=1
print(n)" "$DATA/oubo-kiroku.tsv")
  if [ "$bad" -gt 0 ]; then echo "🔴 応募の記録に壊れた字の行が $bad 行（番号が読めない行がある）"; n=$((n+1)); else echo "✅ 応募の記録に壊れた字 0行"; fi
else echo "🟡 応募の記録がまだ無い"; fi
Y="$DATA/yakusoku.tsv"; if [ -f "$Y" ]; then echo "📌 まだ果たしていない約束 $(grep -c $'\t未\t' "$Y") 件"; grep $'\t未\t' "$Y" | python3 -c "import sys;[print(l.rstrip()[:120]) for l in sys.stdin]"; fi
exit $n
