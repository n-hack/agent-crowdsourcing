# 見本5 データ取得の小道具（架空の店舗一覧の頁から CSV へ）

**見本として作った物です。店舗名・住所・営業時間はすべて架空で、実在のお店・会社・個人・依頼主のデータは使っていません。** 取りに行く先は、この見本のために手元（127.0.0.1）に立てた頁だけで、外のサイトには一度もアクセスしていません。
作り方と見せ方の型は [templates/portfolio/05-data-shutoku.md](../../templates/portfolio/05-data-shutoku.md)。本番では型のとおり、相手の頁の robots.txt と利用規約を先に読んでから取ります。この見本は「表の取り方・頁送り・前回との差・頁の形が変わったときの止まり方」を見せるための物です。

## 置いてある物
| ファイル | 中身 |
|---|---|
| shutoku.py | 頁から表を取り CSV に書く（Python 3 の標準だけで動く）。手元の頁しか取らない |
| site/robots.txt | 手元の頁の決まり（取ってよい） |
| site/seijou/ | 想定どおりの形の頁（index.html・page2.html に5店ずつ・計10店） |
| site/kawatta/ | 頁の形を変えた版（表の class と列の見出しを変えた） |
| site/midashi/ | 列の見出しだけ変えた版（店舗名→名前・住所→所在地。class はそのまま） |
| tenpo_ichiran.csv | 出来上がり 10行（UTF-8・BOM 付きで Excel でも文字化けしない） |

## 動かし方
```
python3 -m http.server 8765 --bind 127.0.0.1 --directory site &   # 手元に頁を立てる
python3 shutoku.py                                                # 正常な回（rc=0）
python3 shutoku.py http://127.0.0.1:8765/kawatta/index.html       # 頁の形を変えた回（rc=2）
python3 shutoku.py http://127.0.0.1:8765/midashi/index.html       # 見出しだけ変えた回（rc=2）
```

## 決まり（shutoku.py が守ること）
- 手元（127.0.0.1・localhost）の頁しか取らない。外の URL を渡すと取らずに止まる（rc=2）
- 取る前に robots.txt を読む。「次の頁」をたどるときは1頁ごとに1秒空ける
- 表は class="tenpo-ichiran" で探し、列の見出しが「店舗ID・店舗名・都道府県・住所・営業時間・定休日」と一字一句同じかを見る
- 形が違う・行が0・空の欄がある行が半分を超えた・店舗ID が重なった、のどれかなら、**空の表を出さず、前回の CSV も書き換えずに rc=2 で止まり、理由を出す**
- 前回の CSV があれば、増えた店と消えた店を出す

