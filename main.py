import os
import requests
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# พิกัดหาดใหญ่ สงขลา
LAT = "7.0084"
LON = "100.4747"

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")
LINE_TOKEN = os.getenv("LINE_NOTIFY_TOKEN") # เพิ่มเผื่อไว้ (ไม่ใส่ก็ไม่พัง)

# ตัวแปรสำหรับจดบันทึกสถิติรายวัน (Weather Logger)
daily_stats = {"max_temp": -999, "min_temp": 999, "max_pm25": 0}

# =======================================================
# 1. ฟังก์ชันดึงและประมวลผลข้อมูลสภาพอากาศ + PM 2.5
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
        
        # อัปเดตสถิติประจำวัน (Logger)
        global daily_stats
        if temp > daily_stats["max_temp"]: daily_stats["max_temp"] = temp
        if temp < daily_stats["min_temp"]: daily_stats["min_temp"] = temp
        if pm25 > daily_stats["max_pm25"]: daily_stats["max_pm25"] = pm25
        
        aqi_th = {
            1: "ดีมาก 🟢", 2: "ดี 🟢", 3: "ปานกลาง 🟡", 
            4: "เริ่มมีผลกระทบต่อสุขภาพ 🟠", 5: "มีผลกระทบต่อสุขภาพอย่างมาก 🔴"
        }.get(aqi_code, "ไม่สามารถระบุได้")
        
        status_text = "วันนี้อากาศปกติครับ" if aqi_code <= 2 else "ช่วงนี้มีฝุ่นเล็กน้อยครับ" if aqi_code == 3 else "ระวังสุขภาพด้วยนะครับ"
        
        # เลือกรูปไอคอน Thumbnail ตามสภาพอากาศจริง
        thumbnail_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
        if pm25 >= 37.5:
            thumbnail_url = "https://cdn-icons-png.flaticon.com/512/1835/1835848.png" # รูปหน้ากาก/ฝุ่นหมอก
        
        return {
            "temp": temp, "humidity": humidity, "desc": description,
            "main_weather": main_weather, "pm25": pm25, "aqi": aqi_th,
            "status": status_text, "thumbnail": thumbnail_url, "aqi_code": aqi_code
        }, None
    except Exception as e:
        return None, f"โค้ดทำงานผิดพลาด: `{str(e)}`"

# =======================================================
# 2. ฟังก์ชันส่ง LINE Notify (แถมพ่วงไว้ให้)
# =======================================================
def send_line_notify(message):
    if LINE_TOKEN:
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
        payload = {"message": message}
        requests.post(url, headers=headers, data=payload)

