#!/usr/bin/env python3
"""DHDnews · Generador de contenido para redes.
Lee news.json y crea en contenido/AAAA-MM-DD/:
  story-1.png, story-2.png  (1080x1920, Instagram/TikTok stories)
  reel.mp4                  (1080x1920, ~25 s, sin música: se añade el audio en la app)
Uso: python3 generador/redes.py [ruta_news.json] [fecha AAAA-MM-DD]
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
    d.text((x+s+24*scale, bb[3]+int(10*scale)), "NEWSFLYS · AL VUELO", font=font("bold", int(18*scale)), fill=(170, 170, 190))

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
    logo(img, 80, 230)
    d.text((80, 400), titulo, font=font("anton", 150), fill="white")
    d.text((84, 575), fecha_txt(fecha).upper(), font=font("bold", 34), fill=CYAN)
    y = 680
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

# ---------- REEL ----------
def slide_intro(fecha):
    img = background(PINK); d = ImageDraw.Draw(img, "RGBA")
    logo(img, 80, 300)
    d.text((80, 620), "LAS 5", font=font("anton", 230), fill="white")
    d.text((80, 860), "NOTICIAS", font=font("anton", 230), fill=PINK)
    d.text((80, 1100), "DE HOY", font=font("anton", 230), fill="white")
    d.text((86, 1370), fecha_txt(fecha).upper(), font=font("black", 44), fill=CYAN)
    d.text((86, 1440), "Música · Gaming · Streamers · Deportes · Tele", font=font("semi", 32), fill=(200, 200, 215))
    return img

def slide_news(n, rank):
    lab, col = CATS.get(n["cat"], ("NOTICIA", PINK))
    img = background(col); d = ImageDraw.Draw(img, "RGBA")
    logo(img, 80, 230, .8)
    d.text((W-80-d.textlength(str(rank), font=font("anton", 300)), 180), str(rank), font=font("anton", 300), fill=(255, 255, 255, 40))
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
    logo(img, 80, 520, 1.4)
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
    fecha = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else datetime.date.today()
    news = json.load(open(src))
    out = os.path.join(ROOT, "contenido", fecha.isoformat()); os.makedirs(out, exist_ok=True)
    story_lista(news, fecha, 0, "TOP 10 HOY", "DESLIZA PARA EL 6–10 →").save(os.path.join(out, "story-1.png"))
    story_lista(news, fecha, 5, "DEL 6 AL 10", "LINK EN BIO · dhd16.github.io/dhdnews").save(os.path.join(out, "story-2.png"))
    slides = [(slide_intro(fecha), 2.5)] + [(slide_news(n, i+1), 4.0) for i, n in enumerate(news[:5])] + [(slide_outro(), 3.0)]
    make_reel(slides, os.path.join(out, "reel.mp4"))
    print("OK", out)

if __name__ == "__main__":
    main()
