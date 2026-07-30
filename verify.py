import httpx, json, sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE = "http://localhost:8000"

ENDPOINTS = [
    "/",
    "/home",
    "/movies",
    "/tv-series",
    "/animation",
]

def check_movies(movies, label):
    total = len(movies)
    with_poster = sum(1 for m in movies if m.get("poster_url"))
    with_name = sum(1 for m in movies if m.get("name"))
    print(f"    movies: {total} | names: {with_name}/{total} | posters: {with_poster}/{total}")
    if movies:
        m = movies[0]
        print(f"    sample: name={m.get('name','?')[:40]!r} | poster={'YES' if m.get('poster_url') else 'NULL'}")

for path in ENDPOINTS:
    url = BASE + path
    try:
        r = httpx.get(url, timeout=30)
        status = "OK" if r.status_code == 200 else f"ERR {r.status_code}"
        print(f"\n[{status}] {path}")

        # Root dashboard
        if path == "/":
            print(f"  dashboard loaded: HTTP {r.status_code} (HTML dashboard)")
            continue

        data = r.json()

        # Multi-section pages (/home, /movies, /tv-series, /animation)
        sections = data.get("sections", [])
        if sections:
            print(f"  total_sections: {len(sections)}")
            for s in sections:
                print(f"  [{s.get('section','?')!r}] {s.get('count',0)} movies")
                check_movies(s.get("items", []), s.get("section", "?"))
        else:
            # Single flat list (e.g. /movies returns items directly)
            items = data.get("items", [])
            print(f"  items: {len(items)}")
            check_movies(items, path)

    except Exception as e:
        print(f"\n[FAIL] {path} => {e}")

# Test search
print("\n--- Search Test ---")
try:
    r = httpx.get(f"{BASE}/search?q=attack", timeout=30)
    data = r.json()
    items = data.get("items", [])
    print(f"[OK] /search?q=attack => {len(items)} results")
    if items:
        print(f"  sample: name={items[0].get('name','?')[:40]!r}")
except Exception as e:
    print(f"[FAIL] /search => {e}")

print("\n\nDone.")
