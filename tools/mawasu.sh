#!/bin/bash
# 【入口】1日の回し方を1コマンドで1周：巡回 → 門 → 応募文（下書き）→ 応募（--go のときだけ送る）→ 返事の見張り → 出し漏れの検算
# 入力: config/profile.json（置き場・CDP・巡回の語・メールの見張り）／環境変数 CS_DATA・CS_PROFILE・CS_CDP_URL ／ --go（送る）・--no-browser（ログインの要る段を飛ばす）
# 出力: 段ごとの1行と、要対応（新しい返事・要返信・状態の変化・出し漏れ）の中身。<置き場>/mawasu.log に段ごとの1行。門の全行は <置き場>/junkai/mon-YYYYMMDD-HHMM.txt
# 止まる条件: どれかの段の道具が落ちたら、その段の名前と理由を出して rc=2 で止まる。1周が通り要対応が無ければ rc=0／要対応ありは rc=1
# 呼び方: bash tools/mawasu.sh [--go] [--no-browser]（長いので裏で回す・繰り返すなら終わるたびに呼び直す）
T="$(cd "$(dirname "$0")" && pwd)"; cd "$T/.." || exit 2
GO=0; NOBR=0
for a in "$@"; do case "$a" in --go) GO=1 ;; --no-browser) NOBR=1 ;; *) echo "使い方: bash tools/mawasu.sh [--go] [--no-browser]"; exit 2 ;; esac; done
DATA=$(python3 -c "import sys;sys.path.insert(0,'$T');import settei as S;print(S.DATA)") || { echo "🔴 設定が読めない（config/profile.json）"; exit 2; }
CDP=$(node "$T/settei.cjs" | python3 -c "import json,sys;print(json.load(sys.stdin)['つなぐ先'])") || { echo "🔴 設定が読めない（settei.cjs）"; exit 2; }
mkdir -p "$DATA"; LOG="$DATA/mawasu.log"; YOU=0
kiroku() { echo "$(date '+%m-%d %H:%M') $1" >> "$LOG"; echo "$1"; }
tomaru() { kiroku "🔴 段「$1」で止まった：$2"; exit 2; }
jikan() { local s=$1; shift; perl -e 'alarm shift; exec @ARGV' "$s" "$@"; }   # macOS には timeout が無い

# 0 門（このリポジトリの道具が動く環境か）
node "$T/nhack-mon.cjs" >/dev/null || tomaru 準備 "nhack-mon.cjs が通らない"

# 1 巡回
out=$(python3 "$T/cw-junkai.py" 2>&1); rc=$?
[ $rc -ne 0 ] && tomaru 巡回 "cw-junkai.py rc=$rc ／ $(echo "$out" | tail -1)"
f=$(echo "$out" | head -1); n=$(($(wc -l < "$f") - 1))
kiroku "1 巡回 ✅ 新しい候補 $n 件（$(echo "$out" | tail -1 | cut -c1-80)…）"

# 2 門（分野・できるか・勧誘・二重応募・取らない条件）
hoshi=""
if [ "$n" -gt 0 ]; then
  out=$(python3 "$T/cw-tantei.py" "$f" 2>&1); rc=$?
  [ $rc -ne 0 ] && tomaru 門 "cw-tantei.py rc=$rc ／ $(echo "$out" | tail -2 | tr '\n' ' ')"
  hoshi=$(echo "$out" | grep '^★ ')
  echo "$out" > "$DATA/junkai/mon-$(basename "$f" .tsv).txt"   # 門の全行（★＝応募文へ・☆＝読んで決める・印なし＝落ちた理由つき）
  kiroku "2 門 ✅ $(echo "$out" | tail -1)（全行は junkai/mon-$(basename "$f" .tsv).txt）"
else kiroku "2 門 ─ 候補 0 件（巡回の新着なし）"; fi

# 3 応募文（下書き。中身の穴は残る＝エージェントが本文を読んで埋める）
nd=0
while IFS= read -r l; do [ -z "$l" ] && continue
  id=$(echo "$l" | awk '{print $2}')
  aite=$(awk -F'\t' -v i="$id" '$2==i{print $4; exit}' "$f"); dai=$(awk -F'\t' -v i="$id" '$2==i{print $7; exit}' "$f")
  o=$(node "$T/oubo-shitagaki.cjs" cw "$id" "${aite:--}" "$dai" 2>&1); rc=$?
  [ $rc -ne 0 ] && tomaru 応募文 "oubo-shitagaki.cjs $id rc=$rc ／ $(echo "$o" | head -1)"
  nd=$((nd+1))
done <<< "$hoshi"
kiroku "3 応募文 ✅ 下書き $nd 件（$DATA/oubo-bun/・まだ型。docs/05 の手順1〜6で穴と型の行を募集に合わせて埋め、.json に金額と納期を書き、node tools/shitagaki-kakunin.cjs が ✅ を出すまでが「下書きまで」）"

