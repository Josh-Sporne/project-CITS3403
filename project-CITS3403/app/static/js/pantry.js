(function () {
    'use strict';

    const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const chipsContainer = document.getElementById('pantryChips');
    const ingredientInput = document.getElementById('ingredientInput');
    const resultsContainer = document.getElementById('pantry-results');
    const spinner = document.getElementById('loadingSpinner');

    function getIngredients() {
        return Array.from(chipsContainer.querySelectorAll('.pantry-chip'))
            .map(c => c.dataset.name);
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

    function doSuggest(useAi) {
        const ingredients = getIngredients();
        if (ingredients.length === 0) {
            resultsContainer.innerHTML = '<div class="alert alert-warning">Add at least one ingredient to your pantry.</div>';
            return;
        }

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
            }),
        })
            .then(r => r.json())
            .then(data => {
                spinner.classList.add('d-none');
                if (!data.success) {
                    resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error || 'Something went wrong.'}</div>`;
                    return;
                }
                renderResults(data.matches, data.ai_suggestions);
            })
            .catch(() => {
                spinner.classList.add('d-none');
                resultsContainer.innerHTML = '<div class="alert alert-danger">Network error — please try again.</div>';
            });
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
                        <h3>${m.slug ? '<a href="/recipe/' + m.slug + '">' + m.title + '</a>' : m.title}</h3>
                        <div class="d-flex justify-content-between align-items-center" style="font-size:.72rem">
                            <span class="text-muted-custom"><i class="bi bi-clock"></i> ${m.cooking_time || '—'} min</span>
                            <span class="badge bg-info">${m.category || ''}</span>
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
            html += '<h5 class="mb-3"><i class="bi bi-robot text-violet"></i> AI Suggestions</h5>';
            html += '<div class="row g-3">';
            aiSuggestions.forEach(s => {
                html += `
                <div class="col-sm-6">
                    <div class="card h-100">
                        <div class="card-body">
                            <h6 class="card-title">${s.title}</h6>
                            <p class="card-text" style="font-size:.78rem">${s.instructions ? s.instructions.substring(0, 150) + '…' : ''}</p>
                            <div class="d-flex flex-wrap gap-1">
                                ${(s.ingredients || []).map(i => '<span class="chip">' + i + '</span>').join('')}
                            </div>
                        </div>
                    </div>
                </div>`;
            });
            html += '</div>';
        }

        resultsContainer.innerHTML = html;
    }

    document.getElementById('findMatchesBtn').addEventListener('click', function () {
        doSuggest(false);
    });

    document.getElementById('generateAiBtn').addEventListener('click', function () {
        doSuggest(true);
    });
})();
