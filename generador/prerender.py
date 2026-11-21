#!/usr/bin/env python3
"""Genera una versión 100% estática (sin JavaScript necesario) de cada
artículo en noticia/<id>.html, a partir de la página interactiva
articulo.html?id=<id>. Así Google ve el contenido completo al instante,
sin tener que ejecutar JS, y cada artículo tiene su propia URL limpia
(sin query string) con <title>, meta description, Open Graph y JSON-LD
ya resueltos.

No sustituye a articulo.html (que sigue funcionando igual para quien
llega desde el feed o comparte el link antiguo); solo añade, para cada
id de articulos/*.json, una copia estática hermana en noticia/<id>.html
que es la que debe indexar Google (apunta a ella el sitemap y el
<link rel=canonical> de articulo.html).

Se ejecuta automáticamente cada día desde redes.py, así que no hace
falta acordarse de lanzarlo a mano.
"""
import os, sys, json, http.server, socketserver, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROD = "https://dhd16.github.io/dhdnews"

FIXUP_JS = """
({prodOrigin, prodPath}) => {
  const localOrigin = location.origin;
  const localSelf = location.origin + location.pathname + location.search;
  const prodSelf = prodOrigin + prodPath;

  const swap = v => {
    if (typeof v !== "string") return v;
    v = v.split(localSelf).join(prodSelf);
    v = v.split(encodeURIComponent(localSelf)).join(encodeURIComponent(prodSelf));
    v = v.split(localOrigin).join(prodOrigin);
    v = v.split(encodeURIComponent(localOrigin)).join(encodeURIComponent(prodOrigin));
    return v;
  };

  document.querySelectorAll("[href],[src],[content]").forEach(el => {
    for (const attr of ["href", "src", "content"]) {
      if (el.hasAttribute(attr)) el.setAttribute(attr, swap(el.getAttribute(attr)));
    }
  });
  const ld = document.getElementById("ldjson");
  if (ld) ld.textContent = swap(ld.textContent);

  // Rutas relativas (sin dominio): al vivir en noticia/<id>.html, un nivel
  // más abajo que articulo.html, necesitan un ../ extra para seguir
  // apuntando a fotos/, articulos/ y la portada.
  document.querySelectorAll("[href],[src]").forEach(el => {
    for (const attr of ["href", "src"]) {
      if (!el.hasAttribute(attr)) continue;
      const v = el.getAttribute(attr);
      if (!v || /^(https?:|data:|mailto:|#|\\/\\/)/.test(v)) continue;
      el.setAttribute(attr, v === "./" ? "../" : "../" + v);
    }
  });
  return document.documentElement.outerHTML;
}
"""

def run(port=8923):
    from playwright.sync_api import sync_playwright

    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    time.sleep(0.3)

    arts_dir = os.path.join(ROOT, "articulos")
    ids = [fn[:-5] for fn in sorted(os.listdir(arts_dir)) if fn.endswith(".json")]
    out_dir = os.path.join(ROOT, "noticia")
    os.makedirs(out_dir, exist_ok=True)

    done, failed = [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            for aid in ids:
                try:
                    url = f"http://127.0.0.1:{port}/articulo.html?id={aid}"
                    page.goto(url, wait_until="networkidle", timeout=20000)
                    page.wait_for_selector(".body", timeout=10000)
                    html = page.evaluate(FIXUP_JS, {"prodOrigin": PROD, "prodPath": f"/noticia/{aid}.html"})
                    # quita el <script> grande de fetch/render: ya no hace falta,
                    # el contenido ya está impreso en el HTML. Deja un script
                    # pequeño solo para el botón de copiar enlace.
                    start = html.find("<script>\nconst CATS")
                    if start == -1:
                        start = html.find("<script>\r\nconst CATS")
                    end = html.find("</script>", start) + len("</script>") if start != -1 else -1
                    if start != -1 and end != -1:
                        mini = (
                            "<script>document.getElementById('y').textContent=new Date().getFullYear();"
                            "var c=document.getElementById('copy');if(c)c.onclick=function(e){"
                            "navigator.clipboard.writeText(location.href).then(function(){e.target.textContent='✓ Enlace copiado';}).catch(function(){});};"
                            "</script>"
                        )
                        html = html[:start] + mini + html[end:]
                    with open(os.path.join(out_dir, f"{aid}.html"), "w", encoding="utf-8") as f:
                        f.write(html)
                    done.append(aid)
                except Exception as e:
                    failed.append((aid, str(e)))
            browser.close()
    finally:
        httpd.shutdown()

    return done, failed

if __name__ == "__main__":
    done, failed = run()
    print(f"OK {len(done)} páginas estáticas generadas en noticia/:", ", ".join(done))
    if failed:
        print("FALLOS:", failed)
        sys.exit(1)
