/* Plate Theory — Discover Page Interactivity */

(function () {
    'use strict';

    const searchInput = document.getElementById('search-input') || document.getElementById('discover-search');
    const tagPills = document.querySelectorAll('#category-tags .tag, .discover-tag');
    const sortSelect = document.getElementById('sort-select') || document.getElementById('discover-sort');
    const resultsContainer = document.getElementById('recipe-results');
    const loadMoreWrap = document.getElementById('load-more-wrap');
    const resultCount = document.getElementById('result-count') || document.getElementById('results-count');

    if (!resultsContainer) return;

    // Pick up initial pagination state from data attributes the server set,
    // so deep links like /discover?page=3 don't make Load More re-fetch page 1.
    const initialPage = parseInt(resultsContainer.dataset.currentPage, 10) || 1;
    const perPage = parseInt(resultsContainer.dataset.perPage, 10) || 12;

    // Pick up initial filter state from the URL so deep links like
    // /discover?category=vegan or /discover?q=pasta apply on page load.
    const urlParams = new URLSearchParams(window.location.search);
    const initialCategory = (urlParams.get('category') || '').toLowerCase();
    const initialQuery = urlParams.get('q') || '';

    let currentPage = initialPage;
    let currentQuery = initialQuery;
    let currentCategory = initialCategory;
    let currentSort = 'newest';

    /* ── Tag pills ── */

    function setActiveTag(activePill) {
        tagPills.forEach(t => {
            const isActive = t === activePill;
            t.classList.toggle('active', isActive);
            t.setAttribute('aria-pressed', String(isActive));
        });
    }

    tagPills.forEach(pill => {
        pill.addEventListener('click', () => {
            const category = pill.dataset.category;

            if (pill.classList.contains('active') && category !== '') {
                // Deselecting the current category — fall back to "All".
                const allPill = document.querySelector('#category-tags .tag[data-category=""]');
                setActiveTag(allPill || pill);
                currentCategory = '';
            } else {
                setActiveTag(pill);
                currentCategory = category || '';
            }

            currentPage = 1;
            fetchRecipes(false);
        });
    });

    /* ── Search with debounce ── */

    let debounceTimer;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                currentQuery = searchInput.value.trim();
                currentPage = 1;
                fetchRecipes(false);
            }, 300);
        });
    }

    /* ── Sort dropdown ── */

    if (sortSelect) {
        sortSelect.addEventListener('change', () => {
            currentSort = sortSelect.value;
            currentPage = 1;
            fetchRecipes(false);
        });
    }

    /* ── Load More ── */

    function bindLoadMore() {
        const btn = document.getElementById('load-more-btn');
        if (btn) {
            btn.addEventListener('click', () => {
                currentPage++;
                fetchRecipes(true);
            });
        }
    }

    bindLoadMore();

    /* ── Fetch recipes ── */

    async function fetchRecipes(append) {
        const params = new URLSearchParams({
            q: currentQuery,
            category: currentCategory,
            sort: currentSort,
            page: currentPage,
            per_page: perPage
        });

        // Keep the browser URL in sync so Back/Forward and sharing work correctly.
        if (!append) {
            const urlParams = new URLSearchParams();
            if (currentQuery)                  urlParams.set('q', currentQuery);
            if (currentCategory)               urlParams.set('category', currentCategory);
            if (currentSort !== 'newest')      urlParams.set('sort', currentSort);
            if (currentPage > 1)               urlParams.set('page', currentPage);
            const newUrl = urlParams.toString()
                ? `${window.location.pathname}?${urlParams}`
                : window.location.pathname;
            history.pushState(
                { q: currentQuery, category: currentCategory, sort: currentSort, page: currentPage },
                '',
                newUrl
            );
        }

        // Skeleton placeholders only on a fresh fetch (not when appending more
        // results via Load More — those shouldn't blank out what's already there).
        if (!append) showSkeletons(resultsContainer, perPage);

        try {
            const data = await apiCall(`/api/recipes?${params}`);

            if (!append) resultsContainer.innerHTML = '';  // clears skeletons

            if (data.recipes.length === 0 && !append) {
                resultsContainer.innerHTML = '<div class="col-12"><p class="text-muted-custom text-center">No recipes found.</p></div>';
            } else {
                const newCols = [];
                data.recipes.forEach(recipe => {
                    const col = document.createElement('div');
                    col.className = 'col-lg-3 col-md-4 col-sm-6';
                    col.innerHTML = buildRecipeCard(recipe);
                    resultsContainer.appendChild(col);
                    const card = col.querySelector('.pt-card');
                    if (card) newCols.push(card);
                });
                // Register new cards with the scroll reveal observer
                if (newCols.length && window.revealElements) {
                    window.revealElements(newCols);
                }
            }

            const shown = resultsContainer.querySelectorAll('.pt-card').length;
            if (resultCount) {
                resultCount.textContent = `Showing ${shown} of ${data.total} recipes`;
            }

            if (loadMoreWrap) {
                loadMoreWrap.innerHTML = data.has_next
                    ? '<button id="load-more-btn" class="btn btn-outline-light"><i class="bi bi-arrow-down-circle me-1"></i> Load More</button>'
                    : '';
                bindLoadMore();
            }
        } catch (err) {
            if (!append) {
                resultsContainer.innerHTML = '<div class="col-12"><p class="text-coral text-center">Could not load recipes. Please try again.</p></div>';
            }
        }
    }

    /* ── Skeleton placeholder cards ── */
    function showSkeletons(grid, count) {
        grid.innerHTML = '';  // wipe whatever was there
        for (let i = 0; i < count; i++) {
            const col = document.createElement('div');
            col.className = 'col-lg-3 col-md-4 col-sm-6';
            col.innerHTML = `
                <div class="pt-card h-100" aria-hidden="true">
                    <div class="skeleton" style="height:160px;border-radius:12px;margin-bottom:0.65rem;"></div>
                    <div class="skeleton" style="height:1.2rem;width:75%;margin-bottom:0.4rem;"></div>
                    <div class="skeleton" style="height:0.9rem;width:50%;margin-bottom:0.4rem;"></div>
                    <div class="skeleton" style="height:0.9rem;width:35%;"></div>
                </div>`;
            grid.appendChild(col);
        }
    }

    /* ── Card HTML builder ── */

    function buildRecipeCard(r) {
        // Same image-fallback pattern as the server-rendered partial:
        // real upload if present, otherwise a deterministic Loremflickr food photo.
        // Use the recipe slug as comma-separated keywords (e.g. "kimchi-fried-rice"
        // → "kimchi,fried,rice") so Loremflickr returns more relevant food photos.
        const slugTags = (r.slug || '').replace(/-/g, ',');
        let imgSrc;
        if (r.image_filename) {
            // image_filename can be either a local upload filename OR a full URL
            // (curated images in seed.py use Wikimedia Special:FilePath URLs).
            imgSrc = r.image_filename.startsWith('http')
                ? r.image_filename
                : `/static/uploads/${escapeHtml(r.image_filename)}`;
        } else {
            imgSrc = `https://loremflickr.com/600/400/${slugTags},food?lock=${r.id}`;
        }
        const imgBlock = `<img src="${imgSrc}" alt="${escapeHtml(r.title)}" style="width:100%;height:160px;object-fit:cover;border-radius:12px;margin-bottom:0.65rem;">`;

        const stars = Array.from({ length: 5 }, (_, i) =>
            `<i class="bi bi-star${i < Math.round(r.avg_rating || 0) ? '-fill' : ''}"></i>`
        ).join('');

        const slug = r.slug || '';
        const title = escapeHtml(r.title || 'Untitled');
        const time = r.cooking_time || 30;
        const category = escapeHtml(r.category || '');
        const rating = (r.avg_rating || 0).toFixed(1);
        const creator = r.creator ? escapeHtml(r.creator.username) : '';

        const aiBadge = r.is_ai_generated
            ? '<span class="badge badge-ai ms-1">AI</span>'
            : '';

        return `
        <article class="pt-card h-100">
            <div class="img-ph">${imgBlock}</div>
            <h3><a href="/recipe/${slug}" class="text-decoration-none" style="color:var(--pt-text);">${title}</a>${aiBadge}</h3>
            <p>
                <i class="bi bi-clock"></i> ${time} min
                ${category ? `<span class="badge bg-info ms-2">${category}</span>` : ''}
            </p>
            <div class="star-rating mb-1">
                ${stars}
                <span class="ms-1 small text-muted-custom">${rating}</span>
            </div>
            ${creator ? `<p class="mb-0"><small>by <a href="/user/${creator}">${creator}</a></small></p>` : ''}
        </article>`;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    /* ── Restore state on Back/Forward ── */
    window.addEventListener('popstate', (e) => {
        const s = e.state || {};
        currentQuery    = s.q        || '';
        currentCategory = s.category || '';
        currentSort     = s.sort     || 'newest';
        currentPage     = s.page     || 1;

        if (searchInput) searchInput.value = currentQuery;
        if (sortSelect)  sortSelect.value  = currentSort;
        tagPills.forEach(t => {
            const match = t.dataset.category === currentCategory ||
                          (!currentCategory && t.dataset.category === '');
            t.classList.toggle('active', match);
            t.setAttribute('aria-pressed', String(match));
        });
        fetchRecipes(false);
    });

    /* ── Initial sync: apply ?category and ?q from URL on page load ── */
    if (initialCategory || initialQuery) {
        if (searchInput && initialQuery) {
            searchInput.value = initialQuery;
        }
        if (initialCategory) {
            tagPills.forEach(t => {
                const isMatch = t.dataset.category.toLowerCase() === initialCategory;
                t.classList.toggle('active', isMatch);
                t.setAttribute('aria-pressed', String(isMatch));
            });
        }
        // Re-fetch from page 1 with the URL-derived filters applied.
        currentPage = 1;
        fetchRecipes(false);
    }
})();