## 動かした記録（2026-11-06・この順に続けて打った・「印」は CSV の md5 の頭8桁）
```
$ python3 shutoku.py 
robots.txt を読んだ：取ってよい（http://127.0.0.1:8765/robots.txt）
1頁目 http://127.0.0.1:8765/seijou/index.html … 5 行
2頁目 http://127.0.0.1:8765/seijou/page2.html … 5 行
✅ 2 頁から 10 行を tenpo_ichiran.csv に書いた（空の欄がある行 0）
前回の CSV：無し（今回が1回目）
rc=0
tenpo_ichiran.csv の印 011dd2a1

$ python3 shutoku.py 
robots.txt を読んだ：取ってよい（http://127.0.0.1:8765/robots.txt）
1頁目 http://127.0.0.1:8765/seijou/index.html … 5 行
2頁目 http://127.0.0.1:8765/seijou/page2.html … 5 行
✅ 2 頁から 10 行を tenpo_ichiran.csv に書いた（空の欄がある行 0）
前回との差：増えた 0 店 ／ 消えた 0 店
rc=0
tenpo_ichiran.csv の印 d1baf2ba

$ python3 shutoku.py http://127.0.0.1:8765/kawatta/index.html
robots.txt を読んだ：取ってよい（http://127.0.0.1:8765/robots.txt）
🔴 止めた：頁の形が変わった：class="tenpo-ichiran" の表が無い（http://127.0.0.1:8765/kawatta/index.html・見つかった表の class：shop-list）
🔴 空の表は出さない・前回の CSV も書き換えない（rc=2）
rc=2
tenpo_ichiran.csv の印 d1baf2ba

$ python3 shutoku.py http://127.0.0.1:8765/midashi/index.html
robots.txt を読んだ：取ってよい（http://127.0.0.1:8765/robots.txt）
🔴 止めた：頁の形が変わった：列の見出しが想定と違う（http://127.0.0.1:8765/midashi/index.html・2列目「店舗名」→「名前」／4列目「住所」→「所在地」）
🔴 空の表は出さない・前回の CSV も書き換えない（rc=2）
rc=2
tenpo_ichiran.csv の印 d1baf2ba

$ python3 shutoku.py https://example.com/
🔴 止めた：手元の頁ではない（example.com）。この見本は手元に立てた頁しか取らない
🔴 空の表は出さない・前回の CSV も書き換えない（rc=2）
rc=2
tenpo_ichiran.csv の印 d1baf2ba
```
2回目の印が1回目と違うのは、取得日時の列が変わったため。頁の形を変えた回・見出しを変えた回・外の URL の回のあとも印は d1baf2ba のままで、止まった回は前回の CSV を書き換えていない。手元の頁の記録（http.server の出力）にも 127.0.0.1 からの読みだけが残っている。

## 出来上がり（tenpo_ichiran.csv の全10行）
```
店舗ID,店舗名,都道府県,住所,営業時間,定休日,取得元URL,取得日時
T001,みほん珈琲 駅前店,架空県,見本市駅前1-1,8:00-20:00,水曜,http://127.0.0.1:8765/seijou/index.html,2026-11-06T16:27:31+09:00
T002,みほん珈琲 中央店,架空県,見本市中央2-3,9:00-21:00,なし,http://127.0.0.1:8765/seijou/index.html,2026-11-06T16:27:31+09:00
T003,ためしベーカリー,架空県,例え町4-5,7:00-18:00,月曜,http://127.0.0.1:8765/seijou/index.html,2026-11-06T16:27:31+09:00
T004,サンプル食堂,架空県,試し町6-7,11:00-22:00,火曜,http://127.0.0.1:8765/seijou/index.html,2026-11-06T16:27:31+09:00
T005,かくう書房,架空県,見本市本町8-9,10:00-20:00,なし,http://127.0.0.1:8765/seijou/index.html,2026-11-06T16:27:31+09:00
T006,見本青果店,仮置県,仮置市南1-2,9:00-19:00,日曜,http://127.0.0.1:8765/seijou/page2.html,2026-11-06T16:27:32+09:00
T007,ためし文具,仮置県,仮置市北3-4,10:00-19:00,水曜,http://127.0.0.1:8765/seijou/page2.html,2026-11-06T16:27:32+09:00
T008,サンプル花店,仮置県,仮置市東5-6,9:30-18:30,木曜,http://127.0.0.1:8765/seijou/page2.html,2026-11-06T16:27:32+09:00
T009,かくう理容室,仮置県,仮置市西7-8,9:00-19:00,月曜,http://127.0.0.1:8765/seijou/page2.html,2026-11-06T16:27:32+09:00
T010,みほん酒店,仮置県,仮置郡例え村9-10,10:00-21:00,なし,http://127.0.0.1:8765/seijou/page2.html,2026-11-06T16:27:32+09:00
```

## 見ていない範囲
- 本物の公開の頁（練習用と明記された頁を含む）からは取っていない。外へは出ない見本にしたため
- スプレッドシートへ書いた画面の画像はまだ無い（CSV を書くところまで）
- 型の指示文は「空の行が半分を超えたら rc=3」だが、この見本は止まる理由をまとめて rc=2 にした（止まった理由は1行目に出る）
