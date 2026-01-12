@app.route('/assess', methods=['POST'])
def assess_risk():
    data = request.json
    city_key = data.get('city')
    
    # Defaults
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    month = today.month
    
    if city_key not in SAUDI_CITIES: return jsonify({'error': "Invalid City"})
    
    coords = SAUDI_CITIES[city_key]
    weather = get_weather_data(coords['lat'], coords['lon'], date_str)
    
    if not weather: return jsonify({'error': "Weather API Error"})

    # Extract Variables
    temp = weather['temp']
    humidity = weather['humidity']
    rain = weather['rain']
    wind = weather['wind']
    dew_point = weather['dew_point']
    pressure = weather['pressure']
    vis = weather['visibility']

    # Derived Logic
    dew_spread = temp - dew_point
    dew_forming = dew_spread < 2.5
    is_dusty = (vis < 5000) and (humidity < 50)
    
    # We store findings as objects to sort/color them later
    findings = []

    # --- 1. Graphiola Leaf Spot ---
    g_level = "Low"
    g_reason = f"Humidity ({humidity}%) is insufficient for spores."
    
    if dew_forming or rain > 0.5:
        if 20 <= temp <= 35:
            g_level = "Critical"
            g_reason = f"Dew detected (Spread {round(dew_spread,1)}°C) + Optimal Temp."
        else:
            g_level = "Moderate"
            g_reason = "Moisture present, but temp is non-optimal."
    elif humidity > 75:
        g_level = "High"
        g_reason = "High atmospheric humidity favors growth."
    
    findings.append({"name": "Graphiola Leaf Spot", "level": g_level, "reason": g_reason})

    # --- 2. White Scale ---
    ws_level = "Low"
    ws_reason = "Conditions stable."
    
    if 28 <= temp <= 36:
        ws_level = "High"
        ws_reason = f"Temp ({temp}°C) is optimal for breeding."
        if is_dusty:
            ws_level = "Very High"
            ws_reason = "Dust storm protects pests from predators."
    elif temp > 38:
        ws_level = "Low"
        ws_reason = "High heat causes pest mortality."
    else:
        ws_level = "Low"
        ws_reason = f"Temp ({temp}°C) is too cool for rapid growth."

    findings.append({"name": "White Scale", "level": ws_level, "reason": ws_reason})

    # --- 3. Red Palm Weevil ---
    rpw_level = "Low"
    rpw_reason = ""
    
    if 18 <= temp <= 40:
        rpw_level = "High"
        rpw_reason = "Active flight temperature range."
        
        # Inhibitors
        if wind > 20:
            rpw_level = "Moderate"
            rpw_reason = f"Flight reduced by High Wind ({wind} km/h)."
        if is_dusty:
            rpw_level = "Low"
            rpw_reason = "Grounded by low visibility/dust."
    else:
        rpw_reason = "Dormant due to extreme temp."
        
    findings.append({"name": "Red Palm Weevil", "level": rpw_level, "reason": rpw_reason})

    # --- 4. Khamedj Disease ---
    k_level = "Low"
    is_season = month in [2, 3, 4] # Feb-Apr
    
    if is_season:
        if pressure < 1008:
            k_level = "High"
            k_reason = f"Storm Alert (Pressure {pressure} hPa) during Spathe Season."
        elif rain > 2.0:
            k_level = "High"
            k_reason = "Rain detected during Spathe Season."
        else:
            k_level = "Moderate"
            k_reason = "Spathe season active (monitor for rain)."
    else:
        k_level = "Low"
        k_reason = "Not Spathe emergence season (Spring)."

    findings.append({"name": "Khamedj Disease", "level": k_level, "reason": k_reason})

    # --- 5. Al Wijam ---
    # Strictly Location Based
    aw_level = "Low"
    if city_key in ["al_hassa", "qatif", "hofuf"]:
        if 25 <= temp <= 35:
            aw_level = "High"
            aw_reason = "Endemic Zone + Vector Active."
        else:
            aw_level = "Moderate"
            aw_reason = "Endemic Zone (Vector dormant)."
    else:
        aw_level = "Negligible"
        aw_reason = "Not a known vector zone."

    findings.append({"name": "Al Wijam", "level": aw_level, "reason": aw_reason})

    # --- HTML Generator ---
    html_output = "<ul class='risk-list'>"
    for item in findings:
        # Assign CSS class based on text content
        css_class = "risk-low"
        if "Moderate" in item['level']: css_class = "risk-mod"
        if "High" in item['level'] or "Critical" in item['level']: css_class = "risk-high"
        
        html_output += f"""
        <li class='{css_class}'>
            <div class='risk-header'>
                <strong>{item['name']}</strong>
                <span class='badge'>{item['level']}</span>
            </div>
            <span class='reason'>{item['reason']}</span>
        </li>
        """
    html_output += "</ul>"

    summary = {
        "temp": temp, "rh": humidity, "dew": dew_point,
        "vis": round(vis/1000, 1), "pressure": pressure, "wind": wind
    }
    
    return jsonify({'result': html_output, 'weather_summary': summary})
