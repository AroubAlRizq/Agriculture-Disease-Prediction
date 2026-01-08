import requests
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
# Coordinates for major Saudi agricultural regions
SAUDI_CITIES = {
    "riyadh": {"lat": 24.7136, "lon": 46.6753},
    "jeddah": {"lat": 21.5433, "lon": 39.1728},
    "dammam": {"lat": 26.4207, "lon": 50.0888},
    "al_hassa": {"lat": 25.3800, "lon": 49.5888}, # Critical for Al Wijam
    "qatif": {"lat": 26.5652, "lon": 50.0121},    # Critical for Khamedj
    "taif": {"lat": 21.2854, "lon": 40.4222},
    "madinah": {"lat": 24.5247, "lon": 39.5692},
    "buraidah": {"lat": 26.3592, "lon": 43.9818},
    "abha": {"lat": 18.2068, "lon": 42.5109},
    "hail": {"lat": 27.5114, "lon": 41.7208},
    "jazan": {"lat": 16.8894, "lon": 42.5706},
    "najran": {"lat": 17.4917, "lon": 44.1322}
}

@app.route('/')
def index():
    return render_template('index.html', cities=SAUDI_CITIES)

@app.route('/assess', methods=['POST'])
def assess_risk():
    data = request.json
    city_key = data.get('city')
    date_str = data.get('date') # Format: YYYY-MM-DD
    
    # 1. Fetch Weather Data (Automated)
    if city_key not in SAUDI_CITIES:
        return jsonify({'error': "Invalid City Selected"})
    
    coords = SAUDI_CITIES[city_key]
    weather = get_weather_data(coords['lat'], coords['lon'], date_str)
    
    if not weather:
        return jsonify({'error': "Could not fetch weather data from API."})

    # 2. Run Risk Logic (Using the fetched data)
    # We map the API data to your specific logic variables
    temp = weather['temp_max']
    humidity = weather['humidity_mean']
    rain_mm = weather['rain_sum']
    
    # Determine "Rain Condition" for your logic based on mm
    rain_condition = "none"
    if rain_mm > 0.5: rain_condition = "moderate"
    if rain_mm > 10.0: rain_condition = "heavy"

    # User manually inputs these, or we default them if not provided
    age = float(data.get('age', 5)) 
    soil = data.get('soil', 'good') 

    # --- Risk Logic ---
    risks = []

    # Graphiola Leaf Spot (Humid/Moderate Temp 23-29, Age > 3)
    g_risk = "Low"
    if 23 <= temp <= 29 and humidity > 60:
        g_risk = "Moderate"
        if age >= 3: g_risk = "High"
    if city_key in ["qatif", "dammam", "jeddah"]:
        if g_risk != "Low": g_risk = "Very High (Endemic Area)"
    if g_risk != "Low":
        risks.append(f"<strong>Graphiola Leaf Spot:</strong> {g_risk}<br><span class='reason'>Conditions: {temp}°C, {humidity}% Humidity.</span>")

    # Khamedj Disease (Heavy Rain, Temp < 40)
    k_risk = "Low"
    if rain_condition == 'heavy' and temp < 40:
        k_risk = "High (Heavy Rain Detected)"
    if city_key in ["qatif"] and k_risk != "Low":
        k_risk = "Very High (Historical Outbreaks)"
    if k_risk != "Low":
        risks.append(f"<strong>Khamedj Disease:</strong> {k_risk}<br><span class='reason'>Triggered by heavy rainfall ({rain_mm}mm).</span>")

    # Al Wijam (Oasis Microclimate)
    if city_key in ["al_hassa", "qatif"]:
        risks.append(f"<strong>Al Wijam:</strong> High<br><span class='reason'>Location match: {city_key} (Oasis environment).</span>")

    # White Scale (Temp 30-35, Humidity ~60%)
    ws_risk = "Low"
    if 30 <= temp <= 35 and 50 <= humidity <= 75:
        ws_risk = "High" if 2 <= age <= 8 else "Moderate"
    if temp > 37: ws_risk = "Low (Heat mortality)"
    if ws_risk != "Low":
        risks.append(f"<strong>White Scale:</strong> {ws_risk}<br><span class='reason'>Ideal insect breeding temp ({temp}°C).</span>")

    # Red Palm Weevil (Temp 17-40, Opt 27-32)
    rpw_risk = "Low"
    if 17 <= temp <= 40:
        rpw_risk = "Moderate"
        if 27 <= temp <= 32: rpw_risk = "High"
        if soil == 'wet': rpw_risk = "Critical (High Moisture)"
    if rpw_risk != "Low":
        risks.append(f"<strong>Red Palm Weevil:</strong> {rpw_risk}<br><span class='reason'>Active in current range ({temp}°C).</span>")

    if not risks:
        html_output = "<div class='safe-status'>No high risks detected for this date.</div>"
    else:
        html_output = "<ul class='risk-list'><li>" + "</li><li>".join(risks) + "</li></ul>"

    # Add a weather summary so the user trusts the data
    summary = f"Weather for {date_str}: Max {temp}°C, Humidity {humidity}%, Rain {rain_mm}mm"
    
    return jsonify({'result': html_output, 'weather_summary': summary})

def get_weather_data(lat, lon, date_str):
    """
    Fetches weather from Open-Meteo. 
    NOTE FOR NCM INTERNSHIP: 
    If you have internal access, replace this URL with: https://api.ncm.gov.sa/...
    and add your 'auth' headers.
    """
    try:
        # Open-Meteo API (Free, No Key)
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,relative_humidity_2m_mean,rain_sum",
            "timezone": "auto",
            "start_date": date_str,
            "end_date": date_str
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        # Extract daily stats
        daily = data.get('daily', {})
        return {
            "temp_max": daily['temperature_2m_max'][0],
            "humidity_mean": daily['relative_humidity_2m_mean'][0],
            "rain_sum": daily['rain_sum'][0]
        }
    except Exception as e:
        print(f"API Error: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True, port=5001)
