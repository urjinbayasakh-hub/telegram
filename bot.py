import os
import telebot

# Environment variables
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Сайн уу, Би Байсагийн Telegram бот байна 🤖")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
