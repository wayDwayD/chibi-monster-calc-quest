#!/usr/bin/env python3
"""src/game.src.html と assets/ から、素材を埋め込んだ単体の index.html を作る。
使い方: python3 tools/build.py"""
import base64, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = lambda *a: os.path.join(ROOT, *a)
MISSING = []
def d(path, mime):
    if not os.path.exists(path):  # 音源がない場合は無音で代用(音源は公開リポジトリに含めない)
        MISSING.append(path); path = p('assets', 'silence.mp3'); mime = 'audio/mpeg'
    return 'data:' + mime + ';base64,' + base64.b64encode(open(path, 'rb').read()).decode()
atlas = json.load(open(p('src', 'atlas.json')))
SE = ['tap','correct','wrong','hit','hit_evolved','defeat','levelup','evolve','clear','zannen','coin','egg_shake','egg_crack','egg_break','rare','cursor_a']
pack = {
  'atlas': {c: {'f': d(p('assets','atlas',c+'.webp'), 'image/webp'), 'r': a['r'], 'as': a.get('as', c)} for c, a in atlas.items()},
  'bg': {n: d(p('assets','bg',n+'.jpg'), 'image/jpeg') for n in ['home','training','boss','boss_ura','gacha','zukan']},
  'se': {n: d(p('assets','se',n+'.mp3'), 'audio/mpeg') for n in SE},
  'bgm': {n: d(p('assets','bgm',n+'.mp3'), 'audio/mpeg') for n in ['home','training','boss']},
}
pack['silent'] = bool(MISSING)
src = open(p('src', 'game.src.html'), encoding='utf8').read()
k = src.index('<script>\n"use strict";')
page = src[:k] + '<script id="pack" type="application/json">' + json.dumps(pack, separators=(',', ':')) + '</script>\n' + src[k:]
head = ('<!doctype html><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">'
        '<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black"><meta name="apple-mobile-web-app-title" content="けいさんクエスト">'
        '<link rel="apple-touch-icon" href="assets/icon-180.png"><link rel="icon" href="assets/icon-180.png">')
open(p('index.html'), 'w', encoding='utf8').write(head + page)
print('index.html', round(len(page) / 1e6, 1), 'MB')