# 4 応募（既定は送らない。--go のとき、穴が埋まり金額・納期があり確かめを通った下書きで、記録に応募の無い物だけ送る）
junbi=$(python3 - "$DATA" <<'PY'
import json, pathlib, re, sys
d = pathlib.Path(sys.argv[1]); k = d / 'oubo-kiroku.tsv'
zumi = set()
if k.exists():
    for l in open(k, encoding='utf-8', errors='replace'):
        c = l.rstrip('\n').split('\t')
        if len(c) >= 7 and re.match(r'(応募|提案)', c[6]): zumi |= {x.strip() for x in c[2].split('・')}
for j in sorted((d / 'oubo-bun').glob('cw-*.json')) if (d / 'oubo-bun').exists() else []:
    m = json.loads(j.read_text(encoding='utf-8')); t = j.with_suffix('.txt')
    if m.get('案件ID') in zumi or not t.exists() or re.search(r'\{[^{}\n]{1,20}\}', t.read_text(encoding='utf-8')): continue
    if m.get('金額') and m.get('納期'): print('\t'.join([m['案件ID'], str(t), str(m['金額']), str(m['納期'])]))
PY
)
# 送れる下書きは、確かめ（shitagaki-kakunin.cjs：穴・型の行・宛名・金額と帯・2つの門）を通った物だけ
junbi=$(while IFS=$'\t' read -r id txt kin nou; do [ -z "$id" ] && continue
  node "$T/shitagaki-kakunin.cjs" "$txt" >/dev/null 2>&1 && printf '%s\t%s\t%s\t%s\n' "$id" "$txt" "$kin" "$nou"; done <<< "$junbi")
nj=$(echo -n "$junbi" | grep -c .)
if [ $GO -eq 1 ] && [ $NOBR -eq 0 ] && [ "$nj" -gt 0 ]; then
  ok=0; ng=0
  while IFS=$'\t' read -r id txt kin nou; do
    o=$(jikan 600 node "$T/cwapply.cjs" "$id" "$txt" "$kin" "$nou" - go 2>&1); rc=$?
    case $rc in 0) ok=$((ok+1)) ;; 2) ng=$((ng+1)); echo "  門で止めた $id：$(echo "$o" | grep '🔴' | head -1)" ;; *) tomaru 応募 "cwapply.cjs $id rc=$rc ／ $(echo "$o" | tail -1)" ;; esac
  done <<< "$junbi"
  kiroku "4 応募 ✅ 送った $ok 件 ／ 門で止めた $ng 件"
elif [ $GO -eq 1 ] && [ $NOBR -eq 1 ]; then kiroku "4 応募 ─ --no-browser なので送らない（送れる下書き $nj 件）"
else kiroku "4 応募 ─ 下書きまで（送れる下書き $nj 件・送るのは --go）"; fi

# 5 返事の見張り（メール → CW の応募ごとの部屋 → 応募一覧の状態の変化）
out=$(python3 "$T/henji-mihari.py" 2>&1); rc=$?
case $rc in 0) kiroku "5 返事（メール）✅ $(echo "$out" | tail -1)" ;; 1) YOU=1; kiroku "5 返事（メール）🔔 新しい便あり"; echo "$out" ;;
  4) kiroku "5 返事（メール）🟡 未設定＝メールは見ていない" ;; *) tomaru 返事の見張り "henji-mihari.py rc=$rc ／ $(echo "$out" | tail -1)" ;; esac
if [ $NOBR -eq 1 ]; then kiroku "5 返事（サイト）─ --no-browser なので見ていない（応募の部屋にだけ届く便がある）"
else
  curl -s -m 5 "$CDP/json/version" >/dev/null || tomaru 返事の見張り "ブラウザ（$CDP）につなげない。ログイン済みの Chrome を --remote-debugging-port で起こすか、--no-browser で飛ばす"
  out=$(jikan 900 node "$T/cw-thread-check.cjs" --atarashii 2>&1); rc=$?
  case $rc in 0) kiroku "5 返事（CW の部屋）✅ $(echo "$out" | tail -1)" ;; 1) YOU=1; kiroku "5 返事（CW の部屋）🔔 $(echo "$out" | grep -c '^要返信') 件"; echo "$out" | grep '^要返信' ;;
    *) tomaru 返事の見張り "cw-thread-check.cjs rc=$rc ／ $(echo "$out" | tail -1)" ;; esac
  prev=$(ls "$DATA"/cw-joutai-*.tsv 2>/dev/null | sort | tail -1); now="$DATA/cw-joutai-$(date +%Y%m%d-%H%M).tsv"
  out=$(jikan 600 node "$T/cw-oubo-joutai.cjs" "$now" 2>&1); rc=$?
  if [ $rc -eq 3 ]; then kiroku "5 状態一覧 🟡 途中で切れた見込み・控えにしない（$(echo "$out" | tail -1)）"
  elif [ $rc -ne 0 ]; then tomaru 返事の見張り "cw-oubo-joutai.cjs rc=$rc ／ $(echo "$out" | tail -1)"
  elif [ -n "$prev" ] && [ "$prev" != "$now" ]; then h=$(python3 "$T/cw-joutai-hikaku.py" --naru "$prev" "$now"); rc=$?
    if [ $rc -eq 1 ]; then YOU=1; kiroku "5 状態一覧 🔔 契約・条件など状態が変わった"; echo "$h"; elif [ $rc -ne 0 ]; then tomaru 返事の見張り "cw-joutai-hikaku.py rc=$rc"; else kiroku "5 状態一覧 ✅ $(echo "$out" | head -1)"; fi
  else kiroku "5 状態一覧 ✅ 初回の控え（$(echo "$out" | head -1)）"; fi
fi

# 6 出し漏れの検算
out=$(python3 "$T/dashi-more.py" 2>&1); rc=$?
case $rc in 0) kiroku "6 検算 ✅ $(echo "$out" | head -1)" ;; 1) YOU=1; kiroku "6 検算 🔔 $(echo "$out" | head -1)"; echo "$out" | tail -n +2 ;; *) tomaru 検算 "dashi-more.py rc=$rc ／ $(echo "$out" | tail -1)" ;; esac

[ $YOU -eq 1 ] && { kiroku "1周 終わり：要対応あり（上の 🔔 を全部返してから次の周へ）"; exit 1; }
kiroku "1周 終わり：要対応なし"; exit 0
