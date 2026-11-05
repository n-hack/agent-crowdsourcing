#!/usr/bin/env python3
# 納品の表（xlsx）を人が見やすい形に整える（2026-11-05 の決まり：納品は全部、人が見やすい形で）
# 使い方: python3.14 xlsx-mieru.py <入力.xlsx|入力.csv> [出力.xlsx]   出力を省くと入力と同じ名前の .xlsx に上書き
# やること: 見出しを色つき太字・1行目と1列目を固定・絞り込み・列の幅を中身に合わせる（全角は2文字分）・折り返し・罫線・URL をリンクに・1行おきに薄い色
# 最後に「確かめ」を出す（見出しの色／固定／絞り込み／幅の最大と最小）。🔴 が出たら渡さない
import sys, csv, os, unicodedata
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

HEAD_FILL = PatternFill('solid', fgColor='1F4E79')
ZEBRA_FILL = PatternFill('solid', fgColor='EEF3F8')
THIN = Side(style='thin', color='BFBFBF')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

def haba(s):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in str(s or ''))

def yomu(p):
    if p.lower().endswith('.csv'):
        wb = Workbook(); ws = wb.active
        with open(p, encoding='utf-8-sig', newline='') as f:
            for row in csv.reader(f): ws.append(row)
        return wb
    return load_workbook(p)

def totonoeru(ws):
    if ws.max_row < 1: return
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF'); c.fill = HEAD_FILL
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True); c.border = BORDER
    ws.row_dimensions[1].height = 24
    for r in range(2, ws.max_row + 1):
        for c in ws[r]:
            c.border = BORDER
            c.alignment = Alignment(vertical='top', wrap_text=True)
            v = str(c.value or '')
            if v.startswith(('http://', 'https://')):
                c.hyperlink = v; c.font = Font(color='0563C1', underline='single')
            if r % 2 == 0: c.fill = ZEBRA_FILL
    for col in ws.columns:
        w = max((haba(c.value) for c in col), default=8)
        ws.column_dimensions[col[0].column_letter].width = max(8, min(w + 2, 60))
    ws.freeze_panes = 'B2' if ws.max_column > 3 else 'A2'
    ws.auto_filter.ref = ws.dimensions

def main():
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + '.xlsx'
    wb = yomu(src)
    for ws in wb.worksheets: totonoeru(ws)
    wb.save(dst)
    wb2 = load_workbook(dst); ng = 0
    for ws in wb2.worksheets:
        h = ws['A1']; ws_w = [ws.column_dimensions[c[0].column_letter].width for c in ws.columns]
        ok_head = bool(h.font.bold) and h.fill.fgColor.rgb.endswith('1F4E79')
        ok = ok_head and bool(ws.freeze_panes) and bool(ws.auto_filter.ref)
        ng += 0 if ok else 1
        print(('✅' if ok else '🔴'), ws.title, '行', ws.max_row, '列', ws.max_column, '見出し', '○' if ok_head else '×', '固定', ws.freeze_panes, '絞り込み', ws.auto_filter.ref, '幅', min(ws_w or [0]), '〜', max(ws_w or [0]))
    print('出力', dst)
    sys.exit(1 if ng else 0)

if __name__ == '__main__':
    main()
