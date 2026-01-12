document.addEventListener('DOMContentLoaded', function() {
    const calcBtn = document.getElementById('calc-btn');
    const resultArea = document.getElementById('result-area');
    const citySelect = document.getElementById('city');

    // Dashboard Elements
    const valTemp = document.getElementById('w-temp');
    const valHum = document.getElementById('w-hum');
    const valDew = document.getElementById('w-dew');
    const valWind = document.getElementById('w-wind');
    const valVis = document.getElementById('w-vis');
    const valPres = document.getElementById('w-pres');
    
    const resultDisplay = document.getElementById('result-display');

    calcBtn.addEventListener('click', async function() {
        // UI: Set Loading State
        calcBtn.innerText = "Processing Telemetry...";
        calcBtn.disabled = true;
        resultArea.classList.add('hidden');

        const payload = {
            city: citySelect.value
        };

        try {
            const response = await fetch('/assess', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();

            if (data.error) {
                alert("System Error: " + data.error);
            } else {
                // 1. Update the Weather Dashboard Grid
                // We use the data from the 'weather_summary' dictionary sent by Python
                valTemp.innerText = data.weather_summary.temp + "°C";
                valHum.innerText = data.weather_summary.rh + "%";
                valDew.innerText = data.weather_summary.dew + "°C";
                valWind.innerText = data.weather_summary.wind + " km/h";
                valVis.innerText = data.weather_summary.vis + " km";
                valPres.innerText = data.weather_summary.pressure + " hPa";

                // 2. Inject the Risk Report HTML
                resultDisplay.innerHTML = data.result;

                // 3. Reveal the Section
                resultArea.classList.remove('hidden');
                
                // Smooth scroll to results
                resultArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

        } catch (error) {
            console.error("Fetch error:", error);
            alert("Connection Failed. Please check your internet or server status.");
        } finally {
            // UI: Reset Button
            calcBtn.innerText = "Analyze Satellite Data";
            calcBtn.disabled = false;
        }
    });
});
