document.addEventListener('DOMContentLoaded', function() {
    const calcBtn = document.getElementById('calc-btn');
    const resultArea = document.getElementById('result-area');
    const resultDisplay = document.getElementById('result-display');

    calcBtn.addEventListener('click', async function() {
        // Collect Inputs
        const data = {
            location: document.getElementById('location').value,
            temp: document.getElementById('temp').value,
            humidity: document.getElementById('humidity').value,
            age: document.getElementById('age').value,
            rain: document.getElementById('rain').value,
            soil: document.getElementById('soil').value
        };

        // Basic Validation
        if (!data.temp || !data.humidity || !data.age) {
            alert("Please fill in all numeric fields (Temp, Humidity, Age).");
            return;
        }

        // Add loading state
        calcBtn.innerText = "Analyzing...";
        calcBtn.disabled = true;

        try {
            const response = await fetch('/assess', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            // Display Results
            resultDisplay.innerHTML = result.result;
            resultArea.classList.remove('hidden');
            
            // Scroll to results
            resultArea.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error(error);
            alert("Connection error.");
        } finally {
            calcBtn.innerText = "Analyze Risk";
            calcBtn.disabled = false;
        }
    });
});
