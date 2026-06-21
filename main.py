import os
import requests
import time

# ดึงค่าจาก Environment บน Render (ที่เราแก้ไปล่าสุด)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")

def get_weather():
    # ดึงสภาพอากาศเมืองหาดใหญ่
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
    # ส่งข้อมูลตรงเข้า Discord ผ่านลิงก์ Webhook
    requests.post(WEBHOOK_URL, json=payload)
    print("✅ ส่งข้อมูลสภาพอากาศเข้า Discord เรียบร้อยแล้ว!")

if __name__ == "__main__":
    # ทำงานทันทีเมื่อเปิดเครื่องบน Render
    send_to_discord()

    # ลูปเปิดเครื่องทิ้งไว้ไม่ให้ Render ดับชั่วคราว
    while True:
        time.sleep(3600)  # ส่งซ้ำทุกๆ 1 ชั่วโมง