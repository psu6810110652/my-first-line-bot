import os
import requests
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. ระบบเปิด Port หลอกเพื่อให้ Render ผ่านด่าน (Port Binding)
class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleServer)
    print(f"🌍 Web Server Started on port {port}")
    server.serve_forever()

# 2. ฟังก์ชันบอทส่งสภาพอากาศเดิมของคุณ
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=hatyai&appid={WEATHER_KEY}&units=metric&lang=th"
    response = requests.get(url).json()
    if response.get("cod") == 200:
        temp = response["main"]["temp"]
        description = response["weather"][0]["description"]
        return f"📊 **รายงานสภาพอากาศ หาดใหญ่**\n🌡️ อุณหภูมิ: {temp}°C\n☁️ สภาพอากาศ: {description}"
    return "❌ ไม่สามารถดึงข้อมูลสภาพอากาศได้"

def send_to_discord():
    message = get_weather()
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)
    print("✅ ส่งข้อมูลสภาพอากาศเข้า Discord เรียบร้อยแล้ว!")

if __name__ == "__main__":
    # สั่งรัน Web Server หลอกแยกเป็นอีกโปรเซสหนึ่ง
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # ส่งข้อความเข้า Discord ทันที
    send_to_discord()

    # ลูปทำงานทุกๆ 1 ชั่วโมง
    while True:
        time.sleep(3600)