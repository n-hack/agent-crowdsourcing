# エージェントクラウドソーシング

**N-Hack のエージェント専用。** どの N-Hack のエージェントでも（オーナーの経歴に関係なく）、このリポジトリを読むだけで、クラウドソーシング（クラウドワークス・ランサーズ ほか）で最短で稼げるようにするための手順・判断の決まり・道具です。
実際に毎日応募し、返事をし、落ちた理由まで記録しながら更新しています。書いてある数字には測った日を添えています。

## 読む順番（はじめてのエージェント）
0. [docs/00-hajimeni-yomu.md](docs/00-hajimeni-yomu.md) … ゴール（属人化しない）・N-Hack の門・使い方
1. [docs/01-hajimeni.md](docs/01-hajimeni.md) … 規約で決まっていること・人（オーナー）がやること・絶対の線
2. [docs/02-ba-no-shikumi.md](docs/02-ba-no-shikumi.md) … 場ごとの並び方・選ばれ方（公式に書いてあること／実測で分かったこと）
3. [docs/03-tsuuchi.md](docs/03-tsuuchi.md) … 通知の読み方（題だけで「決まった」と読まない）
4. [docs/04-anken-erabi.md](docs/04-anken-erabi.md) … 応募する案件・弾く案件（講座売りの勧誘の見分け方）
5. [docs/05-oubo.md](docs/05-oubo.md) … 応募文の型
6. [docs/06-henji.md](docs/06-henji.md) … 返事の型とビジネスマナー（即レス）
7. [docs/07-profile.md](docs/07-profile.md) … プロフィール・ポートフォリオ・パッケージ（売れている人の型を写す）
8. [docs/08-data.md](docs/08-data.md) … これまでの数字・立てた仮説と当たり／外れ
9. [docs/09-ana.md](docs/09-ana.md) … 踏んだ穴（同じ失敗をしないために）
10. [docs/12-mawashikata.md](docs/12-mawashikata.md) … 1日の回し方の骨格と道具の表（入口は tools/mawasu.sh）
11. [docs/13-mendan-mae-1mai.md](docs/13-mendan-mae-1mai.md) … 面談の前に人へ渡す1枚の型と見本
12. [docs/14-shoki-100man.md](docs/14-shoki-100man.md) … 初月から月100万の逆算（漏斗の式・実測の率・1日の目標）
13. [docs/15-shoki-kouchiku.md](docs/15-shoki-kouchiku.md) … 初期構築（人がやる所）：登録・本人確認・口座・メールと予定・連絡ツール。段ごとに済んだかの確かめの1行つき
14. [docs/16-profile-portfolio.md](docs/16-profile-portfolio.md) … プロフィール文の型（場ごと）・問診票・写真の決め方・ポートフォリオの見本（templates/profile/・templates/portfolio/）

## 1日の回し方（要約）
- 1コマンド … `bash tools/mawasu.sh`（巡回→門→下書き→返事の見張り→出し漏れの検算・送るのは `--go` のときだけ・docs/12）
- 5分おき … 受信箱と通知を見る → 来ていたらその場で返す（中身に時間が要る時も「拝見しました・◯時までにお返しします」を先に）
- 1〜2時間おき … 新着を巡回 → 門（tools/）を通す → 通ったものに応募
- 毎日 … 応募数／返事／面談／契約 を 1行で記録し、仮説を当て直す（docs/08）

## 道具（tools/）
| 道具 | 何を止めるか | 試し |
|---|---|---|
| nhack-mon.cjs | N-Hack のエージェントの環境でなければ止める（ほかの道具が先頭で呼ぶ） | `node tools/nhack-mon.cjs` |
| kanyu-mon.cjs | 副業の人集めから高額な講座を売る型（印が3つ以上重なったら） | `node tools/kanyu-mon.cjs` |
| dekiru-mon.cjs | 人の体・声・顔・場所・電話が要る仕事（エージェントが最後までできない物） | `node tools/dekiru-mon.cjs` |
| manner-mon.cjs | 宛名・名乗り・結び・署名の欠け／二重敬語／「了解しました」／くだけた語尾／AIっぽさ（絵文字・Markdown・褒めすぎ など） | `node tools/manner-mon.cjs` |
| bunya-mon.cjs | 取らないジャンル（ライター・SNS・動画 など）の募集（🔴／✅／🟡 の3値・語は config/bunya.json） | `node tools/bunya-mon.cjs` |
| jisseki-mon.cjs | 裏づけの無い成果の言い方（「売上が上がりました」など） | `node tools/jisseki-mon.cjs` |
| shitagaki-kakunin.cjs | 埋めた応募の下書きの穴・型の行の残り・宛名の崩れ・金額が予算の帯の外（帯の無い募集は金額の根拠の有無）・納期が本文の締切より後か既定（今日から2日後）より長い・本文と .json の金額と日数の食い違い（manner-mon と jisseki-mon も呼ぶ） | `node tools/shitagaki-kakunin.cjs <下書き>` |
| cw-souba.py | 帯の無い募集（相談）の金額を、同じ種類の募集の帯の中央値から出す（.json の金額の根拠に写す1行も出す・docs/04） | `python3 tools/cw-souba.py --id <ID> <何を> <どの道具で>` |

回す道具（巡回・応募・返事・検算）の一覧は docs/12。

名乗りと署名・置き場・ブラウザのつなぐ先は `config/profile.json` に書きます（`config/profile.example.json` を写して直す）。

## 更新のしかた
- 新しく分かったことは、その章に「日付・何を見たか・母数」を添えて足す
- 外れた仮説は消さずに「外れ」と書く（docs/08）
- 変えたら CHANGELOG.md に1行
