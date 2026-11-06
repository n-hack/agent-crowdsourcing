#!/usr/bin/env python3
"""台本（daihon.json）を Mac の読み上げ（say・日本語の声）で1本の音声にする。

使い方:
  python3 onsei.py                       # kaigi.m4a を作る
  python3 onsei.py --nuku s21 -o kowashi.m4a   # 台詞 s21 を抜いた壊れた回の音声

要る物: macOS の say と ffmpeg。実在の人の声はまねない（OS に入っている合成の声だけ）。
"""
import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

KOKO = pathlib.Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--daihon", default=str(KOKO / "daihon.json"))
    p.add_argument("--nuku", action="append", default=[], help="抜く台詞の id（壊れた回を作るとき）")
    p.add_argument("-o", "--out", default=str(KOKO / "kaigi.m4a"))
    a = p.parse_args()

    d = json.loads(pathlib.Path(a.daihon).read_text(encoding="utf-8"))
    ids = {s["id"] for s in d["serifu"]}
    for n in a.nuku:
        if n not in ids:
            print(f"🔴 抜く台詞 {n} が台本に無い", file=sys.stderr)
            return 2
    serifu = [s for s in d["serifu"] if s["id"] not in a.nuku]

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        silence = tmp / "ma.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i",
                        "anullsrc=r=22050:cl=mono", "-t", "0.6", str(silence)], check=True)
        lst = []
        for i, s in enumerate(serifu):
            f = tmp / f"{i:03d}.aiff"
            subprocess.run(["say", "-v", d["koe"][s["hito"]], "-o", str(f), s["bun"]], check=True)
            w = tmp / f"{i:03d}.wav"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(f), "-ar", "22050", "-ac", "1", str(w)], check=True)
            lst += [w, silence]
        (tmp / "list.txt").write_text("".join(f"file '{x}'\n" for x in lst), encoding="utf-8")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", str(tmp / "list.txt"), "-c:a", "aac", "-b:a", "48k", a.out], check=True)

    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nk=1:nw=1", a.out], capture_output=True, text=True).stdout.strip()
    sec = float(dur)
    print(f"台詞 {len(serifu)} 本（抜いた台詞 {','.join(a.nuku) or 'なし'}）→ {pathlib.Path(a.out).name}  長さ {int(sec // 60)}分{int(sec % 60):02d}秒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
