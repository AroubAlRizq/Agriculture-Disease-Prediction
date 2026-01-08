from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/assess', methods=['POST'])
def assess_risk():
    data = request.json
    
    # Safe data extraction
    try:
        location = data.get('location', '').lower()
        temp = float(data.get('temp', 0))
        humidity = float(data.get('humidity', 0))
        age = float(data.get('age', 0))
        rain = data.get('rain', 'none')
        soil = data.get('soil', 'good')
    except (ValueError, TypeError):
        return jsonify({'result': "Error: Please ensure numeric fields contain valid numbers."})

    risks = []

    # 1. Graphiola Leaf Spot
    # Logic: Humid/Moderate Temp (23-29C), Age > 3
    g_risk = "Low"
    if 23 <= temp <= 29 and humidity > 70:
        g_risk = "Moderate"
        if age >= 3:
            g_risk = "High"
    if any(city in location for city in ["katif", "dammam", "jeddah", "qatif"]):
        if g_risk != "Low":
            g_risk = "Very High (Endemic Area)"
    if g_risk != "Low":
        risks.append(f"<strong>Graphiola Leaf Spot:</strong> {g_risk}<br><span class='reason'>Triggered by high humidity & moderate temps.</span>")

    # 2. Khamedj Disease (Inflorescence Rot)
    # Logic: Heavy rain, Temp < 40, Poor drainage
    k_risk = "Low"
    if rain == 'heavy' and temp < 40:
        k_risk = "Moderate"
        if soil == 'poor':
            k_risk = "High"
    if "katif" in location or "qatif" in location:
         if k_risk != "Low": k_risk = "Very High (Historical Outbreaks)"
    if k_risk != "Low":
        risks.append(f"<strong>Khamedj Disease:</strong> {k_risk}<br><span class='reason'>Triggered by heavy rain & poor soil drainage.</span>")

    # 3. Al Wijam (Phytoplasma)
    # Logic: Oasis microclimate (Al Hassa)
    if "hassa" in location or "ahsa" in location or "oasis" in location:
        risks.append(f"<strong>Al Wijam:</strong> High<br><span class='reason'>Vector thrives in oasis microclimates (Al Hassa).</span>")

    # 4. White Scale
    # Logic: Temp 30-35, Humidity ~60%, Young palms (2-8 yrs)
    ws_risk = "Low"
    if 30 <= temp <= 35:
        if 50 <= humidity <= 70:
            ws_risk = "Moderate"
            if 2 <= age <= 8:
                ws_risk = "High (Vulnerable Age)"
    if temp > 37:
        ws_risk = "Low" # Heat mortality
    if ws_risk != "Low":
        risks.append(f"<strong>White Scale:</strong> {ws_risk}<br><span class='reason'>Thrives in warm, moderate humidity.</span>")

    # 5. Red Palm Weevil
    # Logic: Temp 17-40 (Opt 27-32), Wet soil/Over-watering
    rpw_risk = "Low"
    if 17 <= temp <= 40:
        rpw_risk = "Moderate"
        if 27 <= temp <= 32:
            rpw_risk = "High"
        if soil == 'wet':
            rpw_risk = "Critical (Attracted to soft tissue)"
    if rpw_risk != "Low":
        risks.append(f"<strong>Red Palm Weevil:</strong> {rpw_risk}<br><span class='reason'>The most dangerous pest. Active in current temps.</span>")

    if not risks:
        final_html = "<div class='safe-status'>Conditions are generally safe from these 5 specific major pests.</div>"
    else:
        final_html = "<ul class='risk-list'><li>" + "</li><li>".join(risks) + "</li></ul>"

    return jsonify({'result': final_html})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
