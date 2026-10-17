#!/usr/bin/env python3
"""assets/se と assets/bgm の音源を1つの chibi-sounds.json にまとめる(リポジトリには含めない)。
iPad の「おんげんを よみこむ」で1回だけ読み込む。使い方: python3 tools/make_sound_pack.py"""
import base64, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SE = ['tap','correct','wrong','hit','hit_evolved','defeat','levelup','evolve','clear','zannen','coin','egg_shake','egg_crack','egg_break','rare','cursor_a']
BGM = ['home','training','boss']
d = lambda f: 'data:audio/mpeg;base64,' + base64.b64encode(open(f, 'rb').read()).decode()
pack = {'v': 1, 'se': {n: d(os.path.join(ROOT,'assets','se',n+'.mp3')) for n in SE}, 'bgm': {n: d(os.path.join(ROOT,'assets','bgm',n+'.mp3')) for n in BGM}}
out = os.path.join(ROOT, 'chibi-sounds.json')
json.dump(pack, open(out, 'w'), separators=(',', ':'))
print(out, round(os.path.getsize(out) / 1e6, 1), 'MB')
