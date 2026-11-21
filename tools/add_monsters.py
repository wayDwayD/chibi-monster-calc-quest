#!/usr/bin/env python3
"""ChatGPTで作った「マゼンタ背景のモンスターシート」を切り出して、アトラスに追加する。

シートの決まり(docs/CONTENT_GUIDE.md 参照):
  - 1254x1254 前後の正方形、背景はベタのマゼンタ(#FF00FF。端がやや暗くなっていてもOK)
  - 横4列x縦5行。各行は左から [進化前A, 進化後A, 進化前B, 進化後B]
  - キャラ自身にマゼンタ/ピンク系を使わない

使い方:
  python3 tools/add_monsters.py              # tools/sheets.json に書いた全シートを処理
  python3 tools/add_monsters.py --debug      # 切り出しの確認画像を /tmp に出す
tools/sheets.json: {"mon_sheet1.webp": ["hamster","frog",...10個のid...], ...}
  (assets/source/ に置いたシート画像と、行→列の順に並んだ monster id のリスト)
出力: assets/atlas/monsN.webp と src/atlas.json の "monsN"(as:"monsters")
必要: numpy / scipy / Pillow"""
import json, os, sys, colorsys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = lambda *a: os.path.join(ROOT, *a)
DEBUG = '--debug' in sys.argv
DROP = {'mon_sheet5.webp': [(759, 356)]}   # シートごとに、じゃまな飾り(切れ目でちぎれた星など)をふくむ塊を捨てる座標 (y, x)
SPR = 256          # スプライトの長辺(px)


def keyed_mask(a):
    """マゼンタ背景(色相 295-330°, 彩度高め, 明るさ中以上)を背景とみなす。"""
    f = a.astype(float) / 255
    mx, mn = f.max(2), f.min(2)
    d = mx - mn
    with np.errstate(divide='ignore', invalid='ignore'):
        h = np.where(mx == f[..., 0], ((f[..., 1] - f[..., 2]) / d) % 6,
            np.where(mx == f[..., 1], (f[..., 2] - f[..., 0]) / d + 2, (f[..., 0] - f[..., 1]) / d + 4)) * 60
        s = np.where(mx > 0, d / mx, 0)
    bg = (h >= 290) & (h <= 335) & (s >= .45) & (mx >= .45) & (f[..., 1] < .65 * np.minimum(f[..., 0], f[..., 2]))
    return bg


