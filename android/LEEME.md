# DHDNEWS · Dailynews en Google Play

La web ya es una PWA (manifest.webmanifest, sw.js, iconos, offline.html). Aquí está todo lo necesario para subirla a Play como app (Trusted Web Activity).

## Archivos listos

- `play-store/icono-play-512.png`: icono de la app (512x512).
- `play-store/grafico-destacado-1024x500.png`: gráfico destacado.
- `play-store/captura-1-portada.png`, `captura-2-articulo.png`, `captura-3-top10.png`: capturas de teléfono (1080x1920).
- `well-known-para-repo-dhd16.github.io/.well-known/assetlinks.json`: plantilla para quitar la barra de dirección de la app.
- Páginas públicas: https://dhd16.github.io/dhdnews/privacidad.html y https://dhd16.github.io/dhdnews/sobre.html

## Datos para PWABuilder (pwabuilder.com → Package for stores → Android → Google Play)

- URL: `https://dhd16.github.io/dhdnews/`
- Package ID: `com.dhdrecords.dhdnews`
- App name: `DHDNEWS · Dailynews` · Launcher name: `DHDNEWS`
- Version code: `1` · Version name: `1.0.0`
- Host: `dhd16.github.io` · Start URL: `/dhdnews/?source=pwa`
- Theme / background / nav bar color: `#0b0b10`
- Signing key: "Create new". GUARDA el zip que descargas (signing.keystore y signing-key-info.txt): sin él no podrás actualizar la app.

## Textos de la ficha de Play Store

**Nombre (máx. 30):** DHDNEWS · Dailynews

**Descripción breve (máx. 80):** Las noticias del día en 60 segundos: música, gaming, streamers, deportes y tele

**Descripción completa:**

DHDNEWS · Dailynews te cuenta cada mañana las 10 noticias que importan, en un minuto.

🎤 Música: lanzamientos, giras, premios y listas, de España y del mundo latino.
🎮 Gaming: estrenos, novedades de PlayStation, Xbox, Nintendo y los juegos más esperados.
🔴 Streamers y youtubers: lo último de los creadores que más se ven.
⚽ Deportes: LaLiga, Premier y Champions, con resultados, horarios y dónde verlo.
📺 Televisión: estrenos, audiencias y novedades de la parrilla.
⭐ Famosos: solo hechos confirmados, sin rumores.

Cada noticia incluye un resumen propio y el enlace a su fuente original, para que puedas ampliar la información.

• Top 10 nuevo todos los días.
• Artículos propios de DHDNEWS.
• Filtra por categoría.
• Funciona sin conexión con las noticias que ya has abierto.
• Sin registro, sin anuncios y sin recoger tus datos.

Síguenos en Instagram y TikTok: @dhdrecords

## Respuestas para Play Console

- **Categoría:** Noticias y revistas. **Etiquetas:** Noticias, Entretenimiento.
- **Anuncios:** No contiene anuncios.
- **Acceso a la app:** Toda la funcionalidad está disponible sin restricciones.
- **Público objetivo:** 16-17 y 18 o más (así evitas la política de Familias).
- **Clasificación de contenido (IARC):** categoría "Referencia, noticias o educación". Responde No a todo (violencia, sexo, lenguaje, drogas, apuestas, interacción entre usuarios, compartir ubicación, compras).
- **Seguridad de los datos:** ¿Recoge o comparte datos? → **No**. (La app no recoge datos de usuario.)
- **Política de privacidad:** https://dhd16.github.io/dhdnews/privacidad.html
- **App de noticias (declaración):** Sí es una app de noticias. Página de información del editor y contacto: https://dhd16.github.io/dhdnews/sobre.html
- **App gubernamental / financiera / salud:** No.
