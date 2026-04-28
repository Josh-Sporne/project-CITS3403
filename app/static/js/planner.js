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
        modal.hide();
        modalEl.addEventListener('hidden.bs.modal', () => location.reload(), { once: true });
        setTimeout(() => location.reload(), 400);
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

    /* --- Range toggles --- */
    document.querySelectorAll('.range-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentRange = this.dataset.range;
            fetchGroceryPreview();
        });
    });

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

    fetchGroceryPreview();
})();
