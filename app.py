import requests
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
# Coordinates for major Saudi agricultural regions (13)
SAUDI_CITIES = {
    "riyadh": {"lat": 24.7136, "lon": 46.6753},
    "jeddah": {"lat": 21.5433, "lon": 39.1728},
    "dammam": {"lat": 26.4207, "lon": 50.0888},
    "al_hassa": {"lat": 25.3800, "lon": 49.5888},
    "qatif": {"lat": 26.5652, "lon": 50.0121},
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
    date_str = data.get('date')
    
    # Parse Date for Seasonality Logic
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        month = date_obj.month
    except:
        month = 1 # Default to Jan if error

    # 1. Fetch Comprehensive Weather Data
    if city_key not in SAUDI_CITIES:
        return jsonify({'error': "Invalid City Selected"})
    
    coords = SAUDI_CITIES[city_key]
    weather = get_weather_data(coords['lat'], coords['lon'], date_str)
    
    if not weather:
        return jsonify({'error': "Could not fetch weather data."})

    # 2. Extract Variables
    temp = weather['temp_max']
    humidity = weather['humidity_mean']
    rain_mm = weather['rain_sum']
    wind_speed = weather['wind_speed_max'] # New Variable

    # User Inputs
    age = float(data.get('age', 5)) 
    soil = data.get('soil', 'good') 

    risks = []

    # --- SOPHISTICATED RISK MODELS ---

    # 1. Graphiola Leaf Spot (Graphiola phoenicis)
    # Refined Logic: Needs high heat AND saturation.
    # Risk drops if temp is too extreme (>40) or too dry.
    g_score = 0
    if 25 <= temp <= 35: g_score += 1
    if humidity > 65: g_score += 1
    if humidity > 85: g_score += 2 # Critical saturation point
    if age >= 3: g_score += 1
    
    if g_score >= 4:
        risks.append(f"<strong>Graphiola Leaf Spot:</strong> High<br><span class='reason'>High humidity ({humidity}%) + Optimal fungal temp.</span>")
    elif g_score >= 2:
        risks.append(f"<strong>Graphiola Leaf Spot:</strong> Moderate<br><span class='reason'>Favorable, but humidity levels sub-critical.</span>")


    # 2. Khamedj Disease (Inflorescence Rot)
    # Refined Logic: Seasonality is key (Feb-April) when Spathes emerge.
    k_risk = "Low"
    is_spathe_season = month in [2, 3, 4] # Feb, Mar, Apr
    
    if is_spathe_season:
        if rain_mm > 5.0: # Significant rain in season
            k_risk = "High"
        elif rain_mm > 0.5 and humidity > 80:
            k_risk = "Moderate"
            
    if "qatif" in city_key and k_risk != "Low":
        k_risk = "Very High (Endemic History)"
        
    if k_risk != "Low":
        risks.append(f"<strong>Khamedj Disease:</strong> {k_risk}<br><span class='reason'>Spathe season (Spring) + Moisture detected.</span>")


    # 3. Al Wijam (Phytoplasma)
    # Refined Logic: Vector activity (Leafhopper) + Location
    # Vector thrives in 25-35C.
    if city_key in ["al_hassa", "qatif", "hofuf"]:
        if 25 <= temp <= 35:
            risks.append(f"<strong>Al Wijam:</strong> High<br><span class='reason'>Oasis zone + Optimal vector flight temp ({temp}°C).</span>")
        else:
            risks.append(f"<strong>Al Wijam:</strong> Moderate<br><span class='reason'>Endemic zone, but temp reduces vector activity.</span>")


    # 4. White Scale (Parlatoria blanchardii)
    # Refined Logic: Heat mortality curve.
    ws_risk = "Low"
    if 28 <= temp <= 36:
        ws_risk = "High"
        if 2 <= age <= 8: ws_risk = "Very High (Target Age)"
    elif temp > 38:
        ws_risk = "Low (Heat Mortality)" # High heat kills the crawlers
    
    if ws_risk != "Low":
        risks.append(f"<strong>White Scale:</strong> {ws_risk}<br><span class='reason'>Temp ({temp}°C) is perfect for colony expansion.</span>")


    # 5. Red Palm Weevil (Rhynchophorus ferrugineus)
    # Refined Logic: Wind Speed & Flight Physics
    # Weevils struggle to fly/infest new trees if wind > 20 km/h
    rpw_risk = "Low"
    
    if 18 <= temp <= 40:
        rpw_risk = "Moderate"
        if 26 <= temp <= 33:
            rpw_risk = "High"
            
        # Biological Multiplier: Moisture
        if soil == 'wet': 
            rpw_risk = "Critical"
            
        # Physical Inhibitor: Wind
        if wind_speed > 20: 
            rpw_risk = f"Moderate (High Wind)"
            wind_note = f"High wind ({wind_speed} km/h) reduces flight/spread."
        else:
            wind_note = "Calm winds favor flight."

    if rpw_risk != "Low":
        risks.append(f"<strong>Red Palm Weevil:</strong> {rpw_risk}<br><span class='reason'>{wind_note} Temp optimal.</span>")

    # Output Construction
    if not risks:
        html_output = "<div class='safe-status'>No critical biological risks detected for today's specific conditions.</div>"
    else:
        html_output = "<ul class='risk-list'><li>" + "</li><li>".join(risks) + "</li></ul>"

    summary = f"{city_key.title()} | {temp}°C | {humidity}% RH | Wind: {wind_speed} km/h"
    
    return jsonify({'result': html_output, 'weather_summary': summary})

def get_weather_data(lat, lon, date_str):
    try:
        # Added wind_speed_10m_max to the request
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,relative_humidity_2m_mean,rain_sum,wind_speed_10m_max",
            "timezone": "auto",
            "start_date": date_str,
            "end_date": date_str
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        daily = data.get('daily', {})
        
        return {
            "temp_max": daily['temperature_2m_max'][0],
            "humidity_mean": daily['relative_humidity_2m_mean'][0],
            "rain_sum": daily['rain_sum'][0],
            "wind_speed_max": daily['wind_speed_10m_max'][0]
        }
    except Exception as e:
        print(f"API Error: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True, port=5001)
