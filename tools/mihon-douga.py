#!/usr/bin/env python3
"""解説動画の見本を作る（VOICEVOX のナレーション＋絵＋テロップ・横 1920x1080）
「◯◯の使用経験（必須）」の募集に、無料の道具を入れて見本を1本作ってから正直に応募するための道具。
要るもの … VOICEVOX エンジン（127.0.0.1:50021 で起動しておく）／ffmpeg／Pillow／日本語のフォント
台本 ……… タブ区切り1行1場面：絵のファイル<TAB>読み上げる文<TAB>テロップ（\\n で改行）<TAB>上の見出し（空でよい）
　　　　　 最後の行を「まとめ」にすると、色の背景＋下の字幕の帯（参考動画の後半の形）で作る
使い方 … python3 mihon-douga.py 台本.tsv 出力.mp4 [話者ID=3] [フォント]
守ること … VOICEVOX は声ごとの規約に従い、動画の中に「VOICEVOX:キャラ名」と入れる（この道具は右下に入れる）
　　　　　 絵は配布元の規約の範囲で使う（例：いらすとやは1作品20点まで）。読みは出力のカナで1行ずつ確かめる
"""
import json, os, subprocess, sys, tempfile, urllib.parse, urllib.request
if subprocess.run(['node', os.path.join(os.path.dirname(__file__), 'nhack-mon.cjs')]).returncode != 0: sys.exit(9)
from PIL import Image, ImageDraw, ImageFont
tsv, out = sys.argv[1], sys.argv[2]
spk = int(sys.argv[3]) if len(sys.argv) > 3 else 3
FONT = sys.argv[4] if len(sys.argv) > 4 else '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
E = 'http://127.0.0.1:50021'
CHARA = {3: 'ずんだもん', 2: '四国めたん', 8: '春日部つむぎ', 13: '青山龍星'}.get(spk, f'話者{spk}')
rows = [l.rstrip('\n').split('\t') for l in open(tsv, encoding='utf-8') if l.strip()]
tmp = tempfile.mkdtemp()

def post(path, data=None, ctype=None):
    req = urllib.request.Request(E + path, data=data, method='POST', headers={'Content-Type': ctype} if ctype else {})
    return urllib.request.urlopen(req, timeout=120).read()

def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))

def telop(n, text, head, last):
    im = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lines = text.replace('\\n', '\n').split('\n')
    if not last:
        f = ImageFont.truetype(FONT, 64); hs = [d.textbbox((0, 0), l, font=f) for l in lines]
        y = 1080 - (sum(b[3] - b[1] for b in hs) + 20 * (len(lines) - 1)) - 60
        for l, b in zip(lines, hs):
            d.text(((1920 - (b[2] - b[0])) // 2, y - b[1]), l, font=f, fill=(20, 20, 20), stroke_width=6, stroke_fill='white'); y += b[3] - b[1] + 20
    else:
        f = ImageFont.truetype(FONT, 60); hs = [d.textbbox((0, 0), l, font=f) for l in lines]
        W = max(b[2] - b[0] for b in hs) + 80; H = sum(b[3] - b[1] for b in hs) + 18 * (len(lines) - 1) + 60
        x0, y0 = (1920 - W) // 2, 1080 - H - 60; d.rounded_rectangle([x0, y0, x0 + W, y0 + H], 18, fill=(0, 0, 0, 165)); y = y0 + 30
        for l, b in zip(lines, hs):
            d.text(((1920 - (b[2] - b[0])) // 2, y - b[1]), l, font=f, fill='white'); y += b[3] - b[1] + 18
    if head:
        f = ImageFont.truetype(FONT, 72); b = d.textbbox((0, 0), head, font=f)
        d.text(((1920 - (b[2] - b[0])) // 2, 30 - b[1]), head, font=f, fill=(255, 170, 0), stroke_width=7, stroke_fill=(60, 20, 0))
    cf = ImageFont.truetype(FONT, 28); c = f'VOICEVOX:{CHARA}'; cb = d.textbbox((0, 0), c, font=cf)
    d.text((1920 - cb[2] - 24, 1080 - cb[3] - 16), c, font=cf, fill=(220, 220, 220) if last else (110, 110, 110))
    p = f'{tmp}/p{n}.png'; im.save(p); return p

parts = []
for n, r in enumerate(rows, 1):
    img, say, tel = r[0], r[1], r[2] if len(r) > 2 else r[1]
    head = r[3] if len(r) > 3 else ''
    last = n == len(rows) and len(rows) > 1
    q = post(f'/audio_query?speaker={spk}&text=' + urllib.parse.quote(say))
    kana = ''.join(m['text'] for a in json.loads(q)['accent_phrases'] for m in a['moras'])
    print(f'{n} 読み：{kana}')  # 読み間違いはここで見つけて、台本の字を変えて直す
    wav = f'{tmp}/v{n}.wav'; open(wav, 'wb').write(post(f'/synthesis?speaker={spk}', q, 'application/json'))
    d = round(dur(wav) + (0.8 if last else 0.4), 2); p = telop(n, tel, head, last); mp4 = f'{tmp}/c{n}.mp4'
    bg = f'gradients=s=1920x1080:r=30:d={d}:c0=0x1e3a5f:c1=0x2e7d6b:speed=0.02' if last else f'color=white:s=1920x1080:r=30:d={d}'
    pos = '(W-w)/2:130' if last else '(W-w)/2:150'; h = 640 if last else 560
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', bg, '-loop', '1', '-i', img, '-loop', '1', '-i', p, '-i', wav,
                    '-filter_complex', f'[1]scale=-1:{h}[im];[0][im]overlay={pos}:shortest=1[a];[a][2]overlay=0:0:shortest=1[v]',
                    '-map', '[v]', '-map', '3', '-t', str(d), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '48000', mp4], check=True)
    parts.append(mp4)
open(f'{tmp}/list.txt', 'w').write(''.join(f"file '{x}'\n" for x in parts))
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', f'{tmp}/list.txt', '-c', 'copy', out], check=True)
print(f'できた：{out}（{dur(out):.1f}秒・{len(parts)}場面）')
