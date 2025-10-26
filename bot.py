import openai
import telebot
import os
from dotenv import load_dotenv

load_dotenv("bot.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_input = message.text
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Та Монгол хэл дээр ойлгомжтой, соёлтой хариулт өг."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.8,
            max_tokens=500
        )
        answer = response.choices[0].message["content"].strip()
        bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Алдаа гарлаа: {e}")

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
