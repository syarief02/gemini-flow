import json, urllib.request

with open('tiktok_images.json', 'r', encoding='utf-8') as f:
    imgs = json.load(f)

# Filter for unique product images (800x800 or 700x700)
seen = set()
product_imgs = []
for img in imgs:
    if img['width'] >= 700 and img['height'] >= 700:
        base = img['src'].split('~')[0] if '~' in img['src'] else img['src'].split('?')[0]
        if base not in seen:
            seen.add(base)
            product_imgs.append(img)

print(f"Found {len(product_imgs)} unique product images")

for i, img in enumerate(product_imgs, 1):
    url = img['src']
    ext = 'webp' if 'webp' in url else 'jpg'
    fname = f"product_image_{i}.{ext}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=15).read()
        with open(fname, 'wb') as f:
            f.write(data)
        alt_text = img["alt"][:60]
        print(f"  [{i}] Saved {fname} ({len(data)} bytes) - alt: {alt_text}")
    except Exception as e:
        print(f"  [{i}] FAILED {fname}: {e}")

print("Done!")
