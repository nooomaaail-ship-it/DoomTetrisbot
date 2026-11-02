import requests, json, os, sys, time, re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE = "https://egy.voxcinemas.com"
PAGES = [BASE + "/movies/whatson", BASE + "/movies/comingsoon"]
TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FILE = "seen.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SKIP = {"whatson", "comingsoon", "advance-booking", "kids", "search"}


def fetch(url):
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=(10, 30), headers=HEADERS)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            print(f"محاولة {attempt + 1} فشلت ({url}): {e}")
            time.sleep(5)
    return None


movies = {}
for page in PAGES:
    html = fetch(page)
    if html is None:
        continue
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        m = re.match(r"^(?:https?://egy\.voxcinemas\.com)?/movies/([^/?#]+)/?$", a["href"])
        if not m or m.group(1) in SKIP:
            continue
        slug = m.group(1)
        name = a.get("title") or a.get_text(" ", strip=True) or slug.replace("-", " ").title()
        if slug not in movies or len(name) > len(movies[slug]):
            movies[slug] = name

print("تم قراءة", len(movies), "فيلم")

if not movies:
    print("مفيش أفلام اتقرأت")
    sys.exit(0)

seen = set(json.load(open(FILE))) if os.path.exists(FILE) else None

if seen is not None:
    for slug in sorted(movies.keys() - seen):
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={
                "chat_id": CHAT_ID,
                "text": f"نزل فيلم جديد: {movies[slug]}\n{BASE}/movies/{slug}",
            },
            timeout=20,
        )

json.dump(sorted((seen or set()) | set(movies)), open(FILE, "w"), ensure_ascii=False)
