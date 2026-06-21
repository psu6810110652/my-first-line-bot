import os
import requests
import time
import threading
import json
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# พิกัดหาดใหญ่ สงขลา
LAT = "7.0084"
LON = "100.4747"

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")

# =======================================================
# 1. ระบบเก็บสถิติย้อนหลังเพื่อเอาไปทำกราฟ (7 วันล่าสุด)
# =======================================================
# จำลองข้อมูลเริ่มต้น (Mock Data) เพื่อให้เปิดเว็บมาแล้วมีกราฟโชว์ทันที
history_data = {
    "labels": ["จันทร์", "อังคาร", "พุธ", "พฤหัสฯ", "ศุกร์", "เสาร์", "อาทิตย์"],
    "temp_max": [33.5, 34.2, 35.0, 32.8, 33.1, 34.6, 35.2],
    "temp_min": [25.1, 24.8, 26.0, 24.2, 25.0, 25.5, 26.1],
    "pm25": [12.5, 18.2, 22.4, 38.0, 15.6, 11.2, 14.5]
}

# ตัวแปรสำหรับจดบันทึกของวันปัจจุบัน
current_day_stats = {"max_temp": -999, "min_temp": 999, "max_pm25": 0}

def update_daily_history(temp, pm25):
    global current_day_stats
    if temp > current_day_stats["max_temp"]: current_day_stats["max_temp"] = temp
    if temp < current_day_stats["min_temp"]: current_day_stats["min_temp"] = temp
    if pm25 > current_day_stats["max_pm25"]: current_day_stats["max_pm25"] = pm25

# =======================================================
# 2. ฟังก์ชันดึงและประมวลผลข้อมูลสภาพอากาศ + PM 2.5
# =======================================================
def get_weather_data():
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={WEATHER_KEY}&units=metric&lang=th"
    pollution_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={WEATHER_KEY}"
    
    try:
        w_res = requests.get(weather_url).json()
        p_res = requests.get(pollution_url).json()
        
        if w_res.get("cod") != 200:
            return None, f"OpenWeather Error: `{w_res.get('message')}`"
            
        temp = w_res["main"]["temp"]
        humidity = w_res["main"]["humidity"]
        description = w_res["weather"][0]["description"]
        main_weather = w_res["weather"][0]["main"]
        icon_code = w_res["weather"][0]["icon"]
        pm25 = p_res["list"][0]["components"]["pm2_5"]
        aqi_code = p_res["list"][0]["main"]["aqi"]
        
        # อัปเดตข้อมูลสถิติของวันนี้
        update_daily_history(temp, pm25)
        
        aqi_th = {
            1: "ดีมาก 🟢", 2: "ดี 🟢", 3: "ปานกลาง 🟡", 
            4: "เริ่มมีผลกระทบต่อสุขภาพ 🟠", 5: "มีผลกระทบต่อสุขภาพอย่างมาก 🔴"
        }.get(aqi_code, "ไม่สามารถระบุได้")
        
        status_text = "วันนี้อากาศปกติครับ" if aqi_code <= 2 else "ช่วงนี้มีฝุ่นเล็กน้อยครับ" if aqi_code == 3 else "ระวังสุขภาพด้วยนะครับ"
        thumbnail_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
        
        return {
            "temp": temp, "humidity": humidity, "desc": description,
            "main_weather": main_weather, "pm25": pm25, "aqi": aqi_th,
            "status": status_text, "thumbnail": thumbnail_url
        }, None
    except Exception as e:
        return None, f"โค้ดทำงานผิดพลาด: `{str(e)}`"

