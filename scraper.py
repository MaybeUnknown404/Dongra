import httpx
from bs4 import BeautifulSoup
import re
import base64
from typing import List, Dict, Any, Optional

BASE_URL = "https://donghub.vip"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def clean_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("/"):
        return f"{BASE_URL}{url}"
    return url

def clean_title(raw_title: str) -> str:
    if not raw_title:
        return "Donghua"
    title = re.sub(r'\s*Subtitle Indonesia.*$', '', raw_title, flags=re.I).strip()
    if len(title) > 30 and title[:len(title)//2] in title:
        title = title[:len(title)//2].strip()
    return title

def decode_b64_iframe(val: str) -> Dict[str, Optional[str]]:
    """
    Decodes Base64 payload string from Donghub mirror option to extract iframe URL.
    """
    if not val:
        return {"iframe_html": "", "src": ""}
    try:
        missing_padding = len(val) % 4
        if missing_padding:
            val += '=' * (4 - missing_padding)
        decoded_bytes = base64.b64decode(val)
        decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
        
        src_match = re.search(r'src=["\']([^"\']+)["\']', decoded_str)
        src = src_match.group(1) if src_match else ""
        if src.startswith("//"):
            src = f"https:{src}"
            
        return {
            "iframe_html": decoded_str,
            "src": src
        }
    except Exception:
        return {"iframe_html": "", "src": ""}

async def fetch_home_data() -> Dict[str, Any]:
    """
    Fetch homepage components: Hero Slider with backdrop images, Popular Today, Latest Releases, and Sidebar Widgets.
    """
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=15.0) as client:
        try:
            r = await client.get(BASE_URL)
            soup = BeautifulSoup(r.text, "html.parser")
            
            # 1. Hero Slider (Extract backdrop image from style="background-image: url(...)")
            slider_items = []
            slider_cards = soup.select(".slider .item") or soup.select(".swiper-slide") or soup.select(".tp-carousel .bs")
            for item in slider_cards:
                a_tag = item.select_one("a.watch") or item.select_one("h2 a") or item.select_one("a")
                if not a_tag:
                    continue
                href = a_tag.get("href", "")
                slug = href.strip("/").split("/")[-1]
                t_tag = item.select_one("h2") or item.select_one(".tt") or item.select_one("h3")
                
                # Extract background image from backdrop div style
                backdrop_div = item.select_one(".backdrop") or item
                bg_match = re.search(r'url\(["\']?([^"\'\)]+)["\']?\)', str(backdrop_div))
                
                img_src = None
                if bg_match:
                    img_src = bg_match.group(1)
                else:
                    img_tag = item.select_one("img")
                    if img_tag:
                        img_src = img_tag.get("src") or img_tag.get("data-src")
                
                slider_items.append({
                    "title": clean_title(t_tag.get_text(strip=True)) if t_tag else slug.replace("-", " ").title(),
                    "slug": slug,
                    "link": clean_url(href),
                    "poster": clean_url(img_src)
                })

            if not slider_items:
                for art in soup.select("article")[:5]:
                    a_tag = art.select_one("a")
                    if not a_tag:
                        continue
                    href = a_tag.get("href", "")
                    slug = href.strip("/").split("/")[-1]
                    t_tag = art.select_one(".tt") or art.select_one("h2") or art.select_one("h3")
                    img_tag = art.select_one("img")
                    img_src = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
                    slider_items.append({
                        "title": clean_title(t_tag.get_text(strip=True)) if t_tag else slug.replace("-", " ").title(),
                        "slug": slug,
                        "link": clean_url(href),
                        "poster": clean_url(img_src)
                    })

            # 2. Popular Today Grid
            popular_today = []
            pop_cards = soup.select(".popular .bsx") or soup.select(".listupd .bs")
            for c in pop_cards[:10]:
                a_tag = c.select_one("a")
                if not a_tag:
                    continue
                href = a_tag.get("href", "")
                slug = href.strip("/").split("/")[-1]
                t_tag = c.select_one(".tt") or c.select_one("h2") or c.select_one("h3")
                img_tag = c.select_one("img")
                img_src = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
                
                ep_tag = c.select_one(".epx") or c.select_one(".ep")
                status_tag = c.select_one(".status")
                type_tag = c.select_one(".typez") or c.select_one(".type")

                popular_today.append({
                    "title": clean_title(t_tag.get_text(strip=True)) if t_tag else slug.replace("-", " ").title(),
                    "slug": slug,
                    "link": clean_url(href),
                    "poster": clean_url(img_src),
                    "episode": ep_tag.get_text(strip=True) if ep_tag else "Ep terbaru",
                    "status": status_tag.get_text(strip=True) if status_tag else "Ongoing",
                    "type": type_tag.get_text(strip=True) if type_tag else "ONA"
                })

            # 3. Latest Releases Grid
            latest_releases = []
            all_articles = soup.select("article")
            for c in all_articles:
                a_tag = c.select_one("a")
                if not a_tag:
                    continue
                href = a_tag.get("href", "")
                slug = href.strip("/").split("/")[-1]
                t_tag = c.select_one(".tt") or c.select_one("h2") or c.select_one("h3")
                img_tag = c.select_one("img")
                img_src = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
                ep_tag = c.select_one(".epx") or c.select_one(".ep")
                type_tag = c.select_one(".typez") or c.select_one(".type")

                latest_releases.append({
                    "title": clean_title(t_tag.get_text(strip=True)) if t_tag else slug.replace("-", " ").title(),
                    "slug": slug,
                    "link": clean_url(href),
                    "poster": clean_url(img_src),
                    "episode": ep_tag.get_text(strip=True) if ep_tag else "Ep terbaru",
                    "type": type_tag.get_text(strip=True) if type_tag else "ONA"
                })

            # 4. Sidebar Widgets
            new_donghua = latest_releases[:5]
            popular_ranking = []
            sidebar = soup.select_one("#sidebar") or soup.select_one(".sidebar")
            if sidebar:
                pop_widget = sidebar.select_one(".serieslist") or sidebar.select_one(".pop-list") or sidebar
                pop_items = pop_widget.select("li") or pop_widget.select(".bsx")
                for idx, item in enumerate(pop_items[:8]):
                    a_tag = item.select_one("a")
                    if not a_tag:
                        continue
                    href = a_tag.get("href", "")
                    slug = href.strip("/").split("/")[-1]
                    t_tag = item.select_one(".tt") or item.select_one("h4") or a_tag
                    img_tag = item.select_one("img")
                    img_src = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
                    
                    popular_ranking.append({
                        "rank": idx + 1,
                        "title": clean_title(t_tag.get_text(strip=True)),
                        "slug": slug,
                        "link": clean_url(href),
                        "poster": clean_url(img_src)
                    })

            genre_list = [
                {"name": "2D", "slug": "genres/2d"},
                {"name": "Action", "slug": "genres/action"},
                {"name": "Adventure", "slug": "genres/adventure"},
                {"name": "Cheat System", "slug": "genres/cheat-system"},
                {"name": "Comedy", "slug": "genres/comedy"},
                {"name": "Cultivation", "slug": "genres/cultivation"},
                {"name": "Demons", "slug": "genres/demons"},
                {"name": "Drama", "slug": "genres/drama"},
                {"name": "Fantasy", "slug": "genres/fantasy"},
                {"name": "Game World", "slug": "genres/game-world"},
                {"name": "Historical", "slug": "genres/historical"},
                {"name": "Isekai", "slug": "genres/isekai"},
                {"name": "Martial Arts", "slug": "genres/martial-arts"},
                {"name": "Mystery", "slug": "genres/mystery"},
                {"name": "OP-MC", "slug": "genres/op-mc"},
                {"name": "Psychological", "slug": "genres/psychological"},
                {"name": "Reincarnation", "slug": "genres/reincarnation"},
                {"name": "Romance", "slug": "genres/romance"},
                {"name": "Sci-Fi", "slug": "genres/sci-fi"},
                {"name": "Super Power", "slug": "genres/super-power"},
                {"name": "Supranatural", "slug": "genres/supranatural"},
                {"name": "Xianxia", "slug": "genres/xianxia"},
            ]

            return {
                "slider": slider_items,
                "popular_today": popular_today,
                "latest_releases": latest_releases,
                "sidebar": {
                    "new_donghua": new_donghua,
                    "popular_ranking": popular_ranking if popular_ranking else popular_today[:5],
                    "genres": genre_list
                }
            }
        except Exception as e:
            return {"error": str(e)}

async def fetch_donghua_list(category: str = "latest", page: int = 1, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch catalog list, popular list, genre filter, or search results.
    """
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=15.0) as client:
        if query:
            url = f"{BASE_URL}/?s={query}" if page == 1 else f"{BASE_URL}/page/{page}/?s={query}"
        elif category == "anime":
            url = f"{BASE_URL}/anime/?page={page}"
        elif category == "popular" or category == "populer":
            url = f"{BASE_URL}/anime/?order=popular&page={page}" if page > 1 else f"{BASE_URL}/anime/?order=popular"
        elif category.startswith("genre/") or category.startswith("genres/"):
            cat_slug = category.replace("genre/", "genres/").strip("/")
            url = f"{BASE_URL}/{cat_slug}/page/{page}/" if page > 1 else f"{BASE_URL}/{cat_slug}/"
        else:
            url = BASE_URL if page == 1 else f"{BASE_URL}/page/{page}/"

        try:
            r = await client.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            
            anime_list = []
            cards = soup.select("article") or soup.select(".bsx") or soup.select(".bs")
            
            for c in cards:
                a_tag = c.select_one("a")
                if not a_tag:
                    continue
                
                href = a_tag.get("href", "")
                if not href or href == "#":
                    continue
                
                slug = href.strip("/").split("/")[-1]
                t_tag = c.select_one(".tt") or c.select_one("h2") or c.select_one("h3") or c.select_one(".entry-title")
                title = clean_title(t_tag.get_text(strip=True)) if t_tag else slug.replace("-", " ").title()
                
                img_tag = c.select_one("img")
                img_src = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
                img_src = clean_url(img_src)
                
                ep_tag = c.select_one(".epx") or c.select_one(".ep")
                type_tag = c.select_one(".typez") or c.select_one(".type")

                anime_list.append({
                    "title": title,
                    "slug": slug,
                    "link": clean_url(href),
                    "poster": img_src,
                    "episode": ep_tag.get_text(strip=True) if ep_tag else "Donghua",
                    "type": type_tag.get_text(strip=True) if type_tag else "ONA",
                })

            return {
                "page": page,
                "category": category,
                "total": len(anime_list),
                "movies": anime_list
            }
        except Exception as e:
            return {"error": str(e), "movies": []}

async def fetch_schedule() -> Dict[str, Any]:
    """
    Fetch weekly Donghua release schedule from https://donghub.vip/schedule/
    Organized by Day of Week.
    """
    url = f"{BASE_URL}/schedule/"
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=15.0) as client:
        try:
            r = await client.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            
            schedule_data = {}
            day_translation = {
                "Monday": "Senin",
                "Tuesday": "Selasa",
                "Wednesday": "Rabu",
                "Thursday": "Kamis",
                "Friday": "Jumat",
                "Saturday": "Sabtu",
                "Sunday": "Minggu"
            }
            
            schedule_blocks = soup.select(".bixbox.schedulepage") or soup.select(".bScheduled")
            for block in schedule_blocks:
                h_tag = block.select_one("h2") or block.select_one("h3") or block.select_one("h4")
                if not h_tag:
                    continue
                
                raw_day = h_tag.get_text(strip=True)
                day_name = day_translation.get(raw_day, raw_day)
                
                cards = block.select(".bsx") or block.select(".bs") or block.select("article")
                day_items = []
                
                for c in cards:
                    a_tag = c.select_one("a")
                    if not a_tag:
                        continue
                    href = a_tag.get("href", "")
                    slug = href.strip("/").split("/")[-1]
                    t_tag = c.select_one(".tt") or c.select_one("h2") or c.select_one("h3") or c.select_one(".title")
                    img_tag = c.select_one("img")
                    img_src = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
                    ep_tag = c.select_one(".epx") or c.select_one(".ep")
                    
                    day_items.append({
                        "title": clean_title(t_tag.get_text(strip=True)) if t_tag else slug.replace("-", " ").title(),
                        "slug": slug,
                        "link": clean_url(href),
                        "poster": clean_url(img_src),
                        "episode": ep_tag.get_text(strip=True) if ep_tag else "Rilis"
                    })
                
                if day_items:
                    schedule_data[day_name] = day_items

            return {"schedule": schedule_data}
        except Exception as e:
            return {"error": str(e), "schedule": {}}

async def fetch_donghua_detail(slug: str) -> Dict[str, Any]:
    """
    Fetch detailed Donghua series page OR episode page with decoded mirror servers.
    """
    target_url = slug if slug.startswith("http") else f"{BASE_URL}/{slug.strip('/')}/"
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=15.0) as client:
        try:
            r = await client.get(target_url)
            soup = BeautifulSoup(r.text, "html.parser")
            
            title_tag = soup.select_one("h1") or soup.select_one(".entry-title")
            title = clean_title(title_tag.get_text(strip=True)) if title_tag else slug.replace("-", " ").title()
            
            synopsis_tag = soup.select_one(".entry-content") or soup.select_one(".synopsis") or soup.select_one(".desc")
            synopsis = synopsis_tag.get_text(strip=True) if synopsis_tag else "Saksikan tayangan Donghua favorit tanpa gangguan iklan."
            
            poster_tag = soup.select_one(".thumb img") or soup.select_one("article img") or soup.select_one(".poster img")
            poster = poster_tag.get("src") or poster_tag.get("data-src") if poster_tag else None
            poster = clean_url(poster)
            
            genres = []
            genre_tags = soup.select(".genxed a") or soup.select(".genres a") or soup.select("a[href*='/genres/']")
            for g in genre_tags:
                genres.append(g.get_text(strip=True))

            # Decode Video Mirrors
            servers = []
            mirror_options = soup.select("select.mirror option") or soup.select("select option")
            for opt in mirror_options:
                val = opt.get("value", "").strip()
                name = opt.get_text(strip=True)
                if val and "Select" not in name:
                    decoded = decode_b64_iframe(val)
                    if decoded["src"]:
                        servers.append({
                            "name": name,
                            "embed_url": decoded["src"],
                            "html": decoded["iframe_html"]
                        })

            if not servers:
                iframe = soup.select_one(".player-embed iframe") or soup.select_one("iframe")
                if iframe and iframe.get("src"):
                    servers.append({
                        "name": "Default Player",
                        "embed_url": iframe.get("src"),
                        "html": str(iframe)
                    })

            # Episode List
            episodes = []
            ep_items = soup.select(".eplister li") or soup.select(".bxcl li") or soup.select(".eplister a")
            for ep in ep_items:
                a_el = ep if ep.name == "a" else ep.select_one("a")
                if not a_el or not a_el.get("href"):
                    continue
                
                ep_href = a_el.get("href")
                ep_slug = ep_href.strip("/").split("/")[-1]
                num_tag = ep.select_one(".epl-num") or ep.select_one(".epl-title") or a_el
                ep_title = num_tag.get_text(strip=True) if num_tag else "Episode"

                episodes.append({
                    "title": ep_title,
                    "slug": ep_slug,
                    "url": clean_url(ep_href)
                })

            return {
                "title": title,
                "slug": slug,
                "synopsis": synopsis,
                "poster": poster,
                "genres": genres,
                "servers": servers,
                "episodes": episodes
            }
        except Exception as e:
            return {"error": str(e), "title": slug, "servers": [], "episodes": []}
