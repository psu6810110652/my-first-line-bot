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
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    # ดึงพอร์ตที่ Render กำหนดมา ถ้าไม่มีจะใช้พอร์ต 10000 เป็นค่าเริ่มต้น
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleServer)
    print(f"🌍 เซิร์ฟเวอร์หลอกเปิดใช้งานแล้วที่พอร์ต: {port}")
    server.serve_forever()

# =======================================================
# 2. ฟังก์ชันหลักสำหรับดึงข้อมูลสภาพอากาศและส่งเข้า Discord
# =======================================================
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")

def get_weather():
    # ส่งคำขอไปที่ OpenWeather API (เลือกเมืองหาดใหญ่)
    url = f"https://api.openweathermap.org/data/2.5/weather?lat=7.0084&lon=100.4747&appid={WEATHER_KEY}&units=metric&lang=th"
    
    try:
        response = requests.get(url).json()
        
        # ถ้าดึงข้อมูลสำเร็จ (Status Code: 200)
        if response.get("cod") == 200:
            temp = response["main"]["temp"]
            description = response["weather"][0]["description"]
            return f"📊 **รายงานสภาพอากาศ หาดใหญ่**\n🌡️ อุณหภูมิปัจจุบัน: {temp}°C\n☁️ สภาพอากาศ: {description}"
        
        # กรณี OpenWeather ส่งข้อความเออเร่อกลับมา (เช่น คีย์ยังไม่พร้อมใช้)
        error_msg = response.get("message", "Unknown Error")
        return f"❌ ดึงข้อมูลไม่สำเร็จเนื่องจากระบบ OpenWeather แจ้งว่า: `{error_msg}` (Code: {response.get('cod')})\n💡 *คำแนะนำ: ถ้าเป็น API Key พึ่งสมัครใหม่ อาจจะต้องรอระบบเปิดใช้งาน 1-2 ชั่วโมงนะครับ*"
        
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาดในระบบโค้ด: `{str(e)}`"

def send_to_discord():
    message = get_weather()
    payload = {"content": message}
    
    if WEBHOOK_URL:
        # ยิงข้อความตรงเข้า Discord Channel ผ่าน Webhook ลิงก์
        requests.post(WEBHOOK_URL, json=payload)
        print("✅ สั่งยิงข้อความรายงานผลเข้า Discord เรียบร้อยแล้ว!")
    else:
        print("⚠️ ไม่สามารถส่งได้เนื่องจากหาค่า DISCORD_WEBHOOK ไม่เจอใน Environment")

# =======================================================
# 3. จุดเริ่มต้นการทำงานของโปรแกรม (Main)
# =======================================================
if __name__ == "__main__":
    print("🚀 บอทกำลังเริ่มทำงาน...")
    
    # สั่งให้ Web Server หลอกทำงานแยกเป็นเบื้องหลัง (Background Thread)
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # สั่งให้ส่งข้อมูลสภาพอากาศเข้าดิสคอร์ดทันทีที่เปิดเครื่องครั้งแรก
    send_to_discord()

    # สั่งให้บอทลูปทำงานซ้ำทุกๆ 1 ชั่วโมง (3600 วินาที)
    print("⏰ บอทเข้าสู่โหมดสแตนด์บาย จะส่งข้อมูลใหม่ในอีก 1 ชั่วโมง...")
    while True:
        time.sleep(3600)
        send_to_discord()