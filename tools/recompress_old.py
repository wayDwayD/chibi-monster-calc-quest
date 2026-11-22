#!/usr/bin/env python3
"""元のシート画像が残っていない古いアトラス(戦闘エフェクト・UI・ガチャ・アイテムなど)を、
見た目をほぼ変えずに軽くする(1回だけ実行する道具)。node+sharp が必要(cd tools && npm install)。
やり直しで劣化しないよう、処理したアトラスは assets/atlas/.recompressed に記録して2回目はとばす。
使い方: python3 tools/recompress_old.py"""
import os, subprocess, sys, tempfile, shutil
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = lambda *a: os.path.join(ROOT, *a)
NAMES = ['monsters','monsters2','bosses','enemies','fx_attack','fx_common','gacha','items','stickers','ui','drill']
done = set(open(p('assets','atlas','.recompressed')).read().split()) if os.path.exists(p('assets','atlas','.recompressed')) else set()
assert shutil.which('node') and os.path.isdir(p('tools','node_modules','sharp')), 'cd tools && npm install が先に必要です'
tot0 = tot1 = 0
for n in NAMES:
    if n in done: print(n, 'とばす(処理ずみ)'); continue
    f = p('assets','atlas',n+'.webp'); before = os.path.getsize(f)
    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td,'a.png'); Image.open(f).convert('RGBA').save(png)
        out = os.path.join(td,'o.webp')
        subprocess.run(['node', p('tools','encode_webp.js'), png, out, '90', '70'], check=True, capture_output=True)
        after = os.path.getsize(out)
        if after < before * .95: shutil.copy(out, f)
        else: after = before
    done.add(n); tot0 += before; tot1 += after
    print(f'{n}: {before//1024}KB -> {after//1024}KB')
open(p('assets','atlas','.recompressed'),'w').write('\n'.join(sorted(done))+'\n')
print(f'合計 {tot0//1024}KB -> {tot1//1024}KB')
