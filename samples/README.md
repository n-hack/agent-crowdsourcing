# ポートフォリオの見本（実物）

どのエージェントでも同じに使えるように、templates/portfolio/ の型から実際に作って動かした見本です。**題材はすべて架空で、実在の会社・個人・依頼主のデータは使っていません。** 各フォルダの README に、動かした出力をそのまま貼っています。

| 見本 | フォルダ | 型 | 動かし方 |
|---|---|---|---|
| 01 会社リストの CSV（20行・列の型と確かめの印つき） | [01-kaisha-list-csv](01-kaisha-list-csv/) | [型](../templates/portfolio/01-kaisha-list-csv.md) | `python3 make_list.py` |
| 02 Excel の自動集計（数式で動く xlsx と合計の突き合わせ） | [02-excel-shuukei](02-excel-shuukei/) | [型](../templates/portfolio/02-excel-shuukei.md) | `python3 shuukei.py`（openpyxl が要る） |
| 03 問い合わせ FAQ の自動返答（20問・危ない下書きを止める） | [03-faq-jidou-henji](03-faq-jidou-henji/) | [型](../templates/portfolio/03-faq-jidou-henji.md) | `python3 henji.py tameshi` |
| 04 文字起こしと議事録（架空の会議を読み上げた音声・決まったことと宿題を数える） | [04-mojiokoshi-gijiroku](04-mojiokoshi-gijiroku/) | [型](../templates/portfolio/04-mojiokoshi-gijiroku.md) | `python3 gijiroku.py mojiokoshi/kaigi.json`（文字起こしは手元の whisper） |
| 05 データ取得の小道具（手元に立てた架空の頁から CSV・形が変わったら止まる） | [05-data-shutoku](05-data-shutoku/) | [型](../templates/portfolio/05-data-shutoku.md) | `python3 shutoku.py`（先に手元で http.server を立てる） |

04 の音声は OS の読み上げの声で作った物（実在の人の声・実在の会議の録音は使っていません）。05 の取りに行く先は手元（127.0.0.1）に立てた架空の頁だけで、外のサイトには取りに行っていません。

## 使い方（エージェント）
1. 自分の手元で各フォルダの道具を動かし、README と同じ出力が出るかを見る（出なければ使わない）
2. 公開の頁に載せるのは、README の「出来上がりの先頭」「動かした記録」と、型の「ポートフォリオの欄の説明文」（{料金の下限} は問診票から）
3. 架空の題材だと頁の頭と説明文に必ず書く。実績・お客様の名前・納品の件数・売上の数字を足さない（docs/16）
