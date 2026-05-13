(function () {
    'use strict';

    const CSRF = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const modalEl = document.getElementById('assignModal');
    const modal = new bootstrap.Modal(modalEl);

    let selectedDay = null;
    let selectedMeal = null;
    let currentRange = 'week';

    function safeReload() {
        modalEl.addEventListener('hidden.bs.modal', () => location.reload(), { once: true });
        modal.hide();
    }

    /* --- Add-meal buttons --- */
    document.getElementById('plannerGrid').addEventListener('click', function (e) {
        const addBtn = e.target.closest('.add-btn');
        if (addBtn) {
            selectedDay = parseInt(addBtn.dataset.day, 10);
            selectedMeal = addBtn.dataset.meal;
            document.getElementById('modalDayLabel').textContent = DAY_NAMES[selectedDay];
            document.getElementById('modalMealLabel').textContent = selectedMeal;
            document.getElementById('recipeSelect').value = '';
            document.getElementById('customText').value = '';
            document.getElementById('recipeSearch').value = '';
            document.querySelectorAll('#recipeSelect option').forEach(o => o.hidden = false);
            modal.show();
            return;
        }

        const removeBtn = e.target.closest('.remove-btn');
        if (removeBtn) {
            const itemId = removeBtn.dataset.itemId;
            if (!itemId) return;
            fetch('/api/planner/remove', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF,
                },
                body: JSON.stringify({ item_id: parseInt(itemId, 10) }),
            })
                .then(r => r.json())
                .then(data => {
                    if (data.success) safeReload();
                })
                .catch(() => {
                    showErrorToast('Could not remove meal. Please try again.');
                });
        }
    });

    /* --- Save assignment --- */
    document.getElementById('saveAssign').addEventListener('click', function () {
        const recipeId = document.getElementById('recipeSelect').value;
        const customText = document.getElementById('customText').value.trim();

        if (!recipeId && !customText) return;

        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving…';

        const payload = {
            day: selectedDay,
            meal_type: selectedMeal,
        };
        if (recipeId) {
            payload.recipe_id = parseInt(recipeId, 10);
        } else {
            payload.custom_text = customText;
        }

        fetch('/api/planner/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF,
            },
            body: JSON.stringify(payload),
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    safeReload();
                } else {
                    this.disabled = false;
                    this.textContent = 'Save';
                }
            })
            .catch(() => {
                this.disabled = false;
                this.textContent = 'Save';
            });
    });

    /* --- Recipe search filter --- */
    document.getElementById('recipeSearch').addEventListener('input', function () {
        const q = this.value.toLowerCase();
        document.querySelectorAll('#recipeSelect option').forEach(function (opt) {
            if (!opt.value) return;
            opt.hidden = !opt.textContent.toLowerCase().includes(q);
        });
    });

    /* --- Range toggles --- */
    document.querySelectorAll('.range-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentRange = this.dataset.range;
            applyRangeToGrid(currentRange);
            fetchGroceryPreview();
        });
    });

    function applyRangeToGrid(range) {
        const todayIdx = (new Date().getDay() + 6) % 7;
        document.querySelectorAll('.day-slot').forEach(col => {
            const dayIdx = parseInt(col.dataset.day, 10);
            col.style.display = (range === 'day' && dayIdx !== todayIdx) ? 'none' : '';
        });
    }

    /* --- Grocery preview --- */
    function fetchGroceryPreview() {
        const el = document.getElementById('groceryPreview');
        if (!el) return;
        el.innerHTML = '<p class="text-muted-custom" style="font-size:.82rem">Loading…</p>';

        fetch('/api/grocery-list?range=' + currentRange, {
            headers: { 'X-CSRFToken': CSRF },
        })
            .then(r => r.json())
            .then(data => {
                const needed = data.items.filter(i => !i.in_pantry);
                if (needed.length === 0) {
                    el.innerHTML = '<p class="text-muted-custom" style="font-size:.82rem">No ingredients needed.</p>';
                    return;
                }
                el.innerHTML = '<div class="d-flex flex-wrap gap-1">' +
                    needed.slice(0, 12).map(i =>
                        `<span class="chip">${i.name}${i.quantity ? ' <small class="text-muted-custom">' + i.quantity + '</small>' : ''}</span>`
                    ).join('') +
                    (needed.length > 12 ? `<span class="chip" style="opacity:.6">+${needed.length - 12} more</span>` : '') +
                    '</div>' +
                    (data.excluded_count > 0
                        ? `<p class="text-muted-custom mt-2 mb-0" style="font-size:.72rem"><i class="bi bi-box-seam"></i> ${data.excluded_count} item(s) already in pantry</p>`
                        : '');
            })
            .catch(() => {
                el.innerHTML = '<p class="text-coral" style="font-size:.82rem">Could not load preview.</p>';
            });
    }

    applyRangeToGrid(currentRange);
    fetchGroceryPreview();

    /* --- Cross-page Add to Meal Plan modal --- */
    window.openAddToPlanModal = function (recipeId, recipeName) {
        document.getElementById('addToPlanRecipeId').value = recipeId;
        document.getElementById('addToPlanRecipeName').textContent = recipeName;
        new bootstrap.Modal(document.getElementById('addToPlanModal')).show();
    };

    document.getElementById('addToPlanSaveBtn')?.addEventListener('click', function () {
        const recipeId = document.getElementById('addToPlanRecipeId').value;
        const day = document.getElementById('addToPlanDay').value;
        const mealType = document.getElementById('addToPlanMeal').value;

        fetch('/api/planner/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
            body: JSON.stringify({ recipe_id: recipeId, day: day, meal_type: mealType }),
        })
            .then(r => r.json())
            .then(() => {
                bootstrap.Modal.getInstance(document.getElementById('addToPlanModal')).hide();
                if (window.showToast) window.showToast('Added to meal plan');
            })
            .catch(() => {
                if (window.showErrorToast) window.showErrorToast('Could not add to meal plan.');
            });
    });
})();
