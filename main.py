import os
import requests
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# =======================================================
# 1. ระบบ Web Server หลอก (Port Binding) เพื่อให้ Render รันผ่าน
# =======================================================
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is running beautifully!")

def run_web_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleServer)
    server.serve_forever()

# =======================================================
# 2. ฟังก์ชันดึงสภาพอากาศ + ค่าฝุ่น PM 2.5 (พิกัดหาดใหญ่)
# =======================================================
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")

# พิกัดหาดใหญ่ แม่นยำ 100% ไม่เจอปัญหา City Not Found
LAT = "7.0084"
LON = "100.4747"

def get_weather_data():
    # ลิงก์ดึงสภาพอากาศหลัก
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={WEATHER_KEY}&units=metric&lang=th"
    # ลิงก์ดึงค่ามลพิษทางอากาศ (AQI / PM2.5)
    pollution_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={WEATHER_KEY}"
    
    try:
        w_res = requests.get(weather_url).json()
        p_res = requests.get(pollution_url).json()
        
        if w_res.get("cod") != 200:
            return None, f"OpenWeather Error: `{w_res.get('message')}`"
            
        # ดึงค่าจากสภาพอากาศ
        temp = w_res["main"]["temp"]
        humidity = w_res["main"]["humidity"]
        description = w_res["weather"][0]["description"]
        
        # ดึงค่าจากมลพิษทางอากาศ
        pm25 = p_res["list"][0]["components"]["pm2_5"]
        aqi_code = p_res["list"][0]["main"]["aqi"]
        
        # แปลงระดับ AQI ของ OpenWeather (1-5) ให้เป็นข้อความภาษาไทย
        aqi_th = {
            1: "ดีมาก 🟢",
            2: "ดี 🟢",
            3: "ปานกลาง 🟡",
            4: "เริ่มมีผลกระทบต่อสุขภาพ 🟠",
            5: "มีผลกระทบต่อสุขภาพอย่างมาก 🔴"
        }.get(aqi_code, "ไม่สามารถระบุได้")
        
        # สรุปภาพรวมอากาศ
        status_text = "วันนี้อากาศปกติครับ" if aqi_code <= 2 else "ช่วงนี้มีฝุ่นเล็กน้อยครับ" if aqi_code == 3 else "ระวังสุขภาพด้วยนะครับ"
        
        # จัดข้อมูลส่งกลับในรูปแบบ Dictionary เพื่อไปใส่ใน Embed
        data = {
            "temp": f"{temp} °C",
            "humidity": f"{humidity}%",
            "desc": description,
            "pm25": f"{pm25} µg/m³",
            "aqi": aqi_th,
            "status": status_text
        }
        return data, None
        
    except Exception as e:
        return None, f"โค้ดทำงานผิดพลาด: `{str(e)}`"

def send_to_discord():
    data, error = get_weather_data()
    
    # ถ้าดึงข้อมูลไม่สำเร็จ ให้ส่งข้อความแจ้งเตือนข้อผิดพลาดธรรมดา
    if error:
        payload = {"content": f"❌ {error}"}
        requests.post(WEBHOOK_URL, json=payload)
        return

    # สร้างโครงสร้างกล่องข้อความ Embed สวยงามแบบในรูปเดิมเป๊ะๆ
    payload = {
        "embeds": [
            {
                "title": "📍 รายงานอากาศ & มลพิษ: จังหวัดสงขลา (หาดใหญ่)",
                "description": f"✅ {data['status']}",
                "color": 3447003,  # สีฟ้าสว่าง (ตรงกับแถบสีในรูป)
                "fields": [
                    {
                        "name": "🌡️ อุณหภูมิ",
                        "value": data["temp"],
                        "inline": True
                    },
                    {
                        "name": "💧 ความชื้น",
                        "value": data["humidity"],
                        "inline": True
                    },
                    {
                        "name": "☁️ สภาพ",
                        "value": data["desc"],
                        "inline": True
                    },
                    {
                        "name": "😷 คุณภาพอากาศ (AQI)",
                        "value": data["aqi"],
                        "inline": True
                    },
                    {
                        "name": "🌫️ PM 2.5",
                        "value": data["pm25"],
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"อัปเดตล่าสุด: สแตนด์บายอัตโนมัติทุกๆ 1 ชั่วโมง"
                }
            }
        ]
    }
    
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json=payload)
        print("✅ ส่ง Embed สภาพอากาศและมลพิษเข้า Discord สวยงามเรียบร้อย!")

# =======================================================
# 3. จุดเริ่มต้นการทำงาน
# =======================================================
if __name__ == "__main__":
    print("🚀 บอทกล่อง Embed สวยงามกำลังเริ่มทำงาน...")
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # ส่งครั้งแรกทันทีที่เปิดเซิร์ฟเวอร์
    send_to_discord()

    while True:
        time.sleep(3600)  # ส่งซ้ำอัตโนมัติทุกๆ 1 ชั่วโมง
        send_to_discord()