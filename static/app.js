let currentCategory = 'latest';
let currentPage = 1;
let currentQuery = '';
let currentDonghua = null;
let searchDebounce = null;
let sliderIndex = 0;
let sliderTimer = null;

const ALL_GENRES = [
    { name: "2D", slug: "genre/2d" },
    { name: "Action", slug: "genre/action" },
    { name: "Adventure", slug: "genre/adventure" },
    { name: "Cheat System", slug: "genre/cheat-system" },
    { name: "Comedy", slug: "genre/comedy" },
    { name: "Cultivation", slug: "genre/cultivation" },
    { name: "Demons", slug: "genre/demons" },
    { name: "Drama", slug: "genre/drama" },
    { name: "Fantasy", slug: "genre/fantasy" },
    { name: "Game World", slug: "genre/game-world" },
    { name: "Historical", slug: "genre/historical" },
    { name: "Isekai", slug: "genre/isekai" },
    { name: "Martial Arts", slug: "genre/martial-arts" },
    { name: "Mystery", slug: "genre/mystery" },
    { name: "OP-MC", slug: "genre/op-mc" },
    { name: "Psychological", slug: "genre/psychological" },
    { name: "Reincarnation", slug: "genre/reincarnation" },
    { name: "Romance", slug: "genre/romance" },
    { name: "Sci-Fi", slug: "genre/sci-fi" },
    { name: "Super Power", slug: "genre/super-power" },
    { name: "Supranatural", slug: "genre/supranatural" },
    { name: "Urban Fantasy", slug: "genre/urban-fantasy" },
    { name: "War", slug: "genre/war" },
    { name: "Xianxia", slug: "genre/xianxia" }
];

document.addEventListener('DOMContentLoaded', () => {
    loadHome();

    // Debounced Header Search
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(() => {
            currentQuery = e.target.value.trim();
            currentPage = 1;
            if (currentQuery) {
                document.getElementById('mainHeading').innerText = `Hasil Pencarian: "${currentQuery}"`;
                hideSpecialSections();
                loadMoviesOnly();
            } else {
                loadHome();
            }
        }, 400);
    });

    // ESC closes modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
});

function hideSpecialSections() {
    document.getElementById('heroSection').style.display = 'none';
    document.getElementById('popularTodaySection').style.display = 'none';
    document.getElementById('scheduleSection').style.display = 'none';
    document.getElementById('genreSelectorSection').style.display = 'none';
    document.getElementById('mainFeedSection').style.display = 'block';
}

async function loadHome(navElement) {
    currentCategory = 'latest';
    currentPage = 1;
    currentQuery = '';
    document.getElementById('searchInput').value = '';
    document.getElementById('heroSection').style.display = 'block';
    document.getElementById('popularTodaySection').style.display = 'block';
    document.getElementById('scheduleSection').style.display = 'none';
    document.getElementById('genreSelectorSection').style.display = 'none';
    document.getElementById('mainFeedSection').style.display = 'block';
    document.getElementById('mainHeading').innerText = 'Rilis Episode Terbaru';

    updateNavActive(navElement);

    try {
        const response = await fetch('/api/home');
        const data = await response.json();

        if (data.slider && data.slider.length > 0) {
            renderHeroSlider(data.slider);
        }

        if (data.popular_today && data.popular_today.length > 0) {
            renderAnimeGrid('popularTodayGrid', data.popular_today);
        }

        if (data.latest_releases && data.latest_releases.length > 0) {
            renderAnimeGrid('mainAnimeGrid', data.latest_releases);
        }

        if (data.sidebar) {
            renderSidebarWidgets(data.sidebar);
        }

    } catch (err) {
        console.error("Error loading home:", err);
    }
}

