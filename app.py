import requests
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- Configuration: Saudi Cities ---
SAUDI_CITIES = { # 14 cities, possible expansion later
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
    "najran": {"lat": 17.4917, "lon": 44.1322},
    "tabuk": {"lat": 28.3835, "lon": 36.5662},
    "jouf": {"lat": 29.9539, "lon": 40.1970}
}

@app.route('/')
def index():
    return render_template('index.html', cities=SAUDI_CITIES)

@app.route('/assess', methods=['POST'])
def assess_risk():
    data = request.json
    city_key = data.get('city')
    
    # Defaults
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    month = today.month
    age = 5 # starting point, just because most at risk plants are at the 5 year mark        
    
    if city_key not in SAUDI_CITIES:
        return jsonify({'error': "Invalid City"})
    
    # 1. Fetch Advanced Weather Data
    coords = SAUDI_CITIES[city_key]
    weather = get_weather_data(coords['lat'], coords['lon'], date_str)
    
    if not weather:
        return jsonify({'error': "Weather API Error"})

    # Extract Variables
    temp = weather['temp']         # C
    humidity = weather['humidity'] # %
    rain = weather['rain']         # mm
    wind = weather['wind']         # km/h
    dew_point = weather['dew_point'] # C (New)
    pressure = weather['pressure']   # hPa (New)
    vis = weather['visibility']      # meters (New)

    # --- Derived Indicators ---
    # Dew Spread: How close is the air to saturation?
    dew_spread = temp - dew_point 
    dew_forming = dew_spread < 2.5  # If spread is < 2.5C, dew is likely forming

    # Dust Storm Detection: Low Vis + Low Humidity = Dust
    is_dusty = (vis < 5000) and (humidity < 50)
    
    risks = []

    # --- RISK LOGIC ENGINE ---

    # 1. Graphiola Leaf Spot (Physics: Needs Liquid Water/Dew)
    # Logic: High Humidity is not enough; we need DEW Point proximity.
    g_risk = "Low"
    if dew_forming or rain > 0.5:
        # Liquid water is present
        if 20 <= temp <= 35:
            g_risk = "Critical"
            reason = f"Dew Point reached ({dew_point}°C). Free water on leaves triggers spores."
        else:
            g_risk = "Moderate"
            reason = "Moisture present, but temp is non-optimal."
    elif humidity > 75:
        g_risk = "High"
        reason = f"High Humidity ({humidity}%) detected."
    
    if g_risk != "Low":
        risks.append(f"<strong>Graphiola Leaf Spot:</strong> {g_risk}<br><span class='reason'>{reason}</span>")

    # 2. White Scale (Physics: Dust protects them)
    # Logic: Thrives in dust (blocks predators) and moderate heat.
    ws_risk = "Low"
    if 28 <= temp <= 36:
        ws_risk = "High"
        ws_reason = f"Optimal breeding temp ({temp}°C)."
        
        # New Feature: Dust Check
        if is_dusty:
            ws_risk = "Very High"
            ws_reason += " + Dust storm protects scale from predators."
            
    if temp > 38: ws_risk = "Low (Heat Mortality)"
    
    if ws_risk != "Low":
        risks.append(f"<strong>White Scale:</strong> {ws_risk}<br><span class='reason'>{ws_reason}</span>")

    # 3. Red Palm Weevil (Physics: Flight Aerodynamics)
    # Logic: Temp + Wind/Vis constraints
    rpw_risk = "Low"
    if 18 <= temp <= 40:
        rpw_risk = "High"
        flight_status = "Active"
        
        # Flight Inhibitors
        if wind > 20:
            rpw_risk = "Moderate"
            flight_status = f"Reduced by Wind ({wind} km/h)"
        if is_dusty:
            rpw_risk = "Low"
            flight_status = "Grounded by Dust/Sand"
            
    if rpw_risk != "Low":
        risks.append(f"<strong>Red Palm Weevil:</strong> {rpw_risk}<br><span class='reason'>Temp: {temp}°C. Flight: {flight_status}.</span>")

    # 4. Khamedj Disease (Seasonality + Pressure Systems)
    # Logic: Low Pressure often precedes storms/rain.
    k_risk = "Low"
    is_season = month in [2, 3, 4]
    
    if is_season:
        if pressure < 1008: # Low pressure system
            k_risk = "High (Storm Alert)"
            k_reason = f"Low Pressure ({pressure} hPa) indicates incoming instability."
        elif rain > 2.0:
            k_risk = "High"
            k_reason = "Rainfall detected during spathe season."
        else:
            k_risk = "Moderate" # Caution during season
            k_reason = "Spathe season active."
            
        if k_risk != "Moderate" or rain > 0:
            risks.append(f"<strong>Khamedj Disease:</strong> {k_risk}<br><span class='reason'>{k_reason}</span>")

    # 5. Al Wijam (Vector Logic)
    if city_key in ["al_hassa", "qatif", "hofuf"] and 25 <= temp <= 35:
        risks.append(f"<strong>Al Wijam:</strong> High<br><span class='reason'>Endemic Zone + Vector Active.</span>")

    # Output Construction
    if not risks:
        html_output = "<div class='safe-status'>No critical biological risks detected.</div>"
    else:
        html_output = "<ul class='risk-list'><li>" + "</li><li>".join(risks) + "</li></ul>"

    # Create detailed weather summary for the badge
    summary = {
        "temp": temp,
        "rh": humidity,
        "dew": dew_point,
        "vis": round(vis/1000, 1), # Convert to km
        "pressure": pressure,
        "wind": wind
    }
    
    return jsonify({'result': html_output, 'weather_summary': summary})

def get_weather_data(lat, lon, date_str):
    try:
        # Added: dewpoint_2m, surface_pressure, visibility
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,rain,wind_speed_10m,dew_point_2m,surface_pressure,visibility",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        curr = data.get('current', {})
        
        return {
            "temp": curr.get('temperature_2m'),
            "humidity": curr.get('relative_humidity_2m'),
            "rain": curr.get('rain'),
            "wind": curr.get('wind_speed_10m'),
            "dew_point": curr.get('dew_point_2m'),
            "pressure": curr.get('surface_pressure'),
            "visibility": curr.get('visibility') # in meters
        }
    except Exception as e:
        print(f"API Error: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True, port=5001)