# =======================================================
# 3. ฟังก์ชันส่ง Embed สวยงามเข้า Discord
# =======================================================
def send_to_discord(is_manual=False, is_summary=False):
    if is_summary:
        # หากส่งสรุปสิ้นวัน
        global daily_stats
        if daily_stats["max_temp"] == -999: return
        payload = {
            "embeds": [{
                "title": "📝 สรุปสถิติสภาพอากาศรอบวัน: หาดใหญ่",
                "color": 15105570, # สีส้มทองโหมดสรุป
                "description": f"📊 **ภาพรวมสถิติตลอด 24 ชม. ที่ผ่านมา**\n"
                               f"🌡️ อุณหภูมิสูงสุด: {daily_stats['max_temp']} °C\n"
                               f"❄️ อุณหภูมิต่ำสุด: {daily_stats['min_temp']} °C\n"
                               f"🌫️ ค่าฝุ่น PM 2.5 สูงสุดพีคที่: {daily_stats['max_pm25']} µg/m³",
                "footer": {"text": "รีเซ็ตระบบบันทึกเพื่อวันถัดไป"}
            }]
        }
        requests.post(WEBHOOK_URL, json=payload)
        # รีเซ็ตค่าใหม่สำหรับวันพรุ่งนี้
        daily_stats = {"max_temp": -999, "min_temp": 999, "max_pm25": 0}
        return

    data, error = get_weather_data()
    if error:
        requests.post(WEBHOOK_URL, json={"content": f"❌ {error}"})
        return

    # ระบบแจ้งเตือนภัยด่วน (Alert System)
    alert_content = ""
    if data["pm25"] >= 37.5:
        alert_content += "⚠️ **🚨 แจ้งเตือนด่วน @everyone ค่าฝุ่น PM 2.5 เกินมาตรฐานวิกฤต!**\n"
        send_line_notify(f"⚠️ แจ้งเตือนด่วน! หาดใหญ่ค่าฝุ่น PM 2.5 เริ่มสูงวิกฤต: {data['pm25']} ug/m3")
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
                "thumbnail": {"url": data["thumbnail"]}, # ไอคอนเปลี่ยนตามสภาพอากาศจริง
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
# 4. ระบบหน้าเว็บ Live Dashboard คอนโทรลบอทหน้าตาสุดสวย
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

        # ดึงข้อมูลมาโชว์บนหน้าเว็บจริงสดๆ
        data, _ = get_weather_data()
        if not data: data = {"temp": "N/A", "humidity": "N/A", "desc": "รอระบบรีเฟรช", "pm25": "N/A", "aqi": "N/A", "status": ""}

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        # HTML + CSS ออกแบบหน้า Dashboard สไตล์โมเดิร์น
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>⛅ PSU Weather Live Dashboard</title>
            <style>
                body {{ font-family: 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #0f172a, #1e293b); color: white; margin: 0; padding: 40px 20px; display: flex; justify-content: center; }}
                .container {{ max-width: 600px; width: 100%; background: rgba(30, 41, 59, 0.7); padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); text-align: center; }}
                h1 {{ color: #38bdf8; margin-bottom: 5px; font-size: 28px; }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 25px; }}
                .card {{ background: rgba(15, 23, 42, 0.6); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }}
                .card-title {{ font-size: 14px; color: #94a3b8; margin-bottom: 5px; }}
                .card-value {{ font-size: 20px; font-weight: bold; color: #f8fafc; }}
                .btn {{ display: block; background: linear-gradient(90deg, #0284c7, #0369a1); color: white; border: none; padding: 15px; font-size: 18px; border-radius: 12px; cursor: pointer; text-decoration: none; margin-top: 30px; font-weight: bold; transition: 0.3s; box-shadow: 0 4px 15px rgba(2, 132, 199, 0.4); }}
                .btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(2, 132, 199, 0.6); }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📍 คอนโทรลบอทหาดใหญ่ สงขลา</h1>
                <p style="color: #94a3b8; margin-top:0;">ข้อมูลสดๆ บนระบบคลาวด์ขณะนี้</p>
                
                <div class="grid">
                    <div class="card">
                        <div class="card-title">🌡️ อุณหภูมิ</div>
                        <div class="card-value">{data['temp']}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">💧 ความชื้น</div>
                        <div class="card-value">{data['humidity']}</div>
                    </div>
                    <div class="card" style="grid-column: span 2;">
                        <div class="card-title">☁️ สภาพอากาศจริง</div>
                        <div class="card-value" style="color: #38bdf8;">{data['desc']}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">🌫️ ค่าฝุ่น PM 2.5</div>
                        <div class="card-value">{data['pm25']}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">😷 ระดับ AQI</div>
                        <div class="card-value">{data['aqi']}</div>
                    </div>
                </div>
                
                <a href="/trigger-bot" class="btn">🚀 สั่งส่งรายงานเข้า Discord ตอนนี้เลย!</a>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

def run_web_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleServer)
    server.serve_forever()

# =======================================================
# 5. ระบบตั้งเวลาส่งประจำวัน + บันทึกสถิติ (Scheduled Reports)
# =======================================================
def scheduled_worker():
    reported_0730 = False
    reported_1800 = False
    reported_summary = False
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # รีเซ็ตสิทธิ์การส่งตอนเที่ยงคืน
        if current_time == "00:00":
            reported_0730 = False
            reported_1800 = False
            reported_summary = False

        # 1. ส่งตอนเช้า 07:30 น.
        if current_time == "07:30" and not reported_0730:
            send_to_discord(is_manual=False)
            reported_0730 = True
            time.sleep(60)

        # 2. ส่งตอนเย็น 18:00 น.
        if current_time == "18:00" and not reported_1800:
            send_to_discord(is_manual=False)
            reported_1800 = True
            time.sleep(60)

        # 3. ยิงสถิติภาพรวมประจำวันรอบดึก 23:59 น. (Weather Logger)
        if current_time == "23:59" and not reported_summary:
            send_to_discord(is_summary=True)
            reported_summary = True
            time.sleep(60)

        time.sleep(30)

# =======================================================
# 6. จุดเริ่มต้นระบบ
# =======================================================
if __name__ == "__main__":
    print("🚀 ระบบ Super Weather Bot เวอร์ชันเทพกำลังเปิดระบบ...")
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=scheduled_worker, daemon=True).start()
    
    # ส่งทักทายรอบแรกในดิสคอร์ดทันทีที่เปิดเครื่อง
    send_to_discord(is_manual=False)
    
    while True:
        time.sleep(3600)