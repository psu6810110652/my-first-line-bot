import os
import requests
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

# 1. โหลดค่าจากไฟล์ .env
load_dotenv()

def ดึงข้อมูลอากาศ():
    api_key = os.getenv("OPENWEATHER_KEY")
    city = "Songkhla" # หรือเปลี่ยนเป็น Hatyai
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=th"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            return data
        else:
            print(f"❌ Error API: {data.get('message')}")
            return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def ส่งเข้าDiscord(data):
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    if not data:
        return

    # ดึงค่าที่ต้องการจาก JSON
    temp = data['main']['temp']
    weather_desc = data['weather'][0]['description']
    humidity = data['main']['humidity']
    city_name = data['name']
    icon_code = data['weather'][0]['icon']
    
    # เลือกสีแถบข้อความ (Embed Color) ตามอุณหภูมิ
    # สีใช้เลข Decimal (เช่น 16711680 คือสีแดง, 3447003 คือสีฟ้า)
    embed_color = 16711680 if temp > 32 else 3447003 

    # สร้างโครงสร้าง Embed ให้สวยงาม
    payload = {
        "username": "Weather Bot",
        "avatar_url": "https://openweathermap.org/img/wn/01d@2x.png",
        "embeds": [{
            "title": f"📍 รายงานอากาศ: {city_name}",
            "description": f"ขณะนี้เวลา: {datetime.now().strftime('%H:%M:%S')}",
            "color": embed_color,
            "thumbnail": {
                "url": f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
            },
            "fields": [
                {
                    "name": "🌡️ อุณหภูมิ",
                    "value": f"{temp} °C",
                    "inline": True
                },
                {
                    "name": "💧 ความชื้น",
                    "value": f"{humidity}%",
                    "inline": True
                },
                {
                    "name": "☁️ สภาพอากาศ",
                    "value": weather_desc.capitalize(),
                    "inline": False
                }
            ],
            "footer": {
                "text": "พัฒนาโดย PSU Computer Engineering Student"
            },
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

    res = requests.post(webhook_url, json=payload)
    if res.status_code == 204:
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] ส่งข้อมูลสำเร็จ!")
    else:
        print(f"⚠️ ส่งไม่สำเร็จ: {res.status_code}")

# 2. ฟังก์ชันหลักที่จะให้ Schedule เรียกใช้
def job():
    print("--- กำลังเริ่มทำงานตามรอบเวลา ---")
    weather_data = ดึงข้อมูลอากาศ()
    ส่งเข้าDiscord(weather_data)

# 3. ตั้งเวลาการทำงาน
# ลองรันทันที 1 ครั้งเพื่อทดสอบ
job() 

# ตั้งให้ทำงานทุกวัน (เปลี่ยนเวลาได้ตามใจชอบ)
schedule.every().day.at("07:00").do(job)
schedule.every().day.at("12:00").do(job)
schedule.every().day.at("18:00").do(job)

# หรือถ้าอยากทดสอบทุก 1 นาที ให้ปลดคอมเมนต์บรรทัดข้างล่างนี้:
# schedule.every(1).minutes.do(job)

print("🚀 บอทรายงานอากาศเริ่มทำงานแล้ว (กด Ctrl+C เพื่อหยุด)")

# 4. Loop เพื่อให้โปรแกรมรันค้างไว้รอเวลา
while True:
    schedule.run_pending()
    time.sleep(1)