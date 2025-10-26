import os
import openai
import telebot
from dotenv import load_dotenv

load_dotenv("bot.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_input = message.text
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Та Монгол хэл дээр ойлгомжтой, соёлтой хариу өгдөг AI багш юм."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.8,
            max_tokens=500
        )
        answer = completion.choices[0].message["content"].strip()
        bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Алдаа гарлаа: {e}")

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
