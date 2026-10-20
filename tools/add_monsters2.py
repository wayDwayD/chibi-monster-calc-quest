#!/usr/bin/env python3
"""追加モンスター8体(進化前後で16枚)のシート assets/source/monsters2_sheet.png から
背景(絵に焼き込まれた市松模様)を取り除いて切り出し、assets/atlas/monsters2.webp と
src/atlas.json の "monsters2" を作る。
使い方: python3 tools/add_monsters2.py   (numpy / scipy / Pillow が必要)"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = lambda *a: os.path.join(ROOT, *a)

im = Image.open(p('assets', 'source', 'monsters2_sheet.png')).convert('RGB')
a = np.asarray(im).astype(int)
mn = a.min(2); sat = a.max(2) - mn
cand = (mn >= 215) & (sat <= 7)                 # 市松模様の色(白〜うす灰色・色味なし)
lab, n = ndi.label(cand)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
bg = np.isin(lab, list(border))                 # 外周につながった背景
objs = ndi.find_objects(lab)
for i in range(1, n + 1):                       # すきまから見える背景(2色の市松のみ)も背景にする
    if i in border: continue
    sl = objs[i - 1]; m = (lab[sl] == i)
    if m.sum() < 40: continue
    px = a[sl][m]; g = px.min(1)
    if (g < 236).mean() >= .2 and (g >= 248).mean() >= .2 and abs(px[:, 2].mean() - px[:, 0].mean()) <= 1.5:
        bg[sl] |= m
fg = ndi.binary_opening(~bg, iterations=1)
# 進化後の列は上下の絵がつながるので、行の境目で切る
for (x0, x1), ys in {(258, 660): [331, 624, 938], (905, 1254): [325, 628, 946]}.items():
    for y in ys: fg[y - 5:y + 5, x0:x1] = False
L, N = ndi.label(ndi.binary_dilation(fg, iterations=4))
cx = [143, 460, 780, 1070]
cy = [[218, 170, 228, 170], [506, 480, 520, 475], [814, 780, 806, 785], [1111, 1090, 1127, 1090]]
cells = {(r, c): (cx[c], cy[r][c]) for r in range(4) for c in range(4)}
mask = {k: np.zeros_like(fg) for k in cells}
for i in range(1, N + 1):
    comp = (L == i) & fg
    if comp.sum() < 30: continue
    ys, xs = np.nonzero(comp)
    k = min(cells, key=lambda k: (cells[k][0] - xs.mean()) ** 2 + (cells[k][1] - ys.mean()) ** 2)
    mask[k] |= comp
# 左上から: (行, 列) -> 名前
NAMES = {(0, 0): 'raven_stage1', (0, 1): 'raven_stage2', (0, 2): 'piranha_stage1', (0, 3): 'piranha_stage2',
         (1, 0): 'leaffox_stage1', (1, 1): 'leaffox_stage2', (1, 2): 'dino_stage1', (1, 3): 'dino_stage2',
         (2, 0): 'wyvern_stage1', (2, 1): 'wyvern_stage2', (2, 2): 'lavawhale_stage1', (2, 3): 'lavawhale_stage2',
         (3, 0): 'cloudsheep_stage1', (3, 1): 'cloudsheep_stage2', (3, 2): 'mecha_stage1', (3, 3): 'mecha_stage2'}
sprites = {}
for k, nm in NAMES.items():
    ys, xs = np.nonzero(mask[k]); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    mm = ndi.binary_erosion(mask[k][y0:y1, x0:x1], iterations=1)
    al = ndi.gaussian_filter(mm.astype(float), .7)
    rgba = np.dstack([np.asarray(im)[y0:y1, x0:x1], (np.clip(al * 1.15, 0, 1) * 255).astype(np.uint8)])
    s = Image.fromarray(rgba, 'RGBA'); sc = 256 / max(s.size)
    sprites[nm] = s.resize((max(1, round(s.width * sc)), max(1, round(s.height * sc))), Image.LANCZOS)
# 棚詰め(幅1536)
W, GAP = 1536, 2
x = y = rowh = 0; place = {}
for nm, s in sprites.items():
    if x + s.width > W: x = 0; y += rowh + GAP; rowh = 0
    place[nm] = (x, y); x += s.width + GAP; rowh = max(rowh, s.height)
H = y + rowh
sheet = Image.new('RGBA', (W, H), (0, 0, 0, 0))
for nm, s in sprites.items(): sheet.alpha_composite(s, place[nm])
sheet.save(p('assets', 'atlas', 'monsters2.webp'), quality=88, alpha_quality=100, method=6)
rects = {nm: [place[nm][0], place[nm][1], s.width, s.height] for nm, s in sprites.items()}
aj = json.load(open(p('src', 'atlas.json'), encoding='utf8'))
aj['monsters2'] = {'f': 'atlas/monsters2.png', 'as': 'monsters', 'r': rects}
json.dump(aj, open(p('src', 'atlas.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('monsters2.webp', sheet.size, os.path.getsize(p('assets', 'atlas', 'monsters2.webp')) // 1024, 'KB', len(rects), 'sprites')
