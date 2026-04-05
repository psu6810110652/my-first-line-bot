import requests

def send_discord_message(msg):
    # วาง Webhook URL ที่ก๊อปมาในเครื่องหมายคำพูดด้านล่าง
    webhook_url = 'https://discord.com/api/webhooks/1490365197335007425/ywp1n0MkO6Bc2rIDnxSUiAaNOrHtKhABUDvD60IO3EhdgIKyNNS5fvPxRetfLYQCp1v3'
    
    # ข้อมูลที่จะส่ง (Discord รับค่าเป็น Dictionary ที่มี Key ชื่อ 'content')
    data = {
        "content": msg,
        "username": "My Python Bot" # ตั้งชื่อบอทที่จะโชว์ในห้องแชท
    }
    
    # ส่งข้อมูลแบบ POST
    response = requests.post(webhook_url, json=data)
    
    if response.status_code == 204: # Discord ส่งสำเร็จจะคืนค่า 204
        print("ส่งเข้า Discord สำเร็จ!")
    else:
        print(f"พังจ้า! Error Code: {response.status_code}")

# ลองใช้งาน
send_discord_message("เย้! บอทตัวแรกใน Discord ของผมทำงานได้แล้ว")