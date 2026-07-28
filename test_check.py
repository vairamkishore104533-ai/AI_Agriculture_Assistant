import requests
r = requests.get('http://127.0.0.1:5000/static/js/fertilizer.js', timeout=5)
js = r.text
checks = [
    ("positionDropdown", "function positionDropdown"),
    ("position fixed in CSS", 'style.left = rect.left'),
    ("no blur handler", 'addEventListener("blur"' not in js),
    ("doc click close", 'e.target.closest(".fert-search-select")' in js),
    ("passive scroll", 'passive: true' in js),
    ("buildSearchSelect", "function buildSearchSelect"),
]
for name, check in checks:
    print(f"{'OK' if check else 'FAIL'}: {name}")
print(f"Size: {len(js)} bytes")