def send_to_discord(is_manual=False, is_summary=False):
    if is_summary:
        global current_day_stats, history_data
        if current_day_stats["max_temp"] == -999: return
        
        # ดันข้อมูลวันนี้เข้าสู่ระบบกราฟสัปดาห์ (เลื่อนข้อมูลเก่าออก)
        today_name = datetime.now().strftime("%a")
        history_data["labels"].pop(0)
        history_data["labels"].append(today_name)
        history_data["temp_max"].pop(0)
        history_data["temp_max"].append(current_day_stats["max_temp"])
        history_data["temp_min"].pop(0)
        history_data["temp_min"].append(current_day_stats["min_temp"])
        history_data["pm25"].pop(0)
        history_data["pm25"].append(current_day_stats["max_pm25"])
        
        # ยิงสรุปเข้า Discord
        payload = {
            "embeds": [{
                "title": "📝 สรุปสถิติสภาพอากาศรอบวัน: หาดใหญ่",
                "color": 15105570,
                "description": f"📊 **ภาพรวมสถิติตลอด 24 ชม. ที่ผ่านมา**\n"
                               f"🌡️ อุณหภูมิสูงสุด: {current_day_stats['max_temp']} °C\n"
                               f"❄️ อุณหภูมิต่ำสุด: {current_day_stats['min_temp']} °C\n"
                               f"🌫️ ค่าฝุ่น PM 2.5 สูงสุด: {current_day_stats['max_pm25']} µg/m³",
                "footer": {"text": "อัปเดตระบบกราฟสัปดาห์บนหน้าเว็บเรียบร้อยแล้ว"}
            }]
        }
        requests.post(WEBHOOK_URL, json=payload)
        current_day_stats = {"max_temp": -999, "min_temp": 999, "max_pm25": 0}
        return

    data, error = get_weather_data()
    if error:
        requests.post(WEBHOOK_URL, json={"content": f"❌ {error}"})
        return

    alert_content = ""
    if data["pm25"] >= 37.5:
        alert_content += "⚠️ **🚨 แจ้งเตือนด่วน @everyone ค่าฝุ่น PM 2.5 เกินมาตรฐานวิกฤต!**\n"
    if "rain" in data["main_weather"].lower():
        alert_content += "🌧️ **🚨 แจ้งเตือนด่วน @everyone พบกลุ่มฝนในพื้นที่ระวังเปียกกันด้วยครับ!**\n"

    footer_text = "เรียกดูแบบแมนนวลผ่านหน้าเว็บ" if is_manual else "รายงานอัตโนมัติประจำวัน"

    payload = {
        "content": alert_content if alert_content != "" else None,
        "embeds": [
            {
                "title": "📍 รายงานอากาศ & มลพิษ: จังหวัดสงขลา (หาดใหญ่)",
                "description": f"✅ {data['status']}",
                "color": 3447003,
                "thumbnail": {"url": data["thumbnail"]},
                "fields": [
                    {"name": "🌡️ อุณหภูมิ", "value": f"{data['temp']} °C", "inline": True},
                    {"name": "💧 ความชื้น", "value": f"{data['humidity']}%", "inline": True},
                    {"name": "☁️ สภาพอากาศ", "value": data["desc"], "inline": True},
                    {"name": "😷 คุณภาพอากาศ (AQI)", "value": data["aqi"], "inline": True},
                    {"name": "🌫️ PM 2.5", "value": f"{data['pm25']} µg/m³", "inline": True}
                ],
                "footer": {"text": f"อัปเดตล่าสุด ณ เวลาปัจจุบัน • {footer_text}"}
            }
        ]
    }
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json=payload)

