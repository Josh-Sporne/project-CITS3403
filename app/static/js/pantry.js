(function () {
    'use strict';

    const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const chipsContainer = document.getElementById('pantryChips');
    const ingredientInput = document.getElementById('ingredientInput');
    const resultsContainer = document.getElementById('pantry-results');
    const feedbackEl = document.getElementById('pantry-save-feedback');
    const spinner = document.getElementById('loadingSpinner');

    let lastAiSuggestions = [];

    function getIngredients() {
        return Array.from(chipsContainer.querySelectorAll('.pantry-chip'))
            .map(c => c.dataset.name);
    }

    function escapeHtml(str) {
        if (str == null) return '';
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(String(str)));
        return div.innerHTML;
    }

    function addChip(name) {
        name = name.trim();
        if (!name) return;
        if (getIngredients().some(n => n.toLowerCase() === name.toLowerCase())) return;

        const span = document.createElement('span');
        span.className = 'chip pantry-chip';
        span.dataset.name = name;
        span.innerHTML = `${name} <button type="button" class="btn-close btn-close-white ms-1" style="font-size:.5rem;vertical-align:middle" aria-label="Remove"></button>`;
        chipsContainer.appendChild(span);
    }

    function removeChip(chip) {
        chip.remove();
    }

    ingredientInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addChip(this.value);
            this.value = '';
        }
    });

    document.getElementById('addIngredientBtn').addEventListener('click', function () {
        addChip(ingredientInput.value);
        ingredientInput.value = '';
        ingredientInput.focus();
    });

    chipsContainer.addEventListener('click', function (e) {
        const closeBtn = e.target.closest('.btn-close');
        if (closeBtn) {
            removeChip(closeBtn.closest('.pantry-chip'));
        }
    });

    function buildPreferences() {
        const parts = [];
        const diet = document.getElementById('dietSelect').value;
        const maxTime = document.getElementById('maxTime').value;
        if (diet) parts.push('Diet: ' + diet);
        if (maxTime) parts.push('Max cooking time: ' + maxTime + ' minutes');
        return parts.join('. ');
    }

    function showSaveFeedback(slug, isPrivate) {
        if (!feedbackEl) return;
        const view = '/recipe/' + encodeURIComponent(slug);
        const edit = view + '/edit';
        let extra = '';
        if (isPrivate) {
            extra = ' <button type="button" class="btn btn-sm btn-mint ms-2 btn-feedback-publish" data-slug="' +
                escapeHtml(slug) + '">Publish now</button>';
        }
        feedbackEl.innerHTML =
            '<div class="alert alert-success mb-0">' +
            '<strong>Saved.</strong> ' +
            '<a href="' + view + '">View recipe</a> · ' +
            '<a href="' + edit + '">Edit</a>' +
            extra +
            '</div>';
    }

    function doSuggest(useAi) {
        const ingredients = getIngredients();
        if (ingredients.length === 0) {
            resultsContainer.innerHTML = '<div class="alert alert-warning">Add at least one ingredient to your pantry.</div>';
            return;
        }

        if (feedbackEl) feedbackEl.innerHTML = '';

        spinner.classList.remove('d-none');
        resultsContainer.innerHTML = '';

        fetch('/api/ai/suggest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF,
            },
            body: JSON.stringify({
                ingredients: ingredients,
                preferences: buildPreferences(),
                use_ai: useAi,
                max_time: parseInt(document.getElementById('maxTime').value) || null,
            }),
        })
            .then(r => r.json())
            .then(data => {
                spinner.classList.add('d-none');
                if (!data.success) {
                    resultsContainer.innerHTML = `<div class="alert alert-danger">${escapeHtml(data.error || 'Something went wrong.')}</div>`;
                    return;
                }
                renderResults(data.matches, data.ai_suggestions);
            })
            .catch(() => {
                spinner.classList.add('d-none');
                resultsContainer.innerHTML = '<div class="alert alert-danger">Network error — please try again.</div>';
            });
    }

    function ingredientChipHtml(ing) {
        if (typeof ing === 'string') {
            const n = ing.trim();
            return n ? '<span class="chip">' + escapeHtml(n) + '</span>' : '';
        }
        if (ing && typeof ing === 'object') {
            const n = (ing.name || ing.title || ing.ingredient || '').toString().trim();
            return n ? '<span class="chip">' + escapeHtml(n) + '</span>' : '';
        }
        return '';
    }

    function renderResults(matches, aiSuggestions) {
        let html = '';

        if (matches && matches.length > 0) {
            html += '<h5 class="mb-3"><i class="bi bi-book text-mint"></i> Matching Recipes</h5>';
            html += '<div class="row g-3 mb-4">';
            matches.forEach(m => {
                const color = m.match_pct >= 75 ? 'var(--pt-mint)' :
                    m.match_pct >= 40 ? 'var(--pt-sun)' : 'var(--pt-coral)';
                html += `
                <div class="col-sm-6 col-lg-4">
                    <div class="pt-card h-100">
                        <div class="img-ph" style="height:60px"></div>
                        <h3>${m.slug ? '<a href="/recipe/' + escapeHtml(m.slug) + '">' + escapeHtml(m.title) + '</a>' : escapeHtml(m.title)}</h3>
                        <div class="d-flex justify-content-between align-items-center" style="font-size:.72rem">
                            <span class="text-muted-custom"><i class="bi bi-clock"></i> ${m.cooking_time || '—'} min</span>
                            <span class="badge bg-info">${escapeHtml(m.category || '')}</span>
                        </div>
                        <div class="match-bar mt-2">
                            <div class="match-fill" style="width:${m.match_pct}%;background:${color}"></div>
                        </div>
                        <p style="font-size:.68rem;margin-top:.3rem" class="text-muted-custom mb-0">
                            ${m.matched_ingredients}/${m.total_ingredients} ingredients · <strong style="color:${color}">${m.match_pct}%</strong> match
                        </p>
                    </div>
                </div>`;
            });
            html += '</div>';
        } else {
            html += '<div class="alert alert-info mb-4">No matching recipes found. Try adding more ingredients.</div>';
        }

        if (aiSuggestions && aiSuggestions.length > 0) {
            lastAiSuggestions = aiSuggestions;
            html += '<h5 class="mb-3"><i class="bi bi-robot text-violet"></i> AI Suggestions</h5>';
            html += '<div class="row g-3">';
            aiSuggestions.forEach((s, idx) => {
                const title = escapeHtml(s.title || 'Untitled');
                const instr = escapeHtml(s.instructions || '');
                const ingList = (s.ingredients || []).map(ingredientChipHtml).join('');
                html += `
                <div class="col-sm-6 col-lg-4">
                    <div class="pt-card h-100 pantry-ai-card d-flex flex-column" data-ai-index="${idx}">
                        <div class="img-ph" style="height:48px"></div>
                        <h3 style="font-size:1rem">${title}</h3>
                        <div class="text-muted-custom flex-grow-1" style="font-size:.78rem;white-space:pre-wrap;min-height:4rem">${instr}</div>
                        <div class="d-flex flex-wrap gap-1 mt-2 mb-3">${ingList}</div>
                        <div class="d-flex flex-wrap gap-2 mt-auto">
                            <button type="button" class="btn btn-sm btn-outline-light" data-save-ai data-vis="private" data-idx="${idx}">Save for me</button>
                            <button type="button" class="btn btn-sm btn-mint" data-save-ai data-vis="public" data-idx="${idx}">Save &amp; publish</button>
                        </div>
                    </div>
                </div>`;
            });
            html += '</div>';
        } else {
            lastAiSuggestions = [];
        }

        resultsContainer.innerHTML = html;
    }

    resultsContainer.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-save-ai]');
        if (!btn) return;

        const idx = parseInt(btn.dataset.idx, 10);
        const suggestion = lastAiSuggestions[idx];
        if (!suggestion) return;

        const card = btn.closest('.pantry-ai-card');
        const buttons = card ? card.querySelectorAll('[data-save-ai]') : [];
        buttons.forEach(b => { b.disabled = true; });

        const maxEl = document.getElementById('maxTime');
        const dietEl = document.getElementById('dietSelect');
        const maxVal = maxEl && maxEl.value ? parseInt(maxEl.value, 10) : null;
        const dietHint = dietEl ? dietEl.value : '';

        fetch('/api/ai/save-recipe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF,
            },
            body: JSON.stringify({
                title: suggestion.title,
                instructions: suggestion.instructions,
                ingredients: suggestion.ingredients,
                visibility: btn.dataset.vis === 'public' ? 'public' : 'private',
                max_cooking_time: Number.isFinite(maxVal) ? maxVal : null,
                diet_hint: dietHint || null,
            }),
        })
            .then(r => r.json().then(data => ({ ok: r.ok, data })))
            .then(res => {
                if (res.ok && res.data.success) {
                    showSaveFeedback(res.data.slug, btn.dataset.vis === 'private');
                } else {
                    alert(res.data.error || 'Could not save recipe.');
                }
            })
            .catch(() => {
                alert('Network error — please try again.');
            })
            .finally(() => {
                buttons.forEach(b => { b.disabled = false; });
            });
    });

    if (feedbackEl) {
        feedbackEl.addEventListener('click', function (e) {
            const pub = e.target.closest('.btn-feedback-publish');
            if (!pub) return;
            const slug = pub.dataset.slug;
            if (!slug || !confirm('Publish this recipe for everyone to see?')) return;
            pub.disabled = true;
            fetch('/api/recipe/' + encodeURIComponent(slug) + '/visibility', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
                body: JSON.stringify({ public: true }),
            })
                .then(r => r.json().then(data => ({ ok: r.ok, data })))
                .then(res => {
                    if (res.ok && res.data.success) {
                        window.location.href = '/recipe/' + encodeURIComponent(slug);
                    } else {
                        alert(res.data.error || 'Could not publish.');
                        pub.disabled = false;
                    }
                })
                .catch(() => {
                    alert('Network error.');
                    pub.disabled = false;
                });
        });
    }

    document.getElementById('findMatchesBtn').addEventListener('click', function () {
        doSuggest(false);
    });

    document.getElementById('generateAiBtn').addEventListener('click', function () {
        doSuggest(true);
    });
})();
