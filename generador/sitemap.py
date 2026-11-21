#!/usr/bin/env python3
"""Genera sitemap.xml a partir de todos los articulos/*.json del repo.
Se llama automáticamente desde redes.py cada vez que se genera el contenido
del día, así que no hace falta acordarse de ejecutarlo a mano.
"""
import os, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://dhd16.github.io/dhdnews/"

def build():
    arts_dir = os.path.join(ROOT, "articulos")
    urls = [("", datetime.date.today().isoformat(), "daily", "1.0")]
    if os.path.isdir(arts_dir):
        for fn in sorted(os.listdir(arts_dir)):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(arts_dir, fn)
            try:
                a = json.load(open(path, encoding="utf-8"))
            except Exception:
                continue
            aid = a.get("id") or fn[:-5]
            lastmod = a.get("date") or datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
            urls.append((f"noticia/{aid}.html", lastmod, "monthly", "0.7"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, changefreq, priority in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{BASE}{loc}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <changefreq>{changefreq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    out = os.path.join(ROOT, "sitemap.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return out, len(urls)

if __name__ == "__main__":
    out, n = build()
    print("OK", out, f"({n} urls)")