function renderHeroSlider(sliderItems) {
    const sliderTrack = document.getElementById('sliderTrack');
    sliderTrack.innerHTML = sliderItems.map(item => `
        <div class="slider-card" onclick="openDonghuaModal('${item.slug}')" style="background-image: url('${item.poster || 'https://via.placeholder.com/1200x400/1e293b/94a3b8?text=Donghub'}')">
            <div class="slider-content">
                <span class="slider-tag">Featured Donghua</span>
                <h2 class="slider-title">${item.title}</h2>
            </div>
        </div>
    `).join('');

    clearInterval(sliderTimer);
    sliderIndex = 0;
    if (sliderItems.length > 1) {
        sliderTimer = setInterval(() => {
            sliderIndex = (sliderIndex + 1) % sliderItems.length;
            sliderTrack.style.transform = `translateX(-${sliderIndex * 100}%)`;
        }, 5000);
    }
}

function renderAnimeGrid(elementId, items) {
    const container = document.getElementById(elementId);
    if (!container) return;
    container.innerHTML = items.map(item => `
        <div class="anime-card" onclick="openDonghuaModal('${item.slug}')">
            <div class="poster-wrapper">
                <img class="poster-img" src="${item.poster || 'https://via.placeholder.com/300x450/1e293b/94a3b8?text=Donghub'}" alt="${item.title}" loading="lazy">
                <div class="play-overlay">
                    <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                </div>
                ${item.status ? `<div class="status-badge">${item.status}</div>` : ''}
                ${item.episode ? `<div class="ep-badge">${item.episode}</div>` : ''}
                <div class="type-badge">${item.type || 'ONA'}</div>
            </div>
            <div class="card-body">
                <h3 class="card-title">${item.title}</h3>
            </div>
        </div>
    `).join('');
}

function renderSidebarWidgets(sidebarData) {
    const newWidget = document.getElementById('newDonghuaWidget');
    if (sidebarData.new_donghua) {
        newWidget.innerHTML = sidebarData.new_donghua.map(item => `
            <div class="widget-item" onclick="openDonghuaModal('${item.slug}')">
                <img class="widget-thumb" src="${item.poster || 'https://via.placeholder.com/100x140/1e293b/94a3b8'}" alt="${item.title}">
                <div class="widget-info">
                    <div class="widget-name">${item.title}</div>
                    <div class="widget-meta">${item.episode || 'Episode Baru'}</div>
                </div>
            </div>
        `).join('');
    }

    const popWidget = document.getElementById('popularRankingWidget');
    if (sidebarData.popular_ranking) {
        popWidget.innerHTML = sidebarData.popular_ranking.map((item, idx) => `
            <div class="widget-item" onclick="openDonghuaModal('${item.slug}')">
                <div class="widget-rank ${idx === 0 ? 'top1' : idx === 1 ? 'top2' : idx === 2 ? 'top3' : ''}">${idx + 1}</div>
                <img class="widget-thumb" src="${item.poster || 'https://via.placeholder.com/100x140/1e293b/94a3b8'}" alt="${item.title}">
                <div class="widget-info">
                    <div class="widget-name">${item.title}</div>
                    <div class="widget-meta">Top Trending Donghua</div>
                </div>
            </div>
        `).join('');
    }
}

async function loadMoviesOnly() {
    const mainGrid = document.getElementById('mainAnimeGrid');
    mainGrid.innerHTML = '<div style="padding: 40px 0; text-align: center; color: var(--text-muted);">Memuat Donghua...</div>';

    let url = `/api/movies?category=${encodeURIComponent(currentCategory)}&page=${currentPage}`;
    if (currentQuery) {
        url += `&q=${encodeURIComponent(currentQuery)}`;
    }

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (!data.movies || data.movies.length === 0) {
            mainGrid.innerHTML = '<div style="padding: 40px 0; text-align: center; color: var(--text-muted);">Tidak ada Donghua ditemukan.</div>';
            document.getElementById('nextBtn').style.display = 'none';
            return;
        }

        renderAnimeGrid('mainAnimeGrid', data.movies);

        document.getElementById('prevBtn').style.display = currentPage > 1 ? 'block' : 'none';
        document.getElementById('nextBtn').style.display = data.movies.length >= 10 ? 'block' : 'none';

    } catch (err) {
        console.error("Error loading movies:", err);
    }
}

