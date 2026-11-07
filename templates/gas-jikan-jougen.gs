/**
 * 実行時間の上限（6分）で止まらない一括処理の型
 * ・商品情報は最初に1回だけ読み込んで Map にする（行ごとにシートを読まない）
 * ・書き込みは配列にためて、まとめて setValues する（1セルずつ書かない）
 * ・5分を超えそうになったら「どこまで終わったか」を記録し、1分後に続きから自動で再開する
 */
const LIMIT_MS = 5 * 60 * 1000;           // 上限6分の手前で区切る
const KEY = 'HACCHU_NEXT_ROW';            // 続きの行番号を覚えておく名前

function startHacchu() {                   // ボタン・マクロから呼ぶ入口
  PropertiesService.getScriptProperties().setProperty(KEY, '0');
  runHacchu();
}

function runHacchu() {
  const t0 = Date.now();
  const props = PropertiesService.getScriptProperties();
  let i = Number(props.getProperty(KEY) || 0);
  const ss = SpreadsheetApp.getActive();
  const orders = ss.getSheetByName('注文データ').getDataRange().getValues().slice(1);   // 見出しを除く
  const items = new Map(ss.getSheetByName('商品情報').getDataRange().getValues().slice(1).map(r => [String(r[0]), r]));
  const out = [];
  for (; i < orders.length; i++) {
    if (Date.now() - t0 > LIMIT_MS) break;                    // 時間が来たらここで区切る
    const o = orders[i], it = items.get(String(o[0]));
    out.push([o[0], it ? it[1] : '（商品情報なし）', o[1], it ? it[2] * o[1] : '']);  // 品番・品名・数量・金額
  }
  if (out.length) {
    const sh = ss.getSheetByName('発注書');
    sh.getRange(sh.getLastRow() + 1, 1, out.length, out[0].length).setValues(out);     // まとめて1回で書く
  }
  clearTriggers_();
  if (i < orders.length) {                                    // まだ残っている → 続きを予約
    props.setProperty(KEY, String(i));
    ScriptApp.newTrigger('runHacchu').timeBased().after(60 * 1000).create();
  } else {
    props.deleteProperty(KEY);                                // 全部終わった
  }
}

function clearTriggers_() {
  ScriptApp.getProjectTriggers().filter(t => t.getHandlerFunction() === 'runHacchu').forEach(t => ScriptApp.deleteTrigger(t));
}
