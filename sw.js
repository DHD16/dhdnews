/* DHDNEWS · Dailynews — service worker
   - Páginas y JSON (news.json, articulos/*.json): primero red, y si no hay conexión, la última copia guardada.
   - Fotos, iconos y fuentes: primero caché (cambian poco).
   - Sin conexión y sin copia: offline.html. */
const VERSION = "dhd-v1";
const CORE = ["./", "index.html", "articulo.html", "offline.html", "manifest.webmanifest",
              "icons/icon-192.png", "icons/icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const isFresh = req => req.mode === "navigate" || /\.(html|json)$/.test(new URL(req.url).pathname)
                    || new URL(req.url).pathname.endsWith("/");

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const sameOrigin = url.origin === location.origin;
  const isFont = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (!sameOrigin && !isFont) return;           // enlaces a otras webs: sin tocar

  if (sameOrigin && isFresh(req)) {
    // Red primero; guardamos una copia sin el ?t= para usarla sin conexión
    e.respondWith(fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(url.pathname, copy)); }
      return res;
    }).catch(async () => {
      const c = await caches.open(VERSION);
      return (await c.match(url.pathname)) || (await c.match(req, {ignoreSearch: true}))
          || (req.mode === "navigate" ? c.match("offline.html") : Response.error());
    }));
    return;
  }

  // Caché primero para estáticos
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok || res.type === "opaque") { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
    return res;
  })));
});
