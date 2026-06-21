import os
import discord
from discord.ext import commands, tasks
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# --- ตั้งค่า Bot ---
intents = discord.Intents.default()
intents.message_content = True # อนุญาตให้บอทอ่านข้อความ
bot = commands.Bot(command_prefix='/', intents=intents)

# --- ฟังก์ชันดึงข้อมูลอากาศ (เหมือนเดิม) ---
def get_weather():
    api_key = os.getenv("OPENWEATHER_KEY")
    city = "Songkhla"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=th"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    return None

def create_weather_embed(data):
    temp = data['main']['temp']
    desc = data['weather'][0]['description']
    icon = data['weather'][0]['icon']
    
    embed = discord.Embed(
        title=f"📍 รายงานอากาศ: {data['name']}",
        description=f"พยากรณ์อากาศล่าสุด ณ เวลา {datetime.now().strftime('%H:%M')}",
        color=discord.Color.blue() if temp < 33 else discord.Color.red(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=f"https://openweathermap.org/img/wn/{icon}@2x.png")
    embed.add_field(name="🌡️ อุณหภูมิ", value=f"{temp} °C", inline=True)
    embed.add_field(name="☁️ สภาพอากาศ", value=desc.capitalize(), inline=True)
    embed.set_footer(text="พิมพ์ /weather เพื่อดูอีกครั้ง")
    return embed

# --- 1. ระบบตอบโต้ (Commands) ---
@bot.command()
async def weather(ctx):
    """คำสั่งสำหรับดูอากาศปัจจุบัน: พิมพ์ /weather"""
    data = get_weather()
    if data:
        embed = create_weather_embed(data)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ เกิดข้อผิดพลาดในการดึงข้อมูลอากาศ")

# --- 2. ระบบตั้งเวลาส่ง (Background Task) ---
@tasks.loop(hours=24) # หรือตั้งเป็น minutes=60
async def daily_report():
    # เลือก Channel ที่ต้องการให้บอทส่ง (ก๊อป ID ห้องแชทมาใส่)
    # วิธีเอา ID: คลิกขวาที่ชื่อห้องใน Discord -> Copy Channel ID
    CHANNEL_ID = 123456789012345678 # <-- เปลี่ยนเป็น ID ห้องของคุณ
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        data = get_weather()
        if data:
            embed = create_weather_embed(data)
            await channel.send(content="🔔 รายงานประจำวันมาแล้ว!", embed=embed)

@daily_report.before_loop
async def before_daily_report():
    await bot.wait_until_ready()

# --- เหตุการณ์ตอนบอทเริ่มทำงาน ---
@bot.event
async def on_ready():
    print(f'✅ บอทออนไลน์แล้วในชื่อ: {bot.user}')
    daily_report.start() # เริ่มระบบตั้งเวลาอัตโนมัติ

# --- รันบอท ---
bot.run(os.getenv("DISCORD_TOKEN"))