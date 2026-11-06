#!/bin/bash
# 【記録】その日の応募・見送りの数（進捗の報告はこれ1本で数える・数え方が割れないように）
# 入力: 日付 YYYY-MM-DD（無ければ今日）／<置き場>/oubo-kiroku.tsv
# 出力: 「日付 応募 N件（場ごと）／見送り M件」と数え方の1行
# 止まる条件: 記録が無いとき rc=2（0件と言わない）
# 呼び方: bash tools/kyou-kazu.sh [YYYY-MM-DD]
T="$(cd "$(dirname "$0")" && pwd)"
DATA=$(python3 -c "import sys;sys.path.insert(0,'$T');import settei as S;print(S.DATA)") || exit 9
D=${1:-$(date +%Y-%m-%d)}; F="$DATA/oubo-kiroku.tsv"
[ -f "$F" ] || { echo "🔴 記録が無い（$F）＝数えられない"; exit 2; }
awk -F'\t' -v d="$D" '$1 ~ "^"d { if ($7 ~ /^(応募|提案)/) {o[$2]++; O++} else if ($7 ~ /^見送り/) M++ }
END { printf "%s 応募 %d件（", d, O; s=""; for (k in o) {printf "%s%s %d", s, k, o[k]; s="・"}; printf "）／見送り %d件\n", M }' "$F"
echo "数え方：oubo-kiroku.tsv・1列目が ${D}・7列目の頭が 応募|提案＝応募／見送り＝見送り（測った $(date +%H:%M)）"
