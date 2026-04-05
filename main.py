import requests

def ดึงอากาศแบบละเอียด():
    api_key = "bbd8caa9d8154d4ddbe8251ac7985e27"
    city = "Songkhla"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=th"
    
    response = requests.get(url)
    data = response.json()
    
    # --- เพิ่มส่วนนี้เพื่อเช็ก Error ---
    if response.status_code != 200:
        return f"❌ เกิดข้อผิดพลาดจาก API: {data.get('message', 'ไม่ทราบสาเหตุ')}"
    # ------------------------------
    
    สภาพอากาศ = data['weather'][0]['description']
    อุณหภูมิ = data['main']['temp']
    
    return f"📍 {city}: {สภาพอากาศ}, อุณหภูมิ {อุณหภูมิ}°C"

def ส่งไปDiscord(ข้อความ):
    webhook_url = 'https://discord.com/api/webhooks/1490365197335007425/ywp1n0MkO6Bc2rIDnxSUiAaNOrHtKhABUDvD60IO3EhdgIKyNNS5fvPxRetfLYQCp1v3'
    requests.post(webhook_url, json={"content": ข้อความ})

if __name__ == "__main__":
    ผลลัพธ์ = ดึงอากาศแบบละเอียด()
    print(ผลลัพธ์) # ปริ้นดูใน Terminal ก่อน
    ส่งไปDiscord(ผลลัพธ์)