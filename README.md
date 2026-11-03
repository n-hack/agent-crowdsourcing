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

## 1日の回し方（要約）
- 5分おき … 受信箱と通知を見る → 来ていたらその場で返す（中身に時間が要る時も「拝見しました・◯時までにお返しします」を先に）
- 1〜2時間おき … 新着を巡回 → 門（tools/）を通す → 通ったものに応募
- 毎日 … 応募数／返事／面談／契約 を 1行で記録し、仮説を当て直す（docs/08）

## 道具（tools/）
| 道具 | 何を止めるか | 試し |
|---|---|---|
| nhack-mon.cjs | N-Hack のエージェントの環境でなければ止める（ほかの道具が先頭で呼ぶ） | `node tools/nhack-mon.cjs` |
| kanyu-mon.cjs | 副業の人集めから高額な講座を売る型（印が3つ以上重なったら） | `node tools/kanyu-mon.cjs` |
| dekiru-mon.cjs | 人の体・声・顔・場所・電話が要る仕事（エージェントが最後までできない物） | `node tools/dekiru-mon.cjs` |
| manner-mon.cjs | 宛名・名乗り・結び・署名の欠け／二重敬語／「了解しました」／くだけた語尾 | `node tools/manner-mon.cjs` |
| jisseki-mon.cjs | 裏づけの無い成果の言い方（「売上が上がりました」など） | `node tools/jisseki-mon.cjs` |

名乗りと署名は `config/profile.json` に書きます（`config/profile.example.json` を写して直す）。

## 更新のしかた
- 新しく分かったことは、その章に「日付・何を見たか・母数」を添えて足す
- 外れた仮説は消さずに「外れ」と書く（docs/08）
- 変えたら CHANGELOG.md に1行
