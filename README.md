# 🌤️ Hatyai Weather Discord Bot (Cloud Edition)

โปรเจคบอทรายงานสภาพอากาศอัตโนมัติสำหรับเมืองหาดใหญ่ ส่งข้อมูลเข้า Discord ในรูปแบบ Embed ที่สวยงาม โดยทำงานอัตโนมัติ 24/7 บนระบบ Cloud

## 🚀 คุณสมบัติ (Features)
- **Real-time Data:** ดึงข้อมูลสภาพอากาศแม่นยำจาก OpenWeatherMap API
- **Rich Visuals:** ส่งข้อความรูปแบบ **Discord Embeds** พร้อมแถบสีตามอุณหภูมิและไอคอนสภาพอากาศ
- **Automation:** ตั้งเวลาส่งรายงานอัตโนมัติทุกเช้าและเย็นด้วย Library `schedule`
- **Cloud Deployment:** รันโปรแกรมบน **PythonAnywhere** ทำให้ทำงานได้ตลอด 24 ชั่วโมงโดยไม่ต้องเปิดคอมพิวเตอร์ทิ้งไว้
- **Security:** จัดการความลับ (API Key/Webhook) ผ่านไฟล์ `.env` อย่างปลอดภัย

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)
- **Language:** Python 3.10+
- **Libraries:** `requests`, `python-dotenv`, `schedule`
- **Infrastructure:** PythonAnywhere (Cloud Hosting)
- **API:** OpenWeatherMap API

## 🏗️ โครงสร้างระบบ (System Architecture)



1. **Trigger:** ระบบ Schedule ตรวจพบว่าถึงเวลาที่กำหนด (เช่น 07:00 น.)
2. **Data Fetch:** Python ส่งคำขอไปยัง OpenWeather API เพื่อรับข้อมูล JSON
3. **Processing:** ระบบคำนวณสี Embed และจัดรูปแบบข้อความภาษาไทย
4. **Notification:** ส่งข้อมูลไปยัง Discord Webhook เพื่อแสดงผลใน Channel

## 📦 การติดตั้งและใช้งาน (Local Setup)

1. **Clone & Install:**
   ```bash
   git clone [https://github.com/ช](https://github.com/ช)ื่อยูสเซอร์ของคุณ/my-first-line-bot.git
   pip install requests python-dotenv schedule