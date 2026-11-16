// ===== BuildBack Maps JS =====

(function() {
    'use strict';

    // Detail page map
    const detailMapEl = document.getElementById('detailMap');
    let detailMap = null;
    let detailMarker = null;

    // Init detail map
    function initDetailMap() {
        if (!detailMapEl) return;
        if (typeof google === 'undefined' || !google.maps) {
            setTimeout(initDetailMap, 100);
            return;
        }

        const lat = parseFloat(detailMapEl.dataset.lat);
        const lng = parseFloat(detailMapEl.dataset.lng);
        const address = detailMapEl.dataset.address;

        if (isNaN(lat) || isNaN(lng)) return;

        const position = { lat, lng };

        detailMap = new google.maps.Map(detailMapEl, {
            center: position,
            zoom: 15,
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
            styles: [
                { elementType: 'geometry', stylers: [{ color: '#151a22' }] },
                { elementType: 'labels.text.stroke', stylers: [{ color: '#0d1016' }] },
                { elementType: 'labels.text.fill', stylers: [{ color: '#8b8f98' }] },
                { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#2a2f3a' }] },
                { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#3a3f4a' }] },
                { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#8b8f98' }] },
                { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0d1016' }] },
                { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#8b8f98' }] }
            ]
        });

        detailMarker = new google.maps.Marker({
            position: position,
            map: detailMap,
            title: address || 'Material Location'
        });

        // Set seller location for calculator
        if (window.BuildBackCalculator) {
            window.BuildBackCalculator.setSellerLocation({ lat, lng });
        }

        // Try to get buyer location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const buyerPos = { lat: pos.coords.latitude, lng: pos.coords.longitude };
                    if (window.BuildBackCalculator) {
                        window.BuildBackCalculator.setBuyerLocation(buyerPos);
                    }
                    // Optionally show buyer marker
                    new google.maps.Marker({
                        position: buyerPos,
                        map: detailMap,
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            scale: 8,
                            fillColor: '#b98a52',
                            fillOpacity: 1,
                            strokeColor: '#0d1016',
                            strokeWeight: 2
                        },
                        title: 'Your Location'
                    });
                },
                () => {} // Silent fail
            );
        }
    }

    // Initialize when Google Maps loads
    window.initDetailMap = initDetailMap;

    // Gallery thumbnail switching
    document.addEventListener('DOMContentLoaded', () => {
        const thumbs = document.querySelectorAll('.gallery__thumb');
        const mainImg = document.getElementById('mainImg');

        thumbs.forEach(thumb => {
            thumb.addEventListener('click', () => {
                const src = thumb.dataset.src;
                if (src && mainImg) {
                    mainImg.src = src;
                    mainImg.alt = thumb.alt || 'Material image';

                    thumbs.forEach(t => {
                        t.classList.remove('active');
                        t.setAttribute('aria-pressed', 'false');
                    });
                    thumb.classList.add('active');
                    thumb.setAttribute('aria-pressed', 'true');
                }
            });

            thumb.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    thumb.click();
                }
            });
        });
    });

})();