#!/usr/bin/env python3
"""Convierte el export de un artefacto (HTML con assets inlined como data URIs)
en la versión ligera para GitHub Pages: data URIs -> rutas relativas assets/.

Uso: python3 export-to-light.py <export.html> [salida.html]
- Los assets que ya existen en assets/ se identifican por hash SHA-256.
- Un data URI sin coincidencia se guarda como assets/fondo-nosotros.jpg
  (único asset nuevo esperado; si hay más de uno, se aborta).
"""
import base64, hashlib, re, sys
from pathlib import Path

EXPORT = Path(sys.argv[1])
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "index.html"
ASSETS = Path(__file__).parent / "assets"

html = EXPORT.read_text(encoding="utf-8")

# Hash de los assets ya existentes
known = {}
for f in ASSETS.iterdir():
    if f.is_file():
        known[hashlib.sha256(f.read_bytes()).hexdigest()] = f.name

pattern = re.compile(r"data:(image/[a-z0-9.+-]+|video/[a-z0-9.+-]+|application/octet-stream);base64,([A-Za-z0-9+/=]+)")
uris = {}
for m in pattern.finditer(html):
    uris.setdefault(m.group(0), (m.group(1), m.group(2)))

print(f"Data URIs únicos en el export: {len(uris)}")
new_saved = []
replacements = {}
for uri, (mime, b64) in uris.items():
    raw = base64.b64decode(b64)
    h = hashlib.sha256(raw).hexdigest()
    if h in known:
        replacements[uri] = f"assets/{known[h]}"
    else:
        ext = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif",
               "image/webp": "webp", "video/mp4": "mp4"}.get(mime)
        if ext is None:
            raise SystemExit(f"ERROR: data URI sin coincidencia y MIME no esperado: {mime}")
        name = f"fondo-nosotros.{ext}"
        (ASSETS / name).write_bytes(raw)
        new_saved.append(name)
        replacements[uri] = f"assets/{name}"
        print(f"Nuevo asset guardado: assets/{name} ({len(raw)} bytes, {mime})")

for uri, rel in replacements.items():
    html = html.replace(uri, rel)

leftover = len(pattern.findall(html))
print(f"Reemplazos: {len(replacements)} | data URIs restantes: {leftover}")
if leftover:
    raise SystemExit("ERROR: quedaron data URIs sin reemplazar")

OUT.write_text(html, encoding="utf-8")
print(f"Escrito: {OUT} ({OUT.stat().st_size} bytes)")