function loadCategory(cat, navElement) {
    currentCategory = cat;
    currentPage = 1;
    currentQuery = '';
    document.getElementById('searchInput').value = '';
    hideSpecialSections();

    updateNavActive(navElement);

    const titleMap = {
        'anime': 'Daftar Katalog Donghua',
        'popular': 'Donghua Populer Teratas',
        'genre/action': 'Genre: Action',
        'genre/fantasy': 'Genre: Fantasy',
        'genre/martial-arts': 'Genre: Martial Arts',
        'genre/romance': 'Genre: Romance',
        'genre/sci-fi': 'Genre: Sci-Fi',
        'genre/2d': 'Genre: 2D Animation',
        'genre/xianxia': 'Genre: Xianxia',
        'genre/cultivation': 'Genre: Cultivation'
    };
    document.getElementById('mainHeading').innerText = titleMap[cat] || `Kategori: ${cat.replace('genre/', '').toUpperCase()}`;

    loadMoviesOnly();
}

async function loadSchedule(navElement) {
    updateNavActive(navElement);
    hideSpecialSections();
    document.getElementById('mainFeedSection').style.display = 'none';
    document.getElementById('scheduleSection').style.display = 'block';

    const container = document.getElementById('scheduleDaysContainer');
    container.innerHTML = '<div style="padding: 40px 0; text-align: center; color: var(--text-muted);">Memuat jadwal rilis Donghua...</div>';

    try {
        const response = await fetch('/api/schedule');
        const data = await response.json();

        if (!data.schedule || Object.keys(data.schedule).length === 0) {
            container.innerHTML = '<div style="padding: 40px 0; text-align: center; color: var(--text-muted);">Gagal memuat jadwal rilis.</div>';
            return;
        }

        let html = '';
        for (const [dayName, items] of Object.entries(data.schedule)) {
            if (items.length === 0) continue;
            html += `
                <div style="margin-bottom: 30px;">
                    <h3 style="font-size: 1.2rem; font-weight: 800; color: var(--accent); margin-bottom: 14px; border-bottom: 1px solid var(--border-color); padding-bottom: 6px;">
                        📅 Hari ${dayName}
                    </h3>
                    <div class="anime-grid">
                        ${items.map(item => `
                            <div class="anime-card" onclick="openDonghuaModal('${item.slug}')">
                                <div class="poster-wrapper">
                                    <img class="poster-img" src="${item.poster || 'https://via.placeholder.com/300x450/1e293b/94a3b8'}" alt="${item.title}" loading="lazy">
                                    <div class="play-overlay">
                                        <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                                    </div>
                                    <div class="ep-badge">${item.episode || 'Rilis'}</div>
                                </div>
                                <div class="card-body">
                                    <h3 class="card-title">${item.title}</h3>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        container.innerHTML = html;

    } catch (err) {
        console.error("Error loading schedule:", err);
        container.innerHTML = '<div style="padding: 40px 0; text-align: center; color: var(--text-muted);">Gagal memuat jadwal rilis.</div>';
    }
}

function loadGenrePage(navElement) {
    updateNavActive(navElement);
    hideSpecialSections();
    document.getElementById('genreSelectorSection').style.display = 'block';

    const fullGenreGrid = document.getElementById('fullGenreGrid');
    fullGenreGrid.innerHTML = ALL_GENRES.map(g => `
        <button class="btn-chip" onclick="loadCategory('${g.slug}', null)">
            ${g.name}
        </button>
    `).join('');

    // Load first genre by default
    loadCategory('genre/action', null);
}

function updateNavActive(navElement) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    if (navElement) navElement.classList.add('active');
}