# =======================================================
# 3. ระบบหน้าเว็บ Live Dashboard + กราฟ Chart.js สุดโปร
# =======================================================
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/trigger-bot":
            send_to_discord(is_manual=True)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'<script>alert("\xe0\xb8\xaa\xe0\xb9\x88\xe0\xb8\x87\xe0\xb8\x82\xe0\xb9\x89\xe0\xb8\xa4\xe0\xb8\x84\xe0\xb8\xa7\xe0\xb8\xb2\xe0\xb8\xa1\xe0\xb9\x80\xe0\xb8\x82\xe0\xb9\x89\xe0\xb8\xb2 Discord \xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\xb5\xe0\xb8\xa2\xe0\xb8\xb9\xe0\xb8\xa3\xe0\xb9\x89\xe0\xb8\xad\xe0\xb8\xa2\xe0\xb9\x81\xe0\xb8\xa5\xe0\xb9\x89\xe0\xb8\xa7! \xf0\x9f\x8e\x89"); window.location.href="/";</script>')
            return

        data, _ = get_weather_data()
        if not data: data = {"temp": "N/A", "humidity": "N/A", "desc": "รอระบบรีเฟรช", "pm25": "N/A", "aqi": "N/A", "status": ""}

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>📊 PSU Weather Graphics Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: white; margin: 0; padding: 30px 10px; display: flex; flex-direction: column; align-items: center; }}
                .container {{ max-width: 750px; width: 100%; background: #1e293b; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); text-align: center; box-sizing: border-radius; }}
                h1 {{ color: #38bdf8; margin-bottom: 5px; font-size: 26px; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin-top: 20px; }}
                .card {{ background: #0f172a; padding: 12px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }}
                .card-title {{ font-size: 13px; color: #94a3b8; }}
                .card-value {{ font-size: 18px; font-weight: bold; color: #f8fafc; margin-top: 5px; }}
                .chart-container {{ background: #0f172a; padding: 15px; border-radius: 15px; margin-top: 25px; border: 1px solid rgba(255,255,255,0.05); }}
                .btn {{ display: block; background: linear-gradient(90deg, #0284c7, #0369a1); color: white; border: none; padding: 14px; font-size: 16px; border-radius: 12px; cursor: pointer; text-decoration: none; margin-top: 25px; font-weight: bold; transition: 0.3s; }}
                .btn:hover {{ transform: translateY(-2px); }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 แผงควบคุม & กราฟสถิติสภาพอากาศ</h1>
                <p style="color: #94a3b8; margin: 0;">พิกัด อ.หาดใหญ่ จ.สงขลา</p>
                
                <div class="grid">
                    <div class="card"><div class="card-title">🌡️ อุณหภูมิ</div><div class="card-value">{data['temp']} °C</div></div>
                    <div class="card"><div class="card-title">💧 ความชื้น</div><div class="card-value">{data['humidity']}%</div></div>
                    <div class="card" style="grid-column: span 2;"><div class="card-title">☁️ สภาพอากาศ</div><div class="card-value" style="color:#38bdf8;">{data['desc']}</div></div>
                    <div class="card"><div class="card-title">🌫️ PM 2.5</div><div class="card-value">{data['pm25']} µg/m³</div></div>
                    <div class="card"><div class="card-title">😷 ระดับ AQI</div><div class="card-value">{data['aqi']}</div></div>
                </div>
                
                <div class="chart-container">
                    <h3 style="margin-top:0; color:#38bdf8; font-size:16px;">📈 กราฟแนวโน้มอุณหภูมิรอบสัปดาห์ (°C)</h3>
                    <canvas id="tempChart"></canvas>
                </div>

                <div class="chart-container">
                    <h3 style="margin-top:0; color:#f43f5e; font-size:16px;">📊 กราฟสถิติมลพิษฝุ่น PM 2.5 (µg/m³)</h3>
                    <canvas id="pmChart"></canvas>
                </div>
                
                <a href="/trigger-bot" class="btn">🚀 สั่งส่งรายงานเข้า Discord ตอนนี้เลย!</a>
            </div>

            <script>
                // เรนเดอร์ กราฟอุณหภูมิ (Line Chart)
                const ctxTemp = document.getElementById('tempChart').getContext('2d');
                new Chart(ctxTemp, {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(history_data["labels"])},
                        datasets: [
                            {{ label: 'อุณหภูมิสูงสุด', data: {json.dumps(history_data["temp_max"])}, borderColor: '#f43f5e', backgroundColor: 'rgba(244,63,94,0.1)', tension: 0.3, fill: true }},
                            {{ label: 'อุณหภูมิต่ำสุด', data: {json.dumps(history_data["temp_min"])}, borderColor: '#38bdf8', backgroundColor: 'rgba(56,189,248,0.1)', tension: 0.3, fill: true }}
                        ]
                    }},
                    options: {{ responsive: true, plugins: {{ legend: {{ labels: {{ color: 'white' }} }} }}, scales: {{ x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: 'white' }} }}, y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: 'white' }} }} }} }}
                }});

                // เรนเดอร์ กราฟฝุ่น PM 2.5 (Bar Chart)
                const ctxPm = document.getElementById('pmChart').getContext('2d');
                new Chart(ctxPm, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(history_data["labels"])},
                        datasets: [{{
                            label: 'ค่าฝุ่น PM 2.5',
                            data: {json.dumps(history_data["pm25"])},
                            backgroundColor: '#fbbf24',
                            borderRadius: 6
                        }}]
                    }},
                    options: {{ responsive: true, plugins: {{ legend: {{ labels: {{ color: 'white' }} }} }}, scales: {{ x: {{ grid: {{ display: false }}, ticks: {{ color: 'white' }} }}, y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: 'white' }} }} }} }}
                }});
            </script>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

def run_web_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleServer)
    server.serve_forever()

def scheduled_worker():
    reported_0730 = False
    reported_1800 = False
    reported_summary = False
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        if current_time == "00:00":
            reported_0730, reported_1800, reported_summary = False, False, False

        if current_time == "07:30" and not reported_0730:
            send_to_discord(is_manual=False)
            reported_0730 = True
            time.sleep(60)

        if current_time == "18:00" and not reported_1800:
            send_to_discord(is_manual=False)
            reported_1800 = True
            time.sleep(60)

        if current_time == "23:59" and not reported_summary:
            send_to_discord(is_summary=True)
            reported_summary = True
            time.sleep(60)

        time.sleep(30)

if __name__ == "__main__":
    print("🚀 เปิดสวิตช์ระบบบอทเวอร์ชันมีกราฟสถิติ...")
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=scheduled_worker, daemon=True).start()
    send_to_discord(is_manual=False)
    while True:
        time.sleep(3600)