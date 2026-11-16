// ===== BuildBack Main JS =====

(function() {
    'use strict';

    // ===== Header Scroll Effect =====
    const header = document.getElementById('header');
    let lastScrollY = window.scrollY;

    function onScroll() {
        const currentScrollY = window.scrollY;
        if (currentScrollY > 20) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        lastScrollY = currentScrollY;
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // ===== Mobile Menu =====
    const hamburger = document.getElementById('hamburger');
    const mobileMenu = document.getElementById('mobileMenu');

    if (hamburger && mobileMenu) {
        hamburger.addEventListener('click', () => {
            const isOpen = mobileMenu.classList.toggle('open');
            hamburger.setAttribute('aria-expanded', isOpen);
            document.body.style.overflow = isOpen ? 'hidden' : '';
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && mobileMenu.classList.contains('open')) {
                mobileMenu.classList.remove('open');
                hamburger.setAttribute('aria-expanded', 'false');
                document.body.style.overflow = '';
                hamburger.focus();
            }
        });

        // Close on link click
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.remove('open');
                hamburger.setAttribute('aria-expanded', 'false');
                document.body.style.overflow = '';
            });
        });
    }

    // ===== User Dropdown =====
    const userMenu = document.getElementById('userMenu');
    if (userMenu) {
        const btn = userMenu.querySelector('.header__user-btn');
        const dropdown = userMenu.querySelector('.header__user-dropdown');

        btn?.addEventListener('click', (e) => {
            e.stopPropagation();
            userMenu.classList.toggle('open');
            btn.setAttribute('aria-expanded', userMenu.classList.contains('open'));
        });

        document.addEventListener('click', (e) => {
            if (!userMenu.contains(e.target)) {
                userMenu.classList.remove('open');
                btn?.setAttribute('aria-expanded', 'false');
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && userMenu.classList.contains('open')) {
                userMenu.classList.remove('open');
                btn?.setAttribute('aria-expanded', 'false');
                btn?.focus();
            }
        });
    }

    // ===== Count-Up Animation =====
    function countUp(el, target, duration = 2000) {
        const start = 0;
        const startTime = performance.now();
        const isFloat = target % 1 !== 0;

        function animate(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            const current = start + (target - start) * eased;
            el.textContent = isFloat ? current.toFixed(1) : Math.floor(current);
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                el.textContent = target;
            }
        }
        requestAnimationFrame(animate);
    }

    function initCountUp() {
        const statValues = document.querySelectorAll('.stat__value[data-target]');
        if (!statValues.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseFloat(el.dataset.target);
                    countUp(el, target);
                    observer.unobserve(el);
                }
            });
        }, { threshold: 0.5 });

        statValues.forEach(el => observer.observe(el));
    }

    // ===== Reveal on Scroll =====
    function initReveal() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (prefersReducedMotion) {
            document.querySelectorAll('.reveal').forEach(el => el.classList.add('revealed'));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

        document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    }

    // ===== Initialize on DOM Ready =====
    document.addEventListener('DOMContentLoaded', () => {
        initCountUp();
        initReveal();
    });

    // ===== Utility Functions =====
    window.BuildBack = {
        // Format currency
        formatCurrency: (amount) => {
            return new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                maximumFractionDigits: 0
            }).format(amount);
        },
        // Format number with commas
        formatNumber: (num) => {
            return new Intl.NumberFormat('en-IN').format(num);
        },
        // Show toast notification
        toast: (message, type = 'info') => {
            const toast = document.createElement('div');
            toast.className = `toast toast--${type}`;
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed; bottom: 2rem; right: 2rem; z-index: 1000;
                padding: 1rem 1.5rem; border-radius: var(--radius);
                background: var(--card); border: 1px solid var(--line);
                box-shadow: var(--shadow); animation: slideIn 0.3s ease-out;
            `;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease-in forwards';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
    };

    // Add toast animations dynamically
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn { from { opacity: 0; transform: translateX(100%); } to { opacity: 1; transform: translateX(0); } }
        @keyframes slideOut { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(100%); } }
    `;
    document.head.appendChild(style);

})();