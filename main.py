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
        main_weather = w_res["weather"][0]["main"] # ดูประเภทสภาพอากาศหลัก (เช่น Rain)
        
        pm25 = p_res["list"][0]["components"]["pm2_5"]
        aqi_code = p_res["list"][0]["main"]["aqi"]
        
        aqi_th = {
            1: "ดีมาก 🟢", 2: "ดี 🟢", 3: "ปานกลาง 🟡", 
            4: "เริ่มมีผลกระทบต่อสุขภาพ 🟠", 5: "มีผลกระทบต่อสุขภาพอย่างมาก 🔴"
        }.get(aqi_code, "ไม่สามารถระบุได้")
        
        status_text = "วันนี้อากาศปกติครับ" if aqi_code <= 2 else "ช่วงนี้มีฝุ่นเล็กน้อยครับ" if aqi_code == 3 else "ระวังสุขภาพด้วยนะครับ"
        
        data = {
            "temp": f"{temp} °C",
            "humidity": f"{humidity}%",
            "desc": description,
            "main_weather": main_weather,
            "pm25": pm25,  # เก็บเป็นตัวเลขไว้เช็กเงื่อนไขแจ้งเตือน
            "aqi": aqi_th,
            "status": status_text
        }
        return data, None
    except Exception as e:
        return None, f"โค้ดทำงานผิดพลาด: `{str(e)}`"

# =======================================================
# 2. ฟังก์ชันจัดฟอร์แมต Embed และยิงเข้า Discord
# =======================================================
def send_to_discord(is_manual=False):
    data, error = get_weather_data()
    if error:
        requests.post(WEBHOOK_URL, json={"content": f"❌ {error}"})
        return

    # ลำดับข้อความแจ้งเตือนด่วน (Alert System)
    alert_content = ""
    if data["pm25"] >= 37.5:
        alert_content += "⚠️ **🚨 แจ้งเตือนภัยด่วน @everyone ค่าฝุ่น PM 2.5 เกินมาตรฐานขั้นวิกฤตแล้ว!**\n"
    if "rain" in data["main_weather"].lower():
        alert_content += "🌧️ **🚨 แจ้งเตือนด่วน @everyone ขณะนี้ตรวจพบกลุ่มฝนในพื้นที่หาดใหญ่ โปรดเตรียมพกร่มด้วยครับ!**\n"

    # ถ้ากดส่งเองแบบแมนนวล ให้ขึ้นหัวข้อบอกนิดนึง
    footer_text = "เรียกดูข้อมูลสดใหม่ตามคำขอผ่านหน้าเว็บ" if is_manual else "รายงานอัตโนมัติประจำวัน"

    payload = {
        "content": alert_content if alert_content != "" else None, # ถ้ามีเคสเตือนภัยด่วนจะแท็กทุกคนทันที
        "embeds": [
            {
                "title": "📍 รายงานอากาศ & มลพิษ: จังหวัดสงขลา (หาดใหญ่)",
                "description": f"✅ {data['status']}",
                "color": 3447003,
                "fields": [
                    {"name": "🌡️ อุณหภูมิ", "value": data["temp"], "inline": True},
                    {"name": "💧 ความชื้น", "value": data["humidity"], "inline": True},
                    {"name": "☁️ สภาพ", "value": data["desc"], "inline": True},
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
# 3. ระบบหน้าเว็บสำหรับกดปุ่มสั่งงาน (Web Interface)
# =======================================================
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        # หากมีการกดปุ่ม หน้าเว็บจะวิ่งมาที่พาร์ท /trigger-bot
        if self.path == "/trigger-bot":
            send_to_discord(is_manual=True)
            # เด้งป๊อปอัปบอกว่าส่งสำเร็จแล้วลิ้งก์กลับหน้าเดิม
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
                <script>
                    alert("\xe0\xb8\xaa\xe0\xb9\x88\xe0\xb8\x87\xe0\xb8\x82\xe0\xb9\x89\xe0\xb8\xa4\xe0\xb8\x84\xe0\xb8\xa7\xe0\xb8\xb2\xe0\xb8\xa1\xe0\xb9\x80\xe0\xb8\x82\xe0\xb9\x89\xe0\xb8\xb2 Discord \xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\xb5\xe0\xb8\xa2\xe0\xb8\xb9\xe0\xb8\xa3\xe0\xb9\x89\xe0\xb8\xad\xe0\xb8\xa2\xe0\xb9\x81\xe0\xb8\xa5\xe0\xb9\x89\xe0\xb8\xa7\xe0\xb8\x84\xe0\xb8\xa3\xe0\xb8\xb1\xe0\xb8\xb1\xe0\xb8\x9a! \xf0\x9f\x8e\x89");
                    window.location.href = "/";
                </script>
            """)
            return

        # หน้าตาหน้าเว็บไซต์หลักแบบมีปุ่มกดสวยๆ
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PSU Weather Guard Control</title>
            <style>
                body { font-family: 'Arial', sans-serif; background-color: #f0f2f5; text-align: center; padding-top: 50px; }
                .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: inline-block; }
                h1 { color: #1e3a8a; }
                .btn { background-color: #0284c7; color: white; border: none; padding: 15px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; transition: 0.3s; }
                .btn:hover { background-color: #0369a1; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🌤️ PSU Weather Guard Control Panel</h1>
                <p>ระบบบอทรายงานสภาพอากาศและฝุ่น PM 2.5 อำเภอหาดใหญ่ กำลังรันอยู่บนระบบคลาวด์...</p>
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
# 4. ลูปเช็กเวลาเพื่อส่งรายงานตามตาราง (Scheduled Thread)
# =======================================================
def scheduled_worker():
    print("⏰ ระบบตั้งเวลาทำงาน (07:30 และ 18:00) เริ่มต้นสแตนด์บายแล้ว...")
    reported_0730 = False
    reported_1800 = False
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # คืนค่าสถานะเมื่อข้ามวันใหม่เพื่อเตรียมส่งในวันถัดไป
        if current_time == "00:00":
            reported_0730 = False
            reported_1800 = False

        # ส่งตอนเช้า 07:30 น.
        if current_time == "07:30" and not reported_0730:
            send_to_discord(is_manual=False)
            reported_0730 = True
            time.sleep(60) # หลับ 1 นาทีป้องกันการส่งซ้ำในนาทีเดียวกัน

        # ส่งตอนเย็น 18:00 น.
        if current_time == "18:00" and not reported_1800:
            send_to_discord(is_manual=False)
            reported_1800 = True
            time.sleep(60)

        time.sleep(30) # ตื่นมาเช็กเวลาทุกๆ 30 วินาที

# =======================================================
# 5. จุดเริ่มต้นโปรแกรมหลัก
# =======================================================
if __name__ == "__main__":
    # 1. เปิดหน้าเว็บคอนโทรลแยกไว้
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # 2. เปิดระบบตรวจจับเวลาทำงานเบื้องหลัง
    threading.Thread(target=scheduled_worker, daemon=True).start()
    
    # 3. ยิงทักทายตอนเปิดระบบครั้งแรกบน Render ให้ชื่นใจ
    send_to_discord(is_manual=False)
    
    # ประคองไม่ให้โค้ดหลักหลับ
    while True:
        time.sleep(3600)