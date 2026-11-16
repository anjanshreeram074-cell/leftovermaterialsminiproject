// ===== BuildBack Sell Form JS =====

(function() {
    'use strict';

    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    const uploadPreview = document.getElementById('uploadPreview');
    const imageUrlsInput = document.getElementById('imageUrls');
    const addressInput = document.getElementById('addressInput');
    const latInput = document.getElementById('id_lat');
    const lngInput = document.getElementById('id_lng');
    const addressHidden = document.getElementById('id_address');
    const gpsBtn = document.getElementById('gpsBtn');
    const clearLocationBtn = document.getElementById('clearLocationBtn');
    const locationMapEl = document.getElementById('locationMap');
    const sellForm = document.getElementById('sellForm');
    const submitBtn = document.getElementById('submitBtn');

    let map = null;
    let marker = null;
    let autocomplete = null;
    let images = []; // Array of {file, previewUrl, cloudinaryUrl}

    const MAX_IMAGES = 5;
    const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
    const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

    // ===== Image Upload =====
    function updateImageUrls() {
        imageUrlsInput.value = images.map(img => img.cloudinaryUrl || img.previewUrl).join(',');
    }

    function renderPreviews() {
        uploadPreview.innerHTML = '';
        images.forEach((img, index) => {
            const div = document.createElement('div');
            div.className = 'upload-preview__item';
            div.innerHTML = `
                <img src="${img.previewUrl}" alt="Image ${index + 1}" loading="lazy">
                <button type="button" class="upload-preview__remove" aria-label="Remove image" data-index="${index}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
                ${index === 0 ? '<span style="position:absolute;top:4px;left:4px;background:var(--gold);color:var(--bg);font-size:0.6rem;padding:0.1rem 0.3rem;border-radius:4px;">MAIN</span>' : ''}
            `;
            uploadPreview.appendChild(div);
        });

        // Remove handlers
        uploadPreview.querySelectorAll('.upload-preview__remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const idx = parseInt(btn.dataset.index);
                images.splice(idx, 1);
                renderPreviews();
                updateImageUrls();
            });
        });
    }

    function handleFiles(files) {
        const validFiles = Array.from(files).filter(file => {
            if (!ALLOWED_TYPES.includes(file.type)) {
                BuildBack.toast(`${file.name}: Invalid file type. Use JPG, PNG, or WebP.`, 'error');
                return false;
            }
            if (file.size > MAX_FILE_SIZE) {
                BuildBack.toast(`${file.name}: File too large. Max 5MB.`, 'error');
                return false;
            }
            return true;
        });

        if (images.length + validFiles.length > MAX_IMAGES) {
            BuildBack.toast(`Maximum ${MAX_IMAGES} images allowed.`, 'error');
            return;
        }

        validFiles.forEach(file => {
            const reader = new FileReader();
            reader.onload = (e) => {
                images.push({
                    file: file,
                    previewUrl: e.target.result,
                    cloudinaryUrl: null // Will be replaced after Cloudinary upload
                });
                renderPreviews();
                updateImageUrls();
            };
            reader.readAsDataURL(file);
        });
    }

    // Upload area events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => uploadArea.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('drag-over'), false);
    });

    uploadArea.addEventListener('drop', (e) => {
        handleFiles(e.dataTransfer.files);
    }, false);

    uploadArea.addEventListener('click', () => imageInput.click());
    uploadArea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); imageInput.click(); }
    });

    imageInput.addEventListener('change', (e) => handleFiles(e.target.files));

    // ===== Google Maps Location Picker =====
    function initMap() {
        if (typeof google === 'undefined' || !google.maps) {
            setTimeout(initMap, 100);
            return;
        }

        const defaultCenter = { lat: 28.6139, lng: 77.2090 }; // Delhi default
        const savedLat = parseFloat(latInput.value);
        const savedLng = parseFloat(lngInput.value);

        const center = (!isNaN(savedLat) && !isNaN(savedLng)) ? { lat: savedLat, lng: savedLng } : defaultCenter;

        map = new google.maps.Map(locationMapEl, {
            center: center,
            zoom: 14,
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

        marker = new google.maps.Marker({
            position: center,
            map: map,
            draggable: true,
            title: 'Drag to set location'
        });

        // Placeholder if no saved location
        if (isNaN(savedLat) || isNaN(savedLng)) {
            marker.setVisible(false);
        }

        // Update inputs on drag
        marker.addListener('dragend', (e) => {
            updateLocationInputs(e.latLng.lat(), e.latLng.lng());
        });

        // Click on map to place pin
        map.addListener('click', (e) => {
            marker.setPosition(e.latLng);
            marker.setVisible(true);
            updateLocationInputs(e.latLng.lat(), e.latLng.lng());
        });

        // Autocomplete
        autocomplete = new google.maps.places.Autocomplete(addressInput, {
            fields: ['geometry', 'formatted_address', 'name'],
            types: ['geocode', 'establishment']
        });

        autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();
            if (!place.geometry) return;

            const lat = place.geometry.location.lat();
            const lng = place.geometry.location.lng();

            map.setCenter({ lat, lng });
            map.setZoom(16);
            marker.setPosition({ lat, lng });
            marker.setVisible(true);
            updateLocationInputs(lat, lng, place.formatted_address);
        });

        // GPS Button
        gpsBtn?.addEventListener('click', () => {
            if (!navigator.geolocation) {
                BuildBack.toast('Geolocation not supported', 'error');
                return;
            }

            gpsBtn.disabled = true;
            gpsBtn.innerHTML = '<svg class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"/><path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="1"/></svg> Locating...';

            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const lat = pos.coords.latitude;
                    const lng = pos.coords.longitude;
                    map.setCenter({ lat, lng });
                    map.setZoom(16);
                    marker.setPosition({ lat, lng });
                    marker.setVisible(true);
                    updateLocationInputs(lat, lng);
                    reverseGeocode(lat, lng);
                    gpsBtn.disabled = false;
                    gpsBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/></svg> Use My Location';
                },
                (err) => {
                    BuildBack.toast('Unable to get location. Please select manually.', 'error');
                    gpsBtn.disabled = false;
                    gpsBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/></svg> Use My Location';
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        });

        // Clear location
        clearLocationBtn?.addEventListener('click', () => {
            latInput.value = '';
            lngInput.value = '';
            addressHidden.value = '';
            addressInput.value = '';
            marker.setVisible(false);
        });
    }

    function updateLocationInputs(lat, lng, address = '') {
        latInput.value = lat.toFixed(6);
        lngInput.value = lng.toFixed(6);
        if (address) addressHidden.value = address;
    }

    function reverseGeocode(lat, lng) {
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ location: { lat, lng } }, (results, status) => {
            if (status === 'OK' && results[0]) {
                addressHidden.value = results[0].formatted_address;
                addressInput.value = results[0].formatted_address;
            }
        });
    }

    // Initialize map when Google Maps loads
    window.initSellMap = initMap;

    // ===== Form Validation & Submit =====
    sellForm?.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Validate images
        if (images.length === 0) {
            BuildBack.toast('Please add at least one image', 'error');
            uploadArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
            uploadArea.style.boxShadow = '0 0 0 3px var(--danger)';
            setTimeout(() => uploadArea.style.boxShadow = '', 3000);
            return;
        }

        // Validate location
        if (!latInput.value || !lngInput.value) {
            BuildBack.toast('Please select a location on the map', 'error');
            locationMapEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }

        // Validate required fields
        const requiredFields = sellForm.querySelectorAll('[required]');
        let hasError = false;
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.closest('.form-group')?.classList.add('has-error');
                hasError = true;
            } else {
                field.closest('.form-group')?.classList.remove('has-error');
            }
        });

        if (hasError) {
            BuildBack.toast('Please fill all required fields', 'error');
            return;
        }

        // Show loading
        submitBtn.disabled = true;
        submitBtn.querySelector('.btn-text').style.display = 'none';
        submitBtn.querySelector('.btn-loading').style.display = 'inline-flex';

        // TODO: Upload images to Cloudinary here before submit
        // For now, using preview URLs
        updateImageUrls();

        // Submit form
        sellForm.submit();
    });

    // Remove error on input
    sellForm?.querySelectorAll('input, select').forEach(field => {
        field.addEventListener('input', () => {
            field.closest('.form-group')?.classList.remove('has-error');
        });
    });

})();