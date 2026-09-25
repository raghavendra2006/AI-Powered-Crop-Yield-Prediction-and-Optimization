// Leaflet.js Map Initialization
document.addEventListener('DOMContentLoaded', function () {
    const mapEl = document.getElementById('map');
    if (!mapEl) return;

    // Default center: India
    const map = L.map('map').setView([20.5937, 78.9629], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
    }).addTo(map);

    let marker = null;
    const latInput = document.getElementById('latitude');
    const lngInput = document.getElementById('longitude');
    const locationLabel = document.getElementById('location-label');

    // Custom marker icon
    const cropIcon = L.divIcon({
        className: 'custom-marker',
        html: '<div class="marker-pin"><span>📍</span></div>',
        iconSize: [40, 40],
        iconAnchor: [20, 40],
    });

    map.on('click', function (e) {
        const { lat, lng } = e.latlng;

        if (marker) {
            map.removeLayer(marker);
        }

        marker = L.marker([lat, lng], { icon: cropIcon }).addTo(map);
        marker.bindPopup(
            `<b>Selected Location</b><br>Lat: ${lat.toFixed(4)}<br>Lng: ${lng.toFixed(4)}`
        ).openPopup();

        if (latInput) latInput.value = lat.toFixed(6);
        if (lngInput) lngInput.value = lng.toFixed(6);

        if (locationLabel) {
            locationLabel.textContent = `📍 ${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E`;
            locationLabel.classList.add('selected');
        }
    });

    // Try to get user's current location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (pos) {
            map.setView([pos.coords.latitude, pos.coords.longitude], 10);
        });
    }
});
