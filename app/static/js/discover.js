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

    let currentPage = 1;
    let currentQuery = '';
    let currentCategory = '';
    let currentSort = 'newest';

    /* ── Tag pills ── */

    tagPills.forEach(pill => {
        pill.addEventListener('click', () => {
            const category = pill.dataset.category;

            if (pill.classList.contains('active') && category !== '') {
                pill.classList.remove('active');
                currentCategory = '';
                const allPill = document.querySelector('#category-tags .tag[data-category=""]');
                if (allPill) allPill.classList.add('active');
            } else {
                tagPills.forEach(t => t.classList.remove('active'));
                pill.classList.add('active');
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
            per_page: 12
        });

        showSpinner(resultsContainer);

        try {
            const data = await apiCall(`/api/recipes?${params}`);

            hideSpinner(resultsContainer);

            if (!append) resultsContainer.innerHTML = '';

            if (data.recipes.length === 0 && !append) {
                resultsContainer.innerHTML = '<div class="col-12"><p class="text-muted-custom text-center">No recipes found.</p></div>';
            } else {
                data.recipes.forEach(recipe => {
                    const col = document.createElement('div');
                    col.className = 'col-lg-3 col-md-4 col-sm-6';
                    col.innerHTML = buildRecipeCard(recipe);
                    resultsContainer.appendChild(col);
                });
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
            hideSpinner(resultsContainer);
            if (!append) {
                resultsContainer.innerHTML = '<div class="col-12"><p class="text-coral text-center">Could not load recipes. Please try again.</p></div>';
            }
        }
    }

    /* ── Card HTML builder ── */

    function buildRecipeCard(r) {
        const imgBlock = r.image_filename
            ? `<img src="/static/uploads/${escapeHtml(r.image_filename)}" alt="${escapeHtml(r.title)}" style="width:100%;height:160px;object-fit:cover;border-radius:12px;margin-bottom:0.65rem;">`
            : '';

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
})();
