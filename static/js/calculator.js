// ===== BuildBack Calculator JS =====

(function() {
    'use strict';

    const calcBtn = document.getElementById('calcBtn');
    const calcResult = document.getElementById('calcResult');
    const calcEmpty = document.getElementById('calcEmpty');
    const calcError = document.getElementById('calcError');

    const inputs = {
        quantity: document.getElementById('calcQuantity'),
        vehicle: document.getElementById('calcVehicle'),
        rate: document.getElementById('calcRate'),
        minFare: document.getElementById('calcMinFare'),
        newPrice: document.getElementById('calcNewPrice')
    };

    const resultEls = {
        distance: document.getElementById('resDistance'),
        transport: document.getElementById('resTransport'),
        material: document.getElementById('resMaterial'),
        total: document.getElementById('resTotal'),
        savings: document.getElementById('resSavings'),
        savingsRow: document.getElementById('resSavingsRow'),
        verdict: document.getElementById('resVerdict')
    };

    // Get material data from page
    const materialData = {
        sellingPrice: parseFloat(document.querySelector('.listing-card__price')?.textContent?.replace(/[^0-9.]/g, '') || '0'),
        distanceKm: parseFloat(document.querySelector('[data-distance]')?.dataset?.distance || '0'),
        location: null
    };

    // Try to get location from map
    let sellerLocation = null;
    let buyerLocation = null;

    // Vehicle defaults
    const vehicleDefaults = {
        bike: { rate: 8, minFare: 50 },
        auto: { rate: 12, minFare: 80 },
        'mini-truck': { rate: 18, minFare: 150 }
    };

    // Update rate/min fare when vehicle changes
    inputs.vehicle.addEventListener('change', () => {
        const val = inputs.vehicle.value;
        if (vehicleDefaults[val]) {
            inputs.rate.value = vehicleDefaults[val].rate;
            inputs.minFare.value = vehicleDefaults[val].minFare;
        }
    });

    // Main calculate function
    async function calculate() {
        // Validate
        const quantity = parseFloat(inputs.quantity.value);
        const rate = parseFloat(inputs.rate.value);
        const minFare = parseFloat(inputs.minFare.value);
        const newPrice = inputs.newPrice.value ? parseFloat(inputs.newPrice.value) : null;

        if (!quantity || quantity <= 0) {
            showError('Please enter a valid quantity');
            return;
        }
        if (isNaN(rate) || rate < 0) {
            showError('Please enter a valid rate per km');
            return;
        }
        if (isNaN(minFare) || minFare < 0) {
            showError('Please enter a valid minimum fare');
            return;
        }

        // Get distance
        let distanceKm = materialData.distanceKm;

        // If we have both locations, fetch road distance
        if (sellerLocation && buyerLocation) {
            try {
                const response = await fetch('/calculator/estimate/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': window.CSRF_TOKEN
                    },
                    body: JSON.stringify({
                        origin_lat: buyerLocation.lat,
                        origin_lng: buyerLocation.lng,
                        dest_lat: sellerLocation.lat,
                        dest_lng: sellerLocation.lng,
                        quantity: quantity,
                        vehicle_rate: rate,
                        min_fare: minFare,
                        selling_price: materialData.sellingPrice,
                        new_market_price: newPrice || materialData.sellingPrice * 1.2 // Estimate
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    displayResults(data);
                    return;
                }
            } catch (e) {
                console.error('Calculator API error:', e);
            }
        }

        // Fallback: use saved distance or show error
        if (!distanceKm) {
            showError('Unable to calculate distance. Please ensure location is set.');
            return;
        }

        // Local calculation
        const transport = Math.max(minFare, distanceKm * rate);
        const materialCost = quantity * materialData.sellingPrice;
        const total = materialCost + transport;

        let savings = 0;
        let savingsPct = 0;
        if (newPrice) {
            const newTotal = quantity * newPrice;
            savings = newTotal - total;
            savingsPct = newTotal > 0 ? (savings / newTotal) * 100 : 0;
        }

        displayResults({
            distance_km: distanceKm,
            transport_charge: transport,
            material_cost: materialCost,
            total_purchase_cost: total,
            savings_amount: savings,
            savings_percentage: savingsPct,
            verdict: savings > 0 ? "Worth buying" : "Not worth it",
            is_worth_it: savings > 0
        });
    }

    function displayResults(data) {
        resultEls.distance.textContent = `${data.distance_km.toFixed(1)} km`;
        resultEls.transport.textContent = `₹${data.transport_charge.toFixed(0)}`;
        resultEls.material.textContent = `₹${data.material_cost.toFixed(0)}`;
        resultEls.total.textContent = `₹${data.total_purchase_cost.toFixed(0)}`;

        if (data.savings_amount !== undefined && data.savings_amount !== 0) {
            resultEls.savings.textContent = `${data.savings_amount > 0 ? '+' : ''}₹${data.savings_amount.toFixed(0)} (${data.savings_percentage.toFixed(1)}%)`;
            resultEls.savingsRow.style.display = 'flex';
            resultEls.savingsRow.classList.toggle('negative', data.savings_amount < 0);
        } else {
            resultEls.savingsRow.style.display = 'none';
        }

        resultEls.verdict.textContent = data.verdict;
        resultEls.verdict.className = 'badge badge--verdict ' + (data.is_worth_it ? 'worth' : 'not-worth');

        calcResult.classList.add('show');
        calcEmpty.style.display = 'none';
        hideError();
    }

    function showError(msg) {
        calcError.textContent = msg;
        calcError.style.display = 'block';
        calcResult.classList.remove('show');
    }

    function hideError() {
        calcError.style.display = 'none';
    }

    calcBtn?.addEventListener('click', () => {
        calcBtn.disabled = true;
        calcBtn.querySelector('.btn-text').style.display = 'none';
        calcBtn.querySelector('.btn-loading').style.display = 'inline-flex';
        calculate().finally(() => {
            calcBtn.disabled = false;
            calcBtn.querySelector('.btn-text').style.display = 'inline';
            calcBtn.querySelector('.btn-loading').style.display = 'none';
        });
    });

    // Enter key on inputs
    Object.values(inputs).forEach(input => {
        input?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') calculate();
        });
    });

    // Expose for maps.js to set locations
    window.BuildBackCalculator = {
        setSellerLocation: (loc) => { sellerLocation = loc; },
        setBuyerLocation: (loc) => { buyerLocation = loc; },
        setMaterialPrice: (price) => { materialData.sellingPrice = price; },
        setDistance: (dist) => { materialData.distanceKm = dist; }
    };

})();