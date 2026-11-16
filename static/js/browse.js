// ===== BuildBack Browse JS =====

(function() {
    'use strict';

    const grid = document.getElementById('listingsGrid');
    const skeletonLoaders = document.getElementById('skeletonLoaders');
    const searchForm = document.getElementById('searchForm');
    const categorySelect = document.getElementById('categorySelect');
    const sortSelect = document.getElementById('sortSelect');
    const locationBtn = document.getElementById('locationBtn');
    const clearLocationBtn = document.getElementById('clearLocationBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');

    let debounceTimer = null;
    let userLocation = null;

    // ===== Fetch Listings =====
    async function fetchListings(params = {}) {
        const url = new URL(window.location.href);
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== '') {
                url.searchParams.set(key, params[key]);
            } else {
                url.searchParams.delete(key);
            }
        });

        // Show skeletons
        if (grid) grid.style.display = 'none';
        if (skeletonLoaders) skeletonLoaders.style.display = 'grid';

        try {
            const response = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            if (!response.ok) throw new Error('Network error');

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const newGrid = doc.getElementById('listingsGrid');
            const newPagination = doc.querySelector('.pagination');

            if (newGrid && grid) {
                grid.innerHTML = newGrid.innerHTML;
                grid.style.display = 'grid';
            }
            if (skeletonLoaders) skeletonLoaders.style.display = 'none';

            // Update pagination
            const paginationContainer = document.querySelector('.pagination');
            if (newPagination && paginationContainer) {
                paginationContainer.outerHTML = newPagination.outerHTML;
            } else if (newPagination && !paginationContainer) {
                grid?.insertAdjacentHTML('afterend', newPagination.outerHTML);
            } else if (!newPagination && paginationContainer) {
                paginationContainer.remove();
            }

            // Update URL without reload
            window.history.pushState({}, '', url);

            // Re-init reveal animations
            if (window.BuildBack && window.BuildBack.initReveal) {
                window.BuildBack.initReveal();
            } else {
                // Fallback: simple reveal
                document.querySelectorAll('.reveal').forEach(el => el.classList.add('revealed'));
            }

        } catch (error) {
            console.error('Fetch error:', error);
            if (skeletonLoaders) skeletonLoaders.style.display = 'none';
            if (grid) {
                grid.style.display = 'grid';
                grid.innerHTML = `
                    <div class="empty-state" style="grid-column: 1/-1;">
                        <svg class="empty-state__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
                        <h3 class="empty-state__title">Failed to load</h3>
                        <p class="empty-state__desc">Please check your connection and try again.</p>
                        <button type="button" class="btn btn--primary" onclick="window.location.reload()">Retry</button>
                    </div>
                `;
            }
        }
    }

    // ===== Debounced Search =====
    function debouncedFetch(params) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => fetchListings(params), 300);
    }

    // ===== Event Listeners =====
    // Search input
    if (searchForm) {
        const input = searchForm.querySelector('input[name="q"]');
        input?.addEventListener('input', (e) => {
            debouncedFetch({ q: e.target.value, page: 1 });
        });
    }

    // Category filter
    categorySelect?.addEventListener('change', (e) => {
        fetchListings({ category: e.target.value, page: 1 });
    });

    // Sort
    sortSelect?.addEventListener('change', (e) => {
        fetchListings({ sort: e.target.value });
    });

    // Location
    locationBtn?.addEventListener('click', () => {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            return;
        }

        locationBtn.disabled = true;
        locationBtn.innerHTML = `
            <svg class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"/><path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="1"/></svg>
            Locating...
        `;

        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                fetchListings({ lat: userLocation.lat, lng: userLocation.lng, page: 1 });
                locationBtn.style.display = 'none';
                clearLocationBtn.style.display = 'inline-flex';
            },
            (error) => {
                alert('Unable to retrieve your location. Please select manually on the map.');
                locationBtn.disabled = false;
                locationBtn.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/></svg>
                    Use My Location
                `;
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    });

    clearLocationBtn?.addEventListener('click', () => {
        userLocation = null;
        fetchListings({ page: 1 });
        locationBtn.style.display = 'inline-flex';
        clearLocationBtn.style.display = 'none';
    });

    // Clear filters
    clearFiltersBtn?.addEventListener('click', () => {
        fetchListings({ page: 1 });
        if (searchForm) searchForm.querySelector('input[name="q"]').value = '';
        if (categorySelect) categorySelect.value = '';
        if (sortSelect) sortSelect.value = '-created_at';
    });

    // Pagination links (delegated)
    document.addEventListener('click', (e) => {
        const link = e.target.closest('.pagination__link[href]');
        if (link) {
            e.preventDefault();
            const url = new URL(link.href);
            const params = {};
            url.searchParams.forEach((v, k) => params[k] = v);
            fetchListings(params);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    // Add spinner animation
    const style = document.createElement('style');
    style.textContent = `@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`;
    document.head.appendChild(style);

})();