/* Plate Theory — Shared Utilities */

function escapeHtml(s) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(s ?? ''));
  return d.innerHTML;
}
window.escapeHtml = escapeHtml;

function showErrorToast(message) {
  const el = document.createElement('div');
  el.className = 'alert alert-danger position-fixed bottom-0 end-0 m-3';
  el.style.zIndex = 9999;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}
window.showErrorToast = showErrorToast;

function toggleFollow(username, btn) {
  const isFollowing = btn.dataset.following === 'true';
  fetch(`/user/${username}/follow`, {
    method: 'POST',
    headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      btn.dataset.following = !isFollowing;
      btn.textContent = isFollowing ? 'Follow' : 'Unfollow';
    }
  })
  .catch(() => showErrorToast('Could not update follow status.'));
}
window.toggleFollow = toggleFollow;

async function apiCall(url, method = 'GET', data = null) {
    const opts = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
        }
    };
    if (data && method !== 'GET') opts.body = JSON.stringify(data);
    const resp = await fetch(url, opts);
    if (!resp.ok) {
        const text = await resp.text();
        throw new Error(text || resp.statusText);
    }
    return resp.json();
}

function autoDismissAlerts() {
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
}

function confirmAction(title, message, callback) {
    if (confirm(`${title}\n\n${message}`)) {
        callback();
    }
}

function showSpinner(container) {
    if (!container || container.querySelector('.pt-spinner-overlay')) return;
    const overlay = document.createElement('div');
    overlay.className = 'pt-spinner-overlay';
    Object.assign(overlay.style, {
        position: 'absolute',
        inset: '0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(15, 14, 20, 0.7)',
        borderRadius: 'inherit',
        zIndex: '10'
    });
    overlay.innerHTML = '<div class="spinner-border text-light" role="status"><span class="visually-hidden">Loading…</span></div>';

    const pos = getComputedStyle(container).position;
    if (pos === 'static') container.style.position = 'relative';

    container.appendChild(overlay);
}

function hideSpinner(container) {
    if (!container) return;
    const overlay = container.querySelector('.pt-spinner-overlay');
    if (overlay) overlay.remove();
}

/* ── Toast helpers ──
 * Shows a small floating message bottom-right that fades after ~2.5s.
 * Use showToast(msg) for success/info (mint).
 * Use showErrorToast(msg) for failures (coral).
 */
function _ensureToastContainer() {
    let container = document.getElementById('pt-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'pt-toast-container';
        document.body.appendChild(container);
    }
    return container;
}

function showToast(message, variant) {
    const container = _ensureToastContainer();
    const toast = document.createElement('div');
    toast.className = 'pt-toast pt-toast--' + (variant === 'error' ? 'error' : 'success');
    toast.setAttribute('role', 'status');  // a11y: screen readers announce it
    toast.textContent = message;
    container.appendChild(toast);

    // Trigger CSS transition by adding .show on the next frame.
    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);  // wait for fade-out before removing
    }, 2500);
}

function showErrorToast(message) {
    showToast(message, 'error');
}

// Expose globally so other scripts (planner.js, detail.html, etc.) can use them.
window.showToast = showToast;
window.showErrorToast = showErrorToast;

/* ── Scroll Reveal ── */
function initScrollReveal() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const targets = document.querySelectorAll(
        '.pt-card, .card, .pt-panel, section, .reveal, .animate-fade'
    );

    // Group siblings so stagger index resets per parent container
    const parentMap = new Map();
    targets.forEach(el => {
        const key = el.parentElement;
        if (!parentMap.has(key)) parentMap.set(key, []);
        parentMap.get(key).push(el);
    });
    parentMap.forEach(group => {
        group.forEach((el, i) => {
            el.style.setProperty('--reveal-index', i);
        });
    });

    targets.forEach(el => el.classList.add('reveal'));

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    targets.forEach(el => observer.observe(el));
}

/* ── Scroll-aware Navbar ── */
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    const onScroll = () => {
        navbar.classList.toggle('scrolled', window.scrollY > 48);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
}

/* ── Top Progress Bar ── */
(function initProgressBar() {
    const bar = document.createElement('div');
    bar.id = 'pt-progress';
    document.body.prepend(bar);

    let width = 0;
    let raf;

    function tick() {
        width = Math.min(width + (100 - width) * 0.08, 92);
        bar.style.width = width + '%';
        raf = requestAnimationFrame(tick);
    }

    // Start on page unload (navigation)
    document.addEventListener('click', e => {
        const a = e.target.closest('a[href]');
        if (!a) return;
        const href = a.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('mailto') ||
            href.startsWith('javascript') || a.target === '_blank') return;
        width = 15;
        bar.style.width = '15%';
        bar.classList.remove('pt-progress-done');
        raf = requestAnimationFrame(tick);
    });

    // Complete on DOMContentLoaded
    window.addEventListener('DOMContentLoaded', () => {
        cancelAnimationFrame(raf);
        bar.style.width = '100%';
        setTimeout(() => bar.classList.add('pt-progress-done'), 200);
    });
})();

/* ── Grocery strikethrough via class toggle ── */
function initGroceryCheck() {
    document.addEventListener('change', e => {
        if (e.target.type !== 'checkbox') return;
        const row = e.target.closest('.grocery-row');
        if (row) row.classList.toggle('checked', e.target.checked);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    autoDismissAlerts();
    initScrollReveal();
    initNavbarScroll();
    initGroceryCheck();
});