def process(sheet, ids, tag, single=False):
    im = Image.open(p('assets', 'source', sheet)).convert('RGB')
    a = np.asarray(im)
    bg = keyed_mask(a)
    bg = ndi.binary_opening(bg, iterations=1) | (bg & ndi.binary_erosion(bg, iterations=2))  # 孤立ノイズ除去
    fg = ~bg
    fg = ndi.binary_opening(fg, iterations=1)
    L, N = ndi.label(fg)
    for (yy, xx) in DROP.get(sheet, []):
        if L[yy, xx]: fg[L == L[yy, xx]] = False
    L, N = ndi.label(fg)
    areas = ndi.sum(fg, L, range(1, N + 1))
    objs = ndi.find_objects(L)
    cores, smalls = [], []
    for i in range(1, N + 1):
        ar = areas[i - 1]
        if ar < 60: continue                       # ごみ
        ys, xs = np.nonzero(L[objs[i - 1]] == i)
        ys = ys + objs[i - 1][0].start; xs = xs + objs[i - 1][1].start
        rec = dict(id=i, ys=ys, xs=xs, cy=ys.mean(), cx=xs.mean())
        (cores if ar >= 3000 else smalls).append(rec)
    rows = -(-len(ids) // 4) if single else len(ids) // 2   # 1行に4つ(なかまは 進化前/後 x2種類、敵は1体x4)

    def kmeans1d(v, k):                              # 1次元k-means(行・列の中心を求める)
        v = np.array(v); c = np.quantile(v, (np.arange(k) + .5) / k)
        for _ in range(50):
            g = np.abs(v[:, None] - c[None]).argmin(1)
            nc = np.array([v[g == j].mean() if (g == j).any() else c[j] for j in range(k)])
            if np.allclose(nc, c): break
            c = nc
        return np.sort(c)
    # 上下でつながってしまった大きな塊は、いちばんくびれた所で切る
    pitch = fg.shape[0] / rows
    again = True
    while again:
        again = False
        for c in list(cores):
            h = c['ys'].max() - c['ys'].min() + 1
            if h > 1.45 * pitch:
                y0 = c['ys'].min(); cnt = np.bincount(c['ys'] - y0, minlength=h)
                lo, hi = int(h * .3), int(h * .7)
                cut = y0 + lo + int(cnt[lo:hi].argmin())
                for part in (c['ys'] < cut, c['ys'] >= cut):
                    ys, xs = c['ys'][part], c['xs'][part]
                    cores.append(dict(id=-1, ys=ys, xs=xs, cy=ys.mean(), cx=xs.mean()))
                cores.remove(c); again = True
                if DEBUG: print('  split merged blob at y=', cut)
                break
    rcen = kmeans1d([c['cy'] for c in cores], rows)
    ccen = kmeans1d([c['cx'] for c in cores], 4)
    if DEBUG: print('  rcen', rcen.round(), 'ccen', ccen.round())
    cell = {}
    def assign(rec):
        return (int(np.abs(rcen - rec['cy']).argmin()), int(np.abs(ccen - rec['cx']).argmin()))
    for c in cores: c['cell'] = assign(c)
    if DEBUG: print('  cores', sorted((c['cell'], int(c['cy']), int(c['cx']), len(c['ys'])) for c in cores))
    for sm in smalls:                                # 小さな飾り(炎・星など)は一番近い本体に付ける
        best = None
        pts = np.stack([sm['ys'][::3], sm['xs'][::3]], 1)
        for c in cores:
            q = np.stack([c['ys'][::7], c['xs'][::7]], 1)
            dmin = ((pts[:, None, :] - q[None]) ** 2).sum(2).min()
            if best is None or dmin < best[0]: best = (dmin, c)
        sm['cell'] = best[1]['cell']; sm['d'] = best[0] ** .5
        if DEBUG and sm['d'] > 12: print('  small piece', sheet, int(sm['cy']), int(sm['cx']), 'area', len(sm['ys']), 'dist', round(sm['d']), '->', best[1]['cell'])
    masks = {}
    for rec in cores + smalls:
        m = masks.setdefault(rec['cell'], np.zeros(fg.shape, bool))
        m[rec['ys'], rec['xs']] = True
    missing = [(r, c) for r in range(rows) for c in range(4) if (r, c) not in masks]
    if missing: print(f'  !! {sheet}: 空のマス {missing}')
    ordered = [(None, None, None, masks.get((r, c))) for r in range(rows) for c in range(4)]
    sprites = {}
    for k, c in enumerate(ordered):
        if single:
            if k >= len(ids): break
            name = ids[k]
        else:
            pair, st = divmod(k, 2)
            if pair >= len(ids): break
            name = f'{ids[pair]}_stage{st + 1}'
        comp = c[3]
        if comp is None: continue
        ys, xs = np.nonzero(comp)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        m = comp[y0:y1, x0:x1]
        # 穴(あし元のすきま等)は背景のまま、輪郭のにじみを少しけずって柔らかいアルファに
        m2 = ndi.binary_erosion(m, iterations=1)
        al = ndi.gaussian_filter(m2.astype(float), .7)
        al = np.clip(al * 1.2, 0, 1)
        rgb = a[y0:y1, x0:x1].astype(float)
        # マゼンタのにじみ除去(縁のみ)
        edge = ndi.binary_dilation(~m2, iterations=3) & m
        spill = np.maximum(0, np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1])
        sp = np.where(edge, spill * .85, 0)
        rgb[..., 0] -= sp; rgb[..., 2] -= sp
        rgba = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), (al * 255).astype(np.uint8)])
        s = Image.fromarray(rgba, 'RGBA')
        sc = SPR / max(s.size)
        sprites[name] = s.resize((max(1, round(s.width * sc)), max(1, round(s.height * sc))), Image.LANCZOS)
    # 棚詰め(幅1536)
    W, GAP = 1536, 2
    x = y = rowh = 0; place = {}
    for nm, s in sprites.items():
        if x + s.width > W: x = 0; y += rowh + GAP; rowh = 0
        place[nm] = (x, y); x += s.width + GAP; rowh = max(rowh, s.height)
    H = y + rowh
    sheet_im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for nm, s in sprites.items(): sheet_im.alpha_composite(s, place[nm])
    out = p('assets', 'atlas', f'{tag}.webp')
    sheet_im.save(out, quality=86, alpha_quality=96, method=6)
    rects = {nm: [place[nm][0], place[nm][1], s.width, s.height] for nm, s in sprites.items()}
    if DEBUG:
        dbg = Image.new('RGB', (W, H), (60, 60, 70)); dbg.paste(sheet_im, (0, 0), sheet_im)
        dbg.save(f'/tmp/{tag}_debug.png')
    print(f'{tag}.webp', sheet_im.size, os.path.getsize(out) // 1024, 'KB', len(rects), 'sprites')
    return rects


def main():
    cfg = json.load(open(p('tools', 'sheets.json'), encoding='utf8'))
    aj = json.load(open(p('src', 'atlas.json'), encoding='utf8'))
    for n, (sheet, ids) in enumerate(cfg.items(), 1):
        if not os.path.exists(p('assets', 'source', sheet)):
            print('skip (no source):', sheet); continue
        if isinstance(ids, dict):                      # 敵などの単体シート: {"as":"enemies","tag":"enemies2","ids":[...]}
            tag = ids['tag']; rects = process(sheet, ids['ids'], tag, single=True); kind = ids['as']
        else:                                          # なかま(進化前/後)シート
            tag = f'mons{n}'; rects = process(sheet, ids, tag); kind = 'monsters'
        aj[tag] = {'f': f'atlas/{tag}.png', 'as': kind, 'r': rects}
    json.dump(aj, open(p('src', 'atlas.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    main()
