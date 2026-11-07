#!/usr/bin/env python3
"""撮影済みの動画の「無音を詰める → 文字起こし → 字幕を焼く」を1本で（撮影済みの解説動画・トーク動画の編集の受け向け）
使い方: python3 cut-jimaku.py 入力.mp4 出力.mp4 [無音とみなす秒=0.6] [模型=large-v3-turbo]
出すもの: 出力.mp4（詰めた・字幕つき）／出力.srt（字幕の下書き＝人の目で1文字ずつ直してから焼き直す）
ffmpeg に字幕の焼き込みが無いので、字幕は1行ずつ画像にして重ねる
"""
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
model = sys.argv[4] if len(sys.argv) > 4 else 'large-v3-turbo'
FONT = '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
tmp = tempfile.mkdtemp()
def sh(*a): return subprocess.run(a, capture_output=True, text=True)
dur = float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src).stdout)
W, H = map(int, sh('ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', src).stdout.strip().split(','))
# ① 無音の区間を見つけて、話している区間だけ残す（前後に0.15秒の余白）
log = sh('ffmpeg', '-i', src, '-af', f'silencedetect=n=-35dB:d={gap}', '-f', 'null', '-').stderr
ss = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; se = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
keep, t = [], 0.0
for a, b in zip(ss, se + [dur] * (len(ss) - len(se))):
    if a - t > 0.05: keep.append((max(0, t - 0.15), min(dur, a + 0.15)))
    t = b
if dur - t > 0.05: keep.append((max(0, t - 0.15), dur))
sel = '+'.join(f'between(t,{a:.3f},{b:.3f})' for a, b in keep)
cut = f'{tmp}/cut.mp4'
sh('ffmpeg', '-y', '-v', 'error', '-i', src, '-vf', f"select='{sel}',setpts=N/FRAME_RATE/TB", '-af', f"aselect='{sel}',asetpts=N/SR/TB", '-c:v', 'h264_videotoolbox', '-b:v', '8M', cut)
cd = float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', cut).stdout)
print(f'① 無音を詰めた：{dur:.1f}秒 → {cd:.1f}秒（残した区間 {len(keep)}）')
# ② 文字起こし（区切りごとの時刻つき）
r = sh('whisper', cut, '--model', model, '--language', 'ja', '--output_format', 'json', '--output_dir', tmp, '--fp16', 'False')
segs = json.load(open(f'{tmp}/cut.json'))['segments']
def ts(x): return f'{int(x//3600):02}:{int(x%3600//60):02}:{int(x%60):02},{int(x*1000%1000):03}'
srt = os.path.splitext(out)[0] + '.srt'
open(srt, 'w').write(''.join(f'{i}\n{ts(s["start"])} --> {ts(s["end"])}\n{s["text"].strip()}\n\n' for i, s in enumerate(segs, 1)))
print(f'② 文字起こし：{len(segs)} 行 → {srt}（★焼く前に1文字ずつ目で確かめる）')
# ③ 字幕を1行ずつ画像にして、時刻に合わせて重ねる
f = ImageFont.truetype(FONT, int(H * 0.055)); ins, flt = ['-i', cut], []
for i, s in enumerate(segs):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); tx = s['text'].strip()
    b = d.textbbox((0, 0), tx, font=f); d.text(((W - (b[2] - b[0])) // 2, H - (b[3] - b[1]) - int(H * 0.07)), tx, font=f, fill='white', stroke_width=int(H * 0.006), stroke_fill='black')
    p = f'{tmp}/s{i}.png'; im.save(p); ins += ['-i', p]
    prev = '0:v' if i == 0 else f'v{i}'
    flt.append(f"[{prev}][{i+1}:v]overlay=0:0:enable='between(t,{s['start']:.2f},{s['end']:.2f})'[v{i+1}]")
if segs:
    sh('ffmpeg', '-y', '-v', 'error', *ins, '-filter_complex', ';'.join(flt), '-map', f'[v{len(segs)}]', '-map', '0:a', '-c:v', 'h264_videotoolbox', '-b:v', '8M', '-c:a', 'aac', out)
else:
    sh('cp', cut, out)
print(f'③ できた：{out}')
