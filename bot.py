import os
import telebot
from dotenv import load_dotenv
from openai import OpenAI

# .env ачаалж байна
load_dotenv("bot.env")

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Сайн уу, би EduHub-ийн ухаалаг туслах бот байна 🤖\nАсуух зүйлээ бичээрэй!")

@bot.message_handler(func=lambda message: True)
def ai_reply(message):
    user_text = message.text

    # OpenAI руу хүсэлт илгээж байна
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a friendly AI tutor who helps students understand and learn."},
            {"role": "user", "content": user_text}
        ]
    )

    reply_text = response.choices[0].message.content.strip()
    bot.reply_to(message, reply_text)

if __name__ == "__main__":
    print("🤖 AI Telegram Bot is running...")
    bot.infinity_polling()
