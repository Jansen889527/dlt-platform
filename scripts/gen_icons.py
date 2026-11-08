# -*- coding: utf-8 -*-
# 大乐透图标生成：蓝底渐变（区分双色球红底）+ 红前蓝后双球（前区红球、后区蓝球）
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), '..')


def round_rect_gradient(size, light, dark, radius):
    w, h = size
    base = Image.new('RGBA', (w, h), dark)
    lighter = Image.new('RGBA', (w, h), light)
    mask = Image.new('L', (w, h), 0)
    px = mask.load()
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2.0
            px[x, y] = int(255 * (1 - t))
    base = Image.composite(lighter, base, mask)
    if radius > 0:
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        rmask = Image.new('L', (w, h), 0)
        ImageDraw.Draw(rmask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
        img = Image.composite(base, img, rmask)
        return img
    return base


def draw_ball(draw, cx, cy, rad, light, dark):
    for i in range(rad, 0, -1):
        t = i / rad
        c = tuple(int(light[k] * (1 - t) + dark[k] * t) for k in range(3)) + (255,)
        draw.ellipse([cx - i, cy - i, cx + i, cy + i], fill=c)
    draw.ellipse([cx - rad * 0.45, cy - rad * 0.52, cx - rad * 0.05, cy - rad * 0.05],
                 fill=(255, 255, 255, 110))


def make_icon(size, radius, maskable):
    # 蓝底渐变（大乐透主色），与双色球红底区分
    img = round_rect_gradient((size, size), (21, 101, 192), (13, 71, 161), radius)
    d = ImageDraw.Draw(img)
    rad = int(size * 0.165)
    gap = int(size * 0.085)
    cy = size // 2
    c1 = size // 2 - gap
    c2 = size // 2 + gap
    draw_ball(d, c1, cy, rad, (255, 122, 117), (183, 28, 28))   # 前区红球
    draw_ball(d, c2, cy, rad, (91, 155, 240), (13, 71, 161))    # 后区蓝球
    return img


# 普通图标（圆角 + 透明边，purpose any）
make_icon(192, 38, False).save(os.path.join(OUT, 'icon-192.png'))
make_icon(512, 100, False).save(os.path.join(OUT, 'icon-512.png'))
# 遮罩图标（满铺，purpose maskable）
make_icon(512, 0, True).save(os.path.join(OUT, 'icon-maskable-512.png'))
# iOS apple-touch-icon（正方形、无透明，iOS 自行圆角）
make_icon(180, 0, True).save(os.path.join(OUT, 'apple-touch-icon.png'))
print('icons generated:', [f for f in os.listdir(OUT) if f.endswith('.png')])