function changePage(delta) {
    currentPage += delta;
    if (currentPage < 1) currentPage = 1;
    loadMoviesOnly();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function openDonghuaModal(slug) {
    const modal = document.getElementById('donghuaModal');
    const playerBox = document.getElementById('playerBox');
    const videoIframe = document.getElementById('videoIframe');
    const serversSection = document.getElementById('serversSection');
    const serversGrid = document.getElementById('serversGrid');
    const episodesSection = document.getElementById('episodesSection');
    const episodesGrid = document.getElementById('episodesGrid');

    playerBox.style.display = 'none';
    videoIframe.src = '';
    episodesSection.style.display = 'none';
    serversSection.style.display = 'none';
    
    document.getElementById('modalTitle').innerText = 'Memuat rincian Donghua...';
    document.getElementById('modalPoster').src = '';
    document.getElementById('modalSynopsis').innerText = '';

    modal.classList.add('active');

    try {
        const response = await fetch(`/api/movie/${encodeURIComponent(slug)}`);
        const data = await response.json();
        currentDonghua = data;

        document.getElementById('modalTitle').innerText = data.title || 'Donghua';
        document.getElementById('modalPoster').src = data.poster || 'https://via.placeholder.com/300x450/1e293b/94a3b8';
        document.getElementById('modalGenres').innerText = (data.genres && data.genres.length) ? data.genres.join(', ') : 'Donghua, Anime';
        document.getElementById('modalSynopsis').innerText = data.synopsis || 'Saksikan tayangan Donghua tanpa gangguan iklan judi.';

        if (data.episodes && data.episodes.length > 0) {
            episodesSection.style.display = 'block';
            episodesGrid.innerHTML = data.episodes.map(ep => `
                <button class="btn-chip" onclick="openDonghuaModal('${ep.slug}')">
                    ${ep.title}
                </button>
            `).join('');
        }

        if (data.servers && data.servers.length > 0) {
            serversSection.style.display = 'block';
            serversGrid.innerHTML = data.servers.map((s, idx) => `
                <button class="btn-chip ${idx === 0 ? 'active' : ''}" onclick="playMirror('${s.embed_url}', this)">
                    ▶ Server ${s.name}
                </button>
            `).join('');

            playMirror(data.servers[0].embed_url, serversGrid.children[0]);
        }

        updateBookmarkBtnText();

    } catch (err) {
        console.error("Error fetching detail:", err);
        document.getElementById('modalTitle').innerText = 'Gagal Memuat Detail';
    }
}

function playMirror(embedUrl, btnElement) {
    if (!embedUrl) return;

    document.querySelectorAll('#serversGrid .btn-chip').forEach(b => b.classList.remove('active'));
    if (btnElement) btnElement.classList.add('active');

    const playerBox = document.getElementById('playerBox');
    const videoIframe = document.getElementById('videoIframe');

    videoIframe.src = `/api/player?url=${encodeURIComponent(embedUrl)}`;
    playerBox.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('donghuaModal');
    const videoIframe = document.getElementById('videoIframe');
    modal.classList.remove('active');
    videoIframe.src = '';
}

function getBookmarks() {
    return JSON.parse(localStorage.getItem('donghub_bookmarks') || '[]');
}

function toggleBookmarkCurrent() {
    if (!currentDonghua) return;
    let bookmarks = getBookmarks();
    const idx = bookmarks.findIndex(b => b.slug === currentDonghua.slug);
    if (idx >= 0) {
        bookmarks.splice(idx, 1);
    } else {
        bookmarks.push({
            title: currentDonghua.title,
            slug: currentDonghua.slug,
            poster: currentDonghua.poster
        });
    }
    localStorage.setItem('donghub_bookmarks', JSON.stringify(bookmarks));
    updateBookmarkBtnText();
}

function updateBookmarkBtnText() {
    const btn = document.getElementById('bookmarkBtn');
    if (!btn || !currentDonghua) return;
    const bookmarks = getBookmarks();
    const isBookmarked = bookmarks.some(b => b.slug === currentDonghua.slug);
    btn.innerText = isBookmarked ? '✓ Tersimpan di Bookmark' : '+ Simpan Bookmark';
}

function showBookmarks(navElement) {
    updateNavActive(navElement);
    hideSpecialSections();
    document.getElementById('mainHeading').innerText = 'Donghua Tersimpan (Bookmark)';

    const bookmarks = getBookmarks();
    if (bookmarks.length === 0) {
        document.getElementById('mainAnimeGrid').innerHTML = '<div style="padding: 40px 0; text-align: center; color: var(--text-muted);">Belum ada Donghua yang disimpan di Bookmark.</div>';
        return;
    }

    renderAnimeGrid('mainAnimeGrid', bookmarks);
}
