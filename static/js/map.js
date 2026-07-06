document.addEventListener("DOMContentLoaded", function () {
    const mapContainer = document.getElementById("map");
    if (!mapContainer) return; // Only run on pages with the map

    // Grab form elements if they exist
    const stateSelect = document.getElementById("field-State_Name");
    const districtSelect = document.getElementById("field-District_Name");
    
    const districtPickerContainer = document.getElementById("district-picker-container");
    const selectedStateTitle = document.getElementById("selected-state-title");
    const districtGrid = document.getElementById("district-grid");

    let geoJsonLayer;
    let selectedLayer;
    let indiaGeoJson = null;
    let statesDistrictsData = null;

    // Initialize Leaflet Map centered on India
    const map = L.map("map", {
        center: [22.9734, 78.6569],
        zoom: 4,
        zoomControl: true,
        attributionControl: false
    });

    // CartoDB Dark Matter Tile Layer (fits premium glassmorphic dark theme)
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 18
    }).addTo(map);

    // Styling constants
    const defaultStyle = {
        color: "rgba(157, 78, 221, 0.4)", // Translucent purple border
        weight: 1.5,
        fillColor: "rgba(157, 78, 221, 0.05)",
        fillOpacity: 0.2
    };

    const hoverStyle = {
        color: "#00F0FF", // Electric Cyan border
        weight: 2,
        fillColor: "rgba(0, 240, 255, 0.15)",
        fillOpacity: 0.4
    };

    const selectedStyle = {
        color: "#00F0FF", // Electric Cyan
        weight: 3,
        fillColor: "rgba(0, 240, 255, 0.25)",
        fillOpacity: 0.6
    };

    // Load GeoJSON and State-District data in parallel
    Promise.all([
        fetch("/static/js/india.json").then(res => res.json()),
        fetch("/static/js/states-and-districts.json").then(res => res.json())
    ]).then(([geoJson, districtsData]) => {
        indiaGeoJson = geoJson;
        statesDistrictsData = districtsData;

        // 1. Populate the state dropdown with ALL states from the JSON
        populateStateDropdown();

        // 2. Render GeoJSON state boundaries on Leaflet map
        renderMapLayers();

        // 3. Set up event listeners for form dropdown synchronization
        setupDropdownSync();
    }).catch(err => {
        console.error("Error loading geographic data files:", err);
    });

    // Populate state dropdown with all states alphabetically sorted
    function populateStateDropdown() {
        if (!stateSelect || !statesDistrictsData) return;

        // Get sorted states list
        const stateList = statesDistrictsData.states.map(s => s.state).sort();

        // Clear existing options
        stateSelect.innerHTML = `<option value="" disabled selected>Select State Name</option>`;

        // Append options
        stateList.forEach(stateName => {
            const opt = document.createElement("option");
            opt.value = stateName;
            opt.textContent = stateName;
            stateSelect.appendChild(opt);
        });

        // Initialize district selector in a clean state
        clearDistrictField();
    }

    // Render GeoJSON state layers on Leaflet
    function renderMapLayers() {
        if (!map || !indiaGeoJson) return;

        geoJsonLayer = L.geoJSON(indiaGeoJson, {
            style: defaultStyle,
            onEachFeature: onEachFeatureClosure
        }).addTo(map);
    }

    // closure to bind events to each state feature
    function onEachFeatureClosure(feature, layer) {
        layer.on({
            mouseover: highlightFeature,
            mouseout: resetHighlight,
            click: selectStateFromMap
        });
    }

    // Highlight on hover
    function highlightFeature(e) {
        const layer = e.target;
        if (layer !== selectedLayer) {
            layer.setStyle(hoverStyle);
        }
    }

    // Reset style on mouseout
    function resetHighlight(e) {
        const layer = e.target;
        if (layer !== selectedLayer) {
            geoJsonLayer.resetStyle(layer);
        }
    }

    // Handle map click on a state
    function selectStateFromMap(e) {
        const layer = e.target;
        const stateName = layer.feature.properties.st_nm;

        // Reset previous selected layer style
        if (selectedLayer) {
            geoJsonLayer.resetStyle(selectedLayer);
        }

        // Set new selected layer and style
        selectedLayer = layer;
        layer.setStyle(selectedStyle);

        // Zoom to the bounds of the clicked state
        map.fitBounds(layer.getBounds());

        // Update form state select
        if (stateSelect) {
            stateSelect.value = stateName;
            // Trigger change event to populate districts
            stateSelect.dispatchEvent(new Event("change"));
        }
    }

    // Handle state selection change (from map or dropdown)
    function handleStateSelection(stateName) {
        if (!statesDistrictsData) return;

        // Find districts for this state
        const stateObj = statesDistrictsData.states.find(s => s.state.toLowerCase() === stateName.toLowerCase());
        if (!stateObj) {
            clearDistrictField();
            return;
        }

        // Display district container
        if (districtPickerContainer) {
            districtPickerContainer.style.display = "block";
        }
        if (selectedStateTitle) {
            selectedStateTitle.textContent = `${stateName} Districts:`;
        }

        // 1. Populate the form district dropdown
        if (districtSelect) {
            districtSelect.innerHTML = `<option value="" disabled selected>Select District Name</option>`;
            stateObj.districts.forEach(dist => {
                const opt = document.createElement("option");
                opt.value = dist;
                opt.textContent = dist;
                districtSelect.appendChild(opt);
            });
            districtSelect.disabled = false;
        }

        // 2. Render dynamic grid of district buttons
        if (districtGrid) {
            districtGrid.innerHTML = "";
            stateObj.districts.sort().forEach(dist => {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.className = "district-btn";
                btn.textContent = dist;
                btn.addEventListener("click", () => {
                    selectDistrict(dist, btn);
                });
                districtGrid.appendChild(btn);
            });
        }
    }

    // Handle selecting a district (from grid button)
    function selectDistrict(districtName, clickedBtn) {
        if (districtSelect) {
            districtSelect.value = districtName;
            districtSelect.dispatchEvent(new Event("change"));
        }

        // Update active class on grid buttons
        if (districtGrid) {
            const buttons = districtGrid.querySelectorAll(".district-btn");
            buttons.forEach(btn => btn.classList.remove("active"));
        }
        if (clickedBtn) {
            clickedBtn.classList.add("active");
        }
    }

    // Clear and disable district dropdown
    function clearDistrictField() {
        if (districtSelect) {
            districtSelect.innerHTML = `<option value="" disabled selected>Select District Name</option>`;
            districtSelect.disabled = true;
        }
        if (districtPickerContainer) {
            districtPickerContainer.style.display = "none";
        }
        if (districtGrid) {
            districtGrid.innerHTML = "";
        }
    }

    // Set up dropdown events syncing back to map/picker
    function setupDropdownSync() {
        if (stateSelect) {
            stateSelect.addEventListener("change", function () {
                const stateName = stateSelect.value;
                handleStateSelection(stateName);

                // Find corresponding layer on Leaflet and style/zoom to it
                if (geoJsonLayer) {
                    let matchedLayer = null;
                    geoJsonLayer.eachLayer(layer => {
                        const layerStateName = layer.feature.properties.st_nm;
                        if (layerStateName.toLowerCase() === stateName.toLowerCase()) {
                            matchedLayer = layer;
                        }
                    });

                    if (matchedLayer) {
                        if (selectedLayer) {
                            geoJsonLayer.resetStyle(selectedLayer);
                        }
                        selectedLayer = matchedLayer;
                        matchedLayer.setStyle(selectedStyle);
                        map.fitBounds(matchedLayer.getBounds());
                    }
                }
            });
        }

        // When form district dropdown is changed, highlight it in the picker grid
        if (districtSelect) {
            districtSelect.addEventListener("change", function () {
                const selectedDistrict = districtSelect.value;
                if (districtGrid) {
                    const buttons = districtGrid.querySelectorAll(".district-btn");
                    buttons.forEach(btn => {
                        if (btn.textContent.trim().toLowerCase() === selectedDistrict.toLowerCase()) {
                            btn.classList.add("active");
                            // Scroll button into view inside scrollable container
                            btn.scrollIntoView({ behavior: "smooth", block: "nearest" });
                        } else {
                            btn.classList.remove("active");
                        }
                    });
                }
            });
        }
    }
});
