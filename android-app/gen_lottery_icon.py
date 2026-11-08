import math
from PIL import Image, ImageDraw

S = 1024  # 母图分辨率

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_col(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))

# ---- 背景：径向渐变（中心亮，边缘暗），让红蓝双球更突出 ----
center_col = (0x3A, 0x3F, 0x5C)
edge_col   = (0x16, 0x19, 0x28)
small = Image.new('RGB', (256, 256))
sp = small.load()
cx0, cy0 = 128.0, 128.0
maxr = 180.0
for y in range(256):
    for x in range(256):
        d = math.hypot(x - cx0, y - cy0) / maxr
        sp[x, y] = lerp_col(center_col, edge_col, min(1.0, d))
bg = small.resize((S, S), Image.LANCZOS).convert('RGBA')

# ---- 绘制一个高光立体球 ----
def draw_ball(img, cx, cy, R, base, high, edge):
    pix = img.load()
    hx, hy = cx - R * 0.40, cy - R * 0.40  # 高光点（左上）
    x0, x1 = int(cx - R), int(cx + R) + 1
    y0, y1 = int(cy - R), int(cy + R) + 1
    for y in range(max(0, y0), min(S, y1)):
        for x in range(max(0, x0), min(S, x1)):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= R * R:
                d = math.hypot(x - hx, y - hy) / (R * 1.25)
                t = min(1.0, d) ** 0.85
                col = lerp_col(high, edge, t)
                pix[x, y] = (col[0], col[1], col[2], 255)
    return img

R = int(S * 0.185)
# 左：红球
draw_ball(bg, S * 0.31, S * 0.50, R,
          base=(230, 0, 18), high=(255, 150, 140), edge=(110, 0, 8))
# 右：蓝球
draw_ball(bg, S * 0.69, S * 0.50, R,
          base=(0, 80, 179), high=(150, 200, 255), edge=(0, 28, 80))

# ---- 镜面高光 ----
overlay = Image.new('RGBA', (S, S), (0, 0, 0, 0))
od = ImageDraw.Draw(overlay)
for cxf in (0.31, 0.69):
    hx, hy = S * cxf - R * 0.40, S * 0.50 - R * 0.40
    od.ellipse([hx - R * 0.26, hy - R * 0.26, hx + R * 0.26, hy + R * 0.26],
               fill=(255, 255, 255, 95))
bg = Image.alpha_composite(bg, overlay)

BASE = '/Users/zhoumeiling/WorkBuddy/彩票工作台/android-app'
bg.save(f'{BASE}/generated-images/lottery_icon_base.png')
print('base saved', bg.size)

# ---- Android 各密度 ----
mip = {
    'mdpi':   (48, 108),
    'hdpi':   (72, 162),
    'xhdpi':  (96, 216),
    'xxhdpi': (144, 324),
    'xxxhdpi':(192, 432),
}
for d, (launcher, fg) in mip.items():
    p = bg.resize((launcher, launcher), Image.LANCZOS)
    p.save(f'{BASE}/android/app/src/main/res/mipmap-{d}/ic_launcher.png')
    p.save(f'{BASE}/android/app/src/main/res/mipmap-{d}/ic_launcher_round.png')
    f = bg.resize((fg, fg), Image.LANCZOS)
    f.save(f'{BASE}/android/app/src/main/res/mipmap-{d}/ic_launcher_foreground.png')

# ---- PWA 图标 ----
bg.resize((192, 192)).save(f'{BASE}/www/icon-192.png')
bg.resize((512, 512)).save(f'{BASE}/www/icon-512.png')
bg.resize((512, 512)).save(f'{BASE}/www/icon-maskable-512.png')
bg.resize((180, 180)).save(f'{BASE}/www/apple-touch-icon.png')

print('all icons generated')
