import os
import requests
import time

# ดึงค่าจาก Environment Variables บน Render
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
WEATHER_KEY = os.getenv("OPENWEATHER_KEY")


def get_weather():
    # เปลี่ยนชื่อเมืองตามต้องการ เช่น hatyai
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
    print("✅ ส่งข้อมูลเข้า Discord เรียบร้อยแล้ว!")


if __name__ == "__main__":
    # สั่งให้ทำงานส่งข้อมูลทันทีเมื่อเปิดเครื่อง บน Render Web Service
    send_to_discord()

    # ลูปทิ้งไว้ไม่ให้ Web Service ดับอัตโนมัติ
    while True:
        time.sleep(3600)  # ทำงานซ้ำทุกๆ 1 ชั่วโมง