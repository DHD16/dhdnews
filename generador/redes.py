#!/usr/bin/env python3
"""DHDNEWS · Dailynews · Generador de contenido para redes.
Lee news.json y crea en contenido/AAAA-MM-DD/:
  story-top5.png                     (story con el top 5)
  story-ultima-1.png, story-ultima-2.png  (formato ÚLTIMAS NOTICIAS, noticias 1 y 2)
  reel.mp4 (solo con --reel)
Uso: python3 generador/redes.py [ruta_news.json] [fecha AAAA-MM-DD | -] [--reel]
"""
import json, os, sys, math, subprocess, shutil, tempfile, datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "generador", "fonts")
W, H = 1080, 1920
BG = (11, 11, 16)
PINK, VIOLET, CYAN = (255, 46, 99), (124, 58, 237), (8, 217, 214)
CATS = {
    "musica":   ("MÚSICA",     (255, 46, 99)),
    "gaming":   ("GAMING",     (139, 92, 246)),
    "youtube":  ("STREAMERS",  (255, 77, 77)),
    "deportes": ("DEPORTES",   (34, 197, 94)),
    "tele":     ("TELEVISIÓN", (59, 130, 246)),
    "gossip":   ("GOSSIP",     (245, 158, 11)),
}
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
DIAS = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]

def font(name, size):
    paths = {"anton": os.path.join(FONTS, "Anton-Regular.woff"),
             "black": "/usr/share/fonts/opentype/inter/Inter-Black.otf",
             "bold": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
             "semi": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"}
    return ImageFont.truetype(paths[name], size)

def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def fit(draw, text, name, maxw, start, minsize=60):
    s = start
    while s > minsize and draw.textlength(text, font=font(name, s)) > maxw: s -= 4
    return font(name, s)

def background(color):
    img = Image.new("RGB", (W, H), BG)
    glow = Image.new("RGB", (W, H), BG)
    g = ImageDraw.Draw(glow)
    g.ellipse((W*0.25, -H*0.25, W*1.6, H*0.55), fill=color)
    g.ellipse((-W*0.7, H*0.65, W*0.55, H*1.35), fill=tuple(int(c*0.55) for c in VIOLET))
    glow = glow.filter(ImageFilter.GaussianBlur(260))
    img = Image.blend(img, glow, 0.85)
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(-H, W, 46):  # rayas diagonales sutiles
        d.line([(x, H), (x + H, 0)], fill=(255, 255, 255, 9), width=3)
    return img

def logo(img, x, y, scale=1.0):
    d = ImageDraw.Draw(img, "RGBA")
    s = int(92*scale)
    grad = Image.new("RGB", (s, s))
    gd = ImageDraw.Draw(grad)
    for i in range(s):
        t = i/s
        gd.line([(0, i), (s, i)], fill=tuple(int(PINK[k]*(1-t)+VIOLET[k]*t) for k in range(3)))
    mask = Image.new("L", (s, s), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, s-1, s-1), radius=int(s*.27), fill=255)
    img.paste(grad, (x, y), mask)
    u = s/48
    d.polygon([(x+13*u, y+12*u), (x+23.5*u, y+12*u), (x+31*u, y+14*u), (x+36*u, y+19*u), (x+37*u, y+24*u), (x+36*u, y+29*u), (x+31*u, y+34*u), (x+23.5*u, y+36*u), (x+13*u, y+36*u)], fill="white")
    d.rounded_rectangle((x+19*u, y+18*u, x+29*u, y+30*u), radius=int(5*u), fill=tuple(int(PINK[k]*.5+VIOLET[k]*.5) for k in range(3)))
    d.ellipse((x+34.5*u, y+5.5*u, x+43.5*u, y+14.5*u), fill=CYAN, outline=BG, width=max(2, int(2.5*u)))
    f1 = font("anton", int(70*scale))
    d.text((x+s+22*scale, y+int(4*scale)), "DHD", font=f1, fill="white")
    dx = d.textlength("DHD", font=f1)
    d.text((x+s+22*scale+dx+2, y+int(4*scale)), "news", font=f1, fill=PINK)
    bb = d.textbbox((x+s+22*scale, y+int(4*scale)), "DHD", font=f1)
    d.text((x+s+24*scale, bb[3]+int(10*scale)), "DAILYNEWS", font=font("black", int(24*scale)), fill=(225, 225, 235))

def logo_c(img, y, scale=1.0):
    layer = Image.new("RGBA", (W*2, int(300*scale)), (0, 0, 0, 0))
    logo(layer, 0, 0, scale)
    bb = layer.getbbox()
    layer = layer.crop(bb)
    x = (W - layer.width)//2
    # halo detrás del logo para que destaque
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).rounded_rectangle((x-40, y-30, x+layer.width+40, y+layer.height+30), radius=60, fill=(11, 11, 16, 150))
    img.paste(Image.alpha_composite(img.convert("RGBA"), halo).convert("RGB"))
    img.paste(layer, (x, y), layer)
    return y + layer.height

def chip(d, x, y, label, color, size=30):
    f = font("black", size)
    w = d.textlength(label, font=f)
    d.rounded_rectangle((x, y, x+w+48, y+size+28), radius=999, fill=color)
    d.text((x+24, y+12), label, font=f, fill=BG)
    return w+48

def fecha_txt(fecha):
    return f"{DIAS[fecha.weekday()]} {fecha.day} de {MESES[fecha.month-1]}"

# ---------- STORIES ----------
def story_lista(news, fecha, desde, titulo, cta):
    img = background(PINK if desde == 0 else VIOLET)
    d = ImageDraw.Draw(img, "RGBA")
    logo_c(img, 210, 1.55); d = ImageDraw.Draw(img, "RGBA")
    ft = font("anton", 120)
    d.text(((W-d.textlength(titulo, font=ft))/2, 430), titulo, font=ft, fill="white")
    fd = font("black", 32); ftxt = fecha_txt(fecha).upper()
    d.text(((W-d.textlength(ftxt, font=fd))/2, 585), ftxt, font=fd, fill=CYAN)
    y = 670
    for i, n in enumerate(news[desde:desde+5], start=desde+1):
        lab, col = CATS.get(n["cat"], ("NOTICIA", PINK))
        d.rounded_rectangle((70, y, W-70, y+190), radius=34, fill=(20, 20, 28, 225), outline=(255, 255, 255, 30), width=2)
        d.rounded_rectangle((70, y, 82, y+190), radius=6, fill=col)
        d.text((108, y+28), str(i), font=font("anton", 110), fill=col)
        tx = 108 + 120
        d.text((tx, y+30), lab, font=font("black", 24), fill=col)
        kw = n.get("kw") or n["title"].split(":")[0]
        d.text((tx, y+60), kw.upper(), font=fit(d, kw.upper(), "anton", W-70-tx-30, 64, 40), fill="white")
        sub = wrap(d, n["title"], font("semi", 27), W-70-tx-30)[:1]
        if sub: d.text((tx, y+138), sub[0] + ("…" if len(wrap(d, n["title"], font("semi", 27), W-70-tx-30)) > 1 else ""), font=font("semi", 27), fill=(200, 200, 215))
        y += 212
    f = font("black", 34)
    w = d.textlength(cta, font=f)
    d.rounded_rectangle(((W-w)/2-40, 1760-10, (W+w)/2+40, 1760+62), radius=999, fill="white")
    d.text(((W-w)/2, 1760+4), cta, font=f, fill=BG)
    return img


# ---------- LOGO RÓTULO DE TV ----------
def bug(img, cx, y, scale=1.0, center=True):
    """Dibuja el logo DHD|NEWS + barra LIVE DAILYNEWS, inclinado como un rótulo de TV."""
    fa = font("anton", int(96*scale)); fb = font("black", int(26*scale)); fl = font("black", int(22*scale))
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    pad = int(30*scale)
    w1 = tmp.textlength("DHD", font=fa) + 2*pad; w2 = tmp.textlength("NEWS", font=fa) + 2*pad
    h1 = int(118*scale); h2 = int(48*scale)
    Wl, Hl = int(w1+w2), h1+h2
    layer = Image.new("RGBA", (Wl+int(60*scale), Hl), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle((0, 0, w1, h1), fill=PINK); d.text((pad, int(8*scale)), "DHD", font=fa, fill="white")
    d.rectangle((w1, 0, w1+w2, h1), fill="white"); d.text((w1+pad, int(8*scale)), "NEWS", font=fa, fill=BG)
    d.rectangle((0, h1, Wl, Hl), fill=CYAN)
    lw = tmp.textlength("LIVE", font=fl) + int(44*scale)
    d.rectangle((pad*0.6, h1+int(8*scale), pad*0.6+lw, Hl-int(8*scale)), fill=BG)
    d.ellipse((pad*0.6+int(10*scale), h1+int(19*scale), pad*0.6+int(22*scale), h1+int(31*scale)), fill=PINK)
    d.text((pad*0.6+int(28*scale), h1+int(11*scale)), "LIVE", font=fl, fill="white")
    d.text((pad*0.6+lw+int(16*scale), h1+int(9*scale)), "D A I L Y N E W S", font=fb, fill=BG)
    k = 0.14  # inclinación
    layer = layer.transform(layer.size, Image.AFFINE, (1, k, -k*Hl, 0, 1, 0), resample=Image.BICUBIC)
    x = int(cx - layer.width/2) if center else int(cx)
    img.paste(layer, (x, y), layer)
    return y + Hl


def link_icon(size, color):
    L = Image.new("RGBA", (size*2, size*2), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    w = max(4, size//7); r = size//2
    d.rounded_rectangle((size*0.25, size*0.75, size*1.15, size*1.25), radius=r//2, outline=color, width=w)
    d.rounded_rectangle((size*0.85, size*0.75, size*1.75, size*1.25), radius=r//2, outline=color, width=w)
    return L.rotate(-45, resample=Image.BICUBIC).resize((size, size), Image.LANCZOS)

def cta_sticker(img, cy, title="LINK EN BIO", sub="dhd16.github.io/dhdnews", angle=-3):
    ft, fs = font("anton", 64), font("black", 26)
    d0 = ImageDraw.Draw(Image.new("RGB", (5, 5)))
    tw = max(d0.textlength(title, font=ft), d0.textlength(sub, font=fs))
    ic = 96; pad = 30
    w, h = int(ic + tw + pad*3 + 70), 160
    lay = Image.new("RGBA", (w+80, h+80), (0, 0, 0, 0))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 52, 40+w, 52+h), radius=h//2, fill=(0, 0, 0, 150))
    lay = Image.alpha_composite(lay, sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(lay)
    # cuerpo blanco con borde degradado
    grad = Image.new("RGBA", (w+12, h+12)); gd = ImageDraw.Draw(grad)
    for x in range(w+12):
        t = x/(w+12); gd.line([(x, 0), (x, h+12)], fill=tuple(int(PINK[k]*(1-t)+CYAN[k]*t) for k in range(3))+(255,))
    m = Image.new("L", grad.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w+11, h+11), radius=(h+12)//2, fill=255)
    lay.paste(grad, (34, 34), m)
    d.rounded_rectangle((40, 40, 40+w, 40+h), radius=h//2, fill="white")
    # icono en círculo rosa
    cx0 = 40+pad-6; d.ellipse((cx0, 40+(h-ic)//2, cx0+ic, 40+(h+ic)//2), fill=PINK)
    li = link_icon(60, "white"); lay.paste(li, (cx0+18, 40+(h-60)//2), li)
    tx = cx0+ic+pad
    d.text((tx, 40+10), title, font=ft, fill=BG)
    d.text((tx+2, 40+104), sub, font=fs, fill=(120, 120, 140))
    # flecha
    ax = 40+w-pad-34; ay = 40+h//2
    d.line([(ax-20, ay+20), (ax+14, ay-14)], fill=PINK, width=9)
    d.line([(ax-6, ay-16), (ax+16, ay-16)], fill=PINK, width=9); d.line([(ax+16, ay-16), (ax+16, ay+6)], fill=PINK, width=9)
    lay = lay.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.paste(lay, (int(W/2 - lay.width/2), int(cy - lay.height/2)), lay)

def story_top5(news, fecha):
    img = background(PINK); d = ImageDraw.Draw(img, "RGBA")
    bug(img, W/2, 200, 1.0)
    ft = font("anton", 130); t = "TOP 5 DE HOY"
    d.text(((W-d.textlength(t, font=ft))/2, 420), t, font=ft, fill="white")
    fd = font("black", 32); ftxt = fecha_txt(fecha).upper()
    d.text(((W-d.textlength(ftxt, font=fd))/2, 585), ftxt, font=fd, fill=CYAN)
    y = 650
    for i, n in enumerate(news[:5], start=1):
        lab, col = CATS.get(n["cat"], ("NOTICIA", PINK))
        d.rounded_rectangle((70, y, W-70, y+180), radius=34, fill=(20, 20, 28, 225), outline=(255, 255, 255, 30), width=2)
        d.rounded_rectangle((70, y, 82, y+180), radius=6, fill=col)
        d.text((108, y+24), str(i), font=font("anton", 106), fill=col)
        tx = 108 + 120
        d.text((tx, y+24), lab, font=font("black", 24), fill=col)
        kw = (n.get("kw") or n["title"].split(":")[0]).upper()
        d.text((tx, y+52), kw, font=fit(d, kw, "anton", W-70-tx-30, 64, 40), fill="white")
        sub = wrap(d, n["title"], font("semi", 27), W-70-tx-30)
        if sub: d.text((tx, y+128), sub[0] + ("…" if len(sub) > 1 else ""), font=font("semi", 27), fill=(200, 200, 215))
        y += 194
    cta_sticker(img, 1735, "TOP 10 COMPLETO", "link en bio · dhd16.github.io/dhdnews")
    return img

def story_ultima(n, fecha):
    lab, col = CATS.get(n["cat"], ("NOTICIA", PINK))
    img = background(col); d = ImageDraw.Draw(img, "RGBA")
    bug(img, W/2, 190, 0.9)
    # rótulo ÚLTIMA HORA
    y = 470
    fu = font("anton", 80); tu = "ÚLTIMAS NOTICIAS"
    wu = d.textlength(tu, font=fu)
    d.rectangle((0, y, wu+160, y+128), fill=PINK)
    d.text((80, y+8), tu, font=fu, fill="white")
    d.rectangle((wu+160, y, W, y+128), fill=(255, 255, 255, 235))
    fh = font("black", 34); hora = fecha_txt(fecha).upper()
    d.text((wu+190, y+44), lab, font=fh, fill=col if col != (255, 255, 255) else BG)
    y += 180
    kw = (n.get("kw") or n["title"].split(":")[0]).upper()
    fk = fit(d, kw, "anton", W-160, 200, 90)
    for l in wrap(d, kw, fk, W-160)[:2]:
        d.text((80, y), l, font=fk, fill="white"); y += int(fk.size*1.02)
    y += 50
    for l in wrap(d, n["title"], font("black", 54), W-160)[:3]:
        d.text((80, y), l, font=font("black", 54), fill="white"); y += 68
    y += 24
    tl = wrap(d, n.get("text", ""), font("semi", 38), W-160)
    if len(tl) > 5: tl = tl[:5]; tl[-1] = tl[-1].rstrip(",.;") + "…"
    for l in tl:
        d.text((80, y), l, font=font("semi", 38), fill=(215, 215, 228)); y += 52
    d.text((80, 1660), "Fuente: " + n.get("source", "") + "  ·  " + hora.lower(), font=font("semi", 28), fill=(160, 160, 180))
    f = font("black", 34); cta = "MÁS INFO · LINK EN BIO"
    w = d.textlength(cta, font=f)
    d.rounded_rectangle(((W-w)/2-40, 1750, (W+w)/2+40, 1822), radius=999, fill="white")
    d.text(((W-w)/2, 1764), cta, font=f, fill=BG)
    return img


def photo_for(news, idx):
    n = news[idx]
    k = sum(1 for m in news[:idx] if m["cat"] == n["cat"])
    folder = os.path.join(ROOT, "fotos", n["cat"])
    files = sorted(f for f in os.listdir(folder) if f.endswith(".jpg")) if os.path.isdir(folder) else []
    return os.path.join(folder, files[k % len(files)]) if files else None

def cover(im, w, h):
    r = max(w/im.width, h/im.height)
    im = im.resize((int(im.width*r)+1, int(im.height*r)+1), Image.LANCZOS)
    l, t = (im.width-w)//2, (im.height-h)//2
    return im.crop((l, t, l+w, t+h))

def mini_bug(img, x, y, size=34):
    f = font("anton", size); d0 = ImageDraw.Draw(Image.new("RGB", (5, 5)))
    p = int(size*0.32); w1 = d0.textlength("DHD", font=f)+2*p; w2 = d0.textlength("NEWS", font=f)+2*p; h = int(size*1.25)
    lay = Image.new("RGBA", (int(w1+w2)+20, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rectangle((0, 0, w1, h), fill=PINK); d.text((p, int(size*0.08)), "DHD", font=f, fill="white")
    d.rectangle((w1, 0, w1+w2, h), fill="white"); d.text((w1+p, int(size*0.08)), "NEWS", font=f, fill=BG)
    lay = lay.transform(lay.size, Image.AFFINE, (1, 0.14, -0.14*h, 0, 1, 0), resample=Image.BICUBIC)
    img.paste(lay, (int(x - lay.width), y), lay)

def story_card(news, idx, fecha):
    n = news[idx]; lab, col = CATS.get(n["cat"], ("NOTICIA", PINK))
    img = Image.new("RGB", (W, H), BG)
    glow = Image.new("RGB", (W, H), BG); ImageDraw.Draw(glow).ellipse((W*0.3, -H*0.2, W*1.5, H*0.35), fill=col)
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(240)), 0.55)
    d = ImageDraw.Draw(img, "RGBA")
    bug(img, W/2, 110, 0.8)
    fh = font("anton", 78); t = "ÚLTIMAS NOTICIAS"
    d.text((60, 325), t, font=fh, fill="white")
    tw = d.textlength(t, font=fh); d.rectangle((60+tw+24, 372, W-60, 376), fill=(255, 255, 255, 70))
    X0, X1, Y0, PH, Y1 = 50, W-50, 450, 540, 1590
    CW = X1-X0
    d.rounded_rectangle((X0, Y0, X1, Y1), radius=44, fill=(22, 22, 31), outline=(255, 255, 255, 28), width=2)
    # foto
    ph = photo_for(news, idx)
    pic = cover(Image.open(ph).convert("RGB"), CW, PH) if ph else Image.new("RGB", (CW, PH), col)
    tint = Image.new("RGBA", (CW, PH), (0, 0, 0, 0)); td = ImageDraw.Draw(tint)
    for yy in range(PH):
        a = int(235 * max(0, (yy - PH*0.35) / (PH*0.65)) ** 1.3)
        td.line([(0, yy), (CW, yy)], fill=(11, 11, 16, a))
    diag = Image.new("RGBA", (CW, PH), col + (0,)); dd = ImageDraw.Draw(diag)
    for xx in range(CW):
        dd.line([(xx, 0), (xx, PH)], fill=col + (int(120*max(0, 1 - xx/(CW*0.6))),))
    pic = Image.alpha_composite(Image.alpha_composite(pic.convert("RGBA"), diag), tint)
    mask = Image.new("L", (CW, PH), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, CW, PH+60), radius=44, fill=255)
    img.paste(pic.convert("RGB"), (X0, Y0), mask)
    d = ImageDraw.Draw(img, "RGBA")
    # chip arriba
    fc = font("black", 30); cw = d.textlength(lab, font=fc)
    d.rounded_rectangle((X0+30, Y0+30, X0+30+cw+92, Y0+30+66), radius=999, fill=(11, 11, 16, 190), outline=(255, 255, 255, 50), width=2)
    d.ellipse((X0+42, Y0+42, X0+84, Y0+84), fill=col)
    d.text((X0+100, Y0+45), lab, font=fc, fill="white")
    # palabra clave + sello + barra
    kw = (n.get("kw") or n["title"].split(":")[0]).upper()
    fk = fit(d, kw, "anton", CW-60-230, 170, 80)
    d.text((X0+34, Y0+PH-30-fk.size*1.05), kw, font=fk, fill="white")
    mini_bug(img, X1-28, Y0+PH-80, 40)
    d.rectangle((X0, Y0+PH-10, X1, Y0+PH), fill=col)
    # cuerpo
    y = Y0+PH+40
    fl = font("black", 30); lw = d.textlength(lab, font=fl)
    d.rounded_rectangle((X0+40, y, X0+40+lw+48, y+60), radius=14, fill=col)
    d.text((X0+64, y+12), lab, font=fl, fill=BG if n["cat"] in ("tele", "gossip", "deportes") else "white")
    y += 96
    ft = font("black", 60)
    for l in wrap(d, n["title"], ft, CW-80)[:3]:
        d.text((X0+40, y), l, font=ft, fill="white"); y += 74
    y += 18
    fx = font("semi", 38); tl = wrap(d, n.get("text", ""), fx, CW-80)
    maxl = max(0, min(6, (Y1-130-y)//54))
    if len(tl) > maxl:
        tl = tl[:maxl]
        if tl: tl[-1] = tl[-1].rstrip(",.;") + "…"
    for l in tl:
        d.text((X0+40, y), l, font=fx, fill=(170, 170, 190)); y += 54
    d.line([(X0+40, Y1-110), (X1-40, Y1-110)], fill=(255, 255, 255, 40), width=2)
    d.text((X0+40, Y1-80), n.get("source", ""), font=font("semi", 32), fill=(160, 160, 180))
    go = "Leer noticia →"; fg = font("black", 32)
    d.text((X1-40-d.textlength(go, font=fg), Y1-80), go, font=fg, fill=CYAN)
    cta_sticker(img, 1700, "LEE LA NOTICIA", "link en bio · dhd16.github.io/dhdnews")
    return img

# ---------- REEL ----------
def slide_intro(fecha):
    img = background(PINK); d = ImageDraw.Draw(img, "RGBA")
    logo_c(img, 280, 1.7); d = ImageDraw.Draw(img, "RGBA")
    d.text((80, 620), "LAS 5", font=font("anton", 230), fill="white")
    d.text((80, 860), "NOTICIAS", font=font("anton", 230), fill=PINK)
    d.text((80, 1100), "DE HOY", font=font("anton", 230), fill="white")
    d.text((86, 1400), fecha_txt(fecha).upper(), font=font("black", 44), fill=CYAN)
    d.text((86, 1470), "Música · Gaming · Streamers · Deportes · Tele", font=font("semi", 32), fill=(200, 200, 215))
    return img

def slide_news(n, rank):
    lab, col = CATS.get(n["cat"], ("NOTICIA", PINK))
    img = background(col); d = ImageDraw.Draw(img, "RGBA")
    d.text((W-80-d.textlength(str(rank), font=font("anton", 300)), 330), str(rank), font=font("anton", 300), fill=(255, 255, 255, 40))
    logo_c(img, 200, 1.3); d = ImageDraw.Draw(img, "RGBA")
    chip(d, 80, 560, lab, col, 34)
    kw = (n.get("kw") or n["title"].split(":")[0]).upper()
    fk = fit(d, kw, "anton", W-160, 210, 90)
    lines = wrap(d, kw, fk, W-160)[:2]
    y = 660
    for l in lines:
        d.text((80, y), l, font=fk, fill="white"); y += int(fk.size*1.02)
    y += 70
    for l in wrap(d, n["title"], font("black", 52), W-160)[:3]:
        d.text((80, y), l, font=font("black", 52), fill="white"); y += 66
    y += 20
    tl = wrap(d, n.get("text", ""), font("semi", 36), W-160)
    if len(tl) > 5: tl = tl[:5]; tl[-1] = tl[-1].rstrip(",.;") + "…"
    for l in tl:
        d.text((80, y), l, font=font("semi", 36), fill=(205, 205, 220)); y += 50
    d.text((80, 1690), "Fuente: " + n.get("source", ""), font=font("semi", 28), fill=(150, 150, 170))
    return img

def slide_outro():
    img = background(VIOLET); d = ImageDraw.Draw(img, "RGBA")
    logo_c(img, 480, 2.0); d = ImageDraw.Draw(img, "RGBA")
    d.text((80, 820), "TODAS LAS", font=font("anton", 150), fill="white")
    d.text((80, 980), "NOTICIAS EN", font=font("anton", 150), fill="white")
    d.text((80, 1140), "LA WEB", font=font("anton", 150), fill=PINK)
    f = font("black", 40); t = "LINK EN BIO  →  dhd16.github.io/dhdnews"
    d.rounded_rectangle((80, 1360, 80+d.textlength(t, font=f)+60, 1440), radius=999, fill="white")
    d.text((110, 1376), t, font=f, fill=BG)
    d.text((80, 1500), "Síguenos para el resumen diario 🔔".replace(" 🔔", ""), font=font("semi", 36), fill=(205, 205, 220))
    return img

def make_reel(slides_durs, out):
    tmp = tempfile.mkdtemp()
    clips = []
    for i, (img, dur) in enumerate(slides_durs):
        p = os.path.join(tmp, f"s{i}.png"); img.save(p)
        c = os.path.join(tmp, f"c{i}.mp4"); fr = int(dur*30)
        vf = (f"scale=1188:2112,zoompan=z='min(zoom+0.0009,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={fr}:s={W}x{H}:fps=30,"
              f"fade=t=in:st=0:d=0.25,fade=t=out:st={dur-0.25}:d=0.25,format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", p, "-vf", vf, "-t", str(dur),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", c], check=True)
        clips.append(c)
    lst = os.path.join(tmp, "l.txt")
    open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "news.json")
    fecha = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else datetime.date.today()
    reel = "--reel" in sys.argv
    news = json.load(open(src))
    out = os.path.join(ROOT, "contenido", fecha.isoformat()); os.makedirs(out, exist_ok=True)
    story_top5(news, fecha).save(os.path.join(out, "story-top5.png"))
    story_card(news, 0, fecha).save(os.path.join(out, "story-ultima-1.png"))
    story_card(news, 1, fecha).save(os.path.join(out, "story-ultima-2.png"))
    if reel:
        slides = [(slide_intro(fecha), 2.5)] + [(slide_news(n, i+1), 4.0) for i, n in enumerate(news[:5])] + [(slide_outro(), 3.0)]
        make_reel(slides, os.path.join(out, "reel.mp4"))
    print("OK", out)

if __name__ == "__main__":
    main()
