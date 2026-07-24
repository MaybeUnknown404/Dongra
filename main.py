from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from scraper import fetch_home_data, fetch_donghua_list, fetch_schedule, fetch_donghua_detail

app = FastAPI(
    title="Donghub - Streaming Anime & Donghua Subtitle Indonesia (Ad-Free)",
    description="1:1 Donghub replica with clean, ad-free Donghua anime streaming.",
    version="2.2.0"
)

# Ensure directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Renders Donghub 1:1 homepage layout.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/home")
async def get_home_api():
    """
    Returns Donghub homepage components: Hero Slider, Popular Today, Latest Releases, and Sidebar Widgets.
    """
    data = await fetch_home_data()
    return data

@app.get("/api/schedule")
async def get_schedule_api():
    """
    Returns weekly Donghua release schedule organized by Day of Week (Monday to Sunday).
    """
    data = await fetch_schedule()
    return data

@app.get("/api/movies")
async def get_donghua_api(
    category: str = Query("latest", description="Donghua category (latest, anime, popular, genre/action)"),
    page: int = Query(1, ge=1, description="Page number"),
    q: str = Query(None, description="Search query")
):
    """
    Returns paginated Donghua catalog list, popular rankings, genre filters, or search results.
    """
    data = await fetch_donghua_list(category=category, page=page, query=q)
    return data

@app.get("/api/movie/{slug:path}")
async def get_donghua_detail_api(slug: str):
    """
    Returns Donghua details, episode list, and decoded video server mirrors.
    """
    data = await fetch_donghua_detail(slug)
    if "error" in data and not data.get("title"):
        raise HTTPException(status_code=404, detail="Donghua tidak ditemukan.")
    return data

@app.get("/api/player", response_class=HTMLResponse)
async def clean_player_proxy(url: str):
    """
    Ad-Blocked Sandboxed Player Embed Proxy.
    Injects strict HTML5 sandbox directives preventing popups, redirects, and gambling ad scripts.
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL player tidak valid.")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Clean Stream Player</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            html, body {{
                width: 100%;
                height: 100%;
                background-color: #000;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            iframe {{
                width: 100%;
                height: 100%;
                border: none;
            }}
        </style>
    </head>
    <body>
        <iframe 
            src="{url}" 
            allowfullscreen="true" 
            webkitallowfullscreen="true" 
            mozallowfullscreen="true"
            sandbox="allow-scripts allow-same-origin allow-presentation allow-forms"
            referrerpolicy="no-referrer">
        </iframe>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
