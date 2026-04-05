import os
import requests
from dotenv import load_dotenv

# โหลดข้อมูลจากไฟล์ .env
load_dotenv()

def ดึงอากาศหาดใหญ่():
    # ดึงค่าจาก .env มาเก็บในตัวแปร
    api_key = os.getenv("OPENWEATHER_KEY")
    city = "Songkhla"
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=th"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            สภาพอากาศ = data['weather'][0]['description']
            อุณหภูมิ = data['main']['temp']
            ความชื้น = data['main']['humidity']
            
            ข้อความ = (
                f"📊 **รายงานสภาพอากาศเมือง {city}**\n"
                f"🌡️ อุณหภูมิ: {อุณหภูมิ}°C\n"
                f"☁️ สภาพอากาศ: {สภาพอากาศ}\n"
                f"💧 ความชื้น: {ความชื้น}%"
            )
            return ข้อความ
        else:
            return f"❌ Error จาก OpenWeather: {data.get('message', 'รหัส API อาจยังไม่พร้อมใช้งาน')}"
            
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}"

def ส่งเข้าDiscord(ข้อความ):
    # ดึงค่า Webhook จาก .env
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    if not webhook_url:
        print("❌ ไม่พบลิงก์ Webhook ในไฟล์ .env")
        return

    payload = {"content": ข้อความ}
    try:
        res = requests.post(webhook_url, json=payload)
        if res.status_code == 204:
            print("✅ ส่งเข้า Discord สำเร็จแล้ว!")
        else:
            print(f"⚠️ ส่งไม่สำเร็จ (Code: {res.status_code})")
    except Exception as e:
        print(f"❌ ระบบส่ง Discord พัง: {e}")

if __name__ == "__main__":
    print("กำลังเริ่มทำงานโดยใช้ค่าจากไฟล์ .env...")
    สรุปอากาศ = ดึงอากาศหาดใหญ่()
    print("-" * 30)
    print(สรุปอากาศ)
    print("-" * 30)
    ส่งเข้าDiscord(สรุปอากาศ)