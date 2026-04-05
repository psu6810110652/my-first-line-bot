# my-first-line-
# Hatyai Weather Discord Bot

โปรเจคบอทรายงานสภาพอากาศอัตโนมัติสำหรับเมืองหาดใหญ่ (หรือจังหวัดอื่นๆ) ส่งข้อมูลเข้า Discord ผ่าน Webhook โดยใช้ภาษา Python 
เป็นโปรเจคเริ่มต้นเพื่อฝึกทักษะการใช้งาน API, การจัดการความปลอดภัยด้วย Environment Variables และการใช้งาน Git/GitHub

## คุณสมบัติ (Features)
- ดึงข้อมูลพยากรณ์อากาศแบบ Real-time จาก **OpenWeatherMap API**
- รายงานข้อมูล: อุณหภูมิ (°C), สภาพอากาศ (เช่น เมฆมาก, ฝนตก), และความชื้น
- ส่งการแจ้งเตือนเข้าช่องแชท **Discord** ทันทีด้วย Webhook
- รองรับการตั้งค่าความปลอดภัยผ่านไฟล์ `.env` (Best Practice)

## เทคโนโลยีที่ใช้ (Tech Stack)
- **Language:** Python 3.x
- **Libraries:** - `requests` (สำหรับดึงข้อมูล API)
  - `python-dotenv` (สำหรับจัดการค่า Config และความลับ)
- **API:** [OpenWeatherMap](https://openweathermap.org/)
- **Tools:** Git, GitHub, VS Code

## การติดตั้งและใช้งาน (Installation)

1. **Clone Repository**
   ```bash
   git clone https://github.com/psu6810110652/my-first-line-bot.git
   cd my-first-line-bot