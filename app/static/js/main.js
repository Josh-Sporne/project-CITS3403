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

/* ─────────────────────────────────────────────
   SCROLL REVEAL
   - Only animates elements NOT already in viewport
   - Exposes window.revealElements(nodeList) so
     dynamically added cards (Load More, planner)
     can be registered after the fact
───────────────────────────────────────────── */
const _revealObserver = (() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return { observe: () => {} };
    }
    return new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;
            el.classList.add('visible');
            _revealObserver.unobserve(el);
        });
    }, { threshold: 0.07, rootMargin: '0px 0px -32px 0px' });
})();

function revealElements(nodeList) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const viewport = window.innerHeight;

    // Group by parent to stagger siblings independently
    const parentMap = new Map();
    Array.from(nodeList).forEach(el => {
        const key = el.parentElement || document.body;
        if (!parentMap.has(key)) parentMap.set(key, []);
        parentMap.get(key).push(el);
    });

    parentMap.forEach(group => {
        let staggerIdx = 0;
        group.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.top < viewport - 20) {
                // Already visible on load — show instantly, no animation
                el.classList.add('reveal', 'visible');
            } else {
                el.classList.add('reveal');
                el.style.setProperty('--reveal-index', staggerIdx++);
                _revealObserver.observe(el);
            }
        });
    });
}
window.revealElements = revealElements;

function initScrollReveal() {
    revealElements(document.querySelectorAll(
        '.pt-card, .card:not(.navbar *), .pt-panel, .animate-fade'
    ));
}

/* ─────────────────────────────────────────────
   SCROLL-AWARE NAVBAR BLUR
───────────────────────────────────────────── */
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    const onScroll = () => navbar.classList.toggle('scrolled', window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
}

/* ─────────────────────────────────────────────
   TOP PAGE LOAD PROGRESS BAR
───────────────────────────────────────────── */
(function initProgressBar() {
    const bar = document.createElement('div');
    bar.id = 'pt-progress';
    document.body.prepend(bar);
    let raf, width = 0;

    function tick() {
        width = Math.min(width + (100 - width) * 0.07, 90);
        bar.style.width = width + '%';
        raf = requestAnimationFrame(tick);
    }

    document.addEventListener('click', e => {
        const a = e.target.closest('a[href]');
        if (!a) return;
        const href = a.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('mailto') ||
            href.startsWith('javascript') || a.target === '_blank') return;
        width = 15;
        bar.style.opacity = '1';
        bar.style.width = '15%';
        bar.classList.remove('pt-progress-done');
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(tick);
    });

    window.addEventListener('DOMContentLoaded', () => {
        cancelAnimationFrame(raf);
        bar.style.width = '100%';
        setTimeout(() => { bar.classList.add('pt-progress-done'); }, 180);
    });
})();

/* ─────────────────────────────────────────────
   MAGNETIC BUTTON EFFECT — desktop only
───────────────────────────────────────────── */
function initMagneticButtons() {
    if (!window.matchMedia('(pointer: fine)').matches) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    function attachMagnetic(el) {
        el.addEventListener('mousemove', e => {
            const rect = el.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top  + rect.height / 2;
            const dx = (e.clientX - cx) * 0.28;
            const dy = (e.clientY - cy) * 0.28;
            el.style.transform = `translate(${dx}px, ${dy}px) scale(1.04)`;
        });
        el.addEventListener('mouseleave', () => {
            el.style.transform = '';
        });
    }

    // Attach to primary action buttons — not every btn
    document.querySelectorAll('.btn-mint, .btn-outline-mint, .btn-coral').forEach(attachMagnetic);

    // Re-attach when new buttons appear (e.g. pantry results)
    const mo = new MutationObserver(muts => {
        muts.forEach(m => m.addedNodes.forEach(n => {
            if (n.nodeType !== 1) return;
            if (n.matches?.('.btn-mint, .btn-outline-mint, .btn-coral')) attachMagnetic(n);
            n.querySelectorAll?.('.btn-mint, .btn-outline-mint, .btn-coral').forEach(attachMagnetic);
        }));
    });
    mo.observe(document.body, { childList: true, subtree: true });
}

/* ─────────────────────────────────────────────
   HERO WORD-BY-WORD REVEAL
   Splits text into word spans with stagger
───────────────────────────────────────────── */
function initHeroReveal() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    document.querySelectorAll('[data-word-reveal]').forEach(el => {
        const words = el.textContent.trim().split(/\s+/);
        el.innerHTML = words.map((w, i) =>
            `<span class="word-reveal-wrap"><span class="word-reveal-inner" style="--wi:${i}">${w}</span></span>`
        ).join(' ');
        el.classList.add('words-ready');
    });
}

/* ─────────────────────────────────────────────
   GROCERY STRIKETHROUGH
───────────────────────────────────────────── */
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
    initMagneticButtons();
    initHeroReveal();
    initGroceryCheck();
});
