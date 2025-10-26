import os
import openai
import telebot
from dotenv import load_dotenv

load_dotenv("bot.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

# -------------------------
# INTENT DETECTION FUNCTION
# -------------------------
def detect_intent(txt):
    t = txt.lower()

    if any(x in t for x in ["сайн уу", "sain uu", "hi", "hello"]):
        return "greeting"

    if "англи" in t or "english" in t:
        return "learn_english"

    if any(x in t for x in ["speaking", "ярих", "ярьж", "говорить"]):
        return "speaking"

    if any(x in t for x in ["үг", "vocab", "vocabulary", "үг цээж", "word"]):
        return "vocab"

    return "fallback"

# -------------------------
# RESPONSE MESSAGES
# -------------------------
RESPONSE_GREETING = (
    "Сайн байна уу! 👋\n"
    "Би англи хэл сурахад туслах туслах-ассистент байна.\n\n"
    "Та яг одоо юу хүсэж байна вэ? 😊\n"
    "1. Англи хэлний үгс сурмаар байна\n"
    "2. Ярианы чадвараа сайжруулмаар байна\n"
    "3. Шинэ эхлэгч, хаанаас эхлэхээ мэдэхгүй байна\n\n"
    "Тохирох дугаарыг бичээд явуулаарай (жишээ: 3)"
)

RESPONSE_LEARN_ENGLISH = (
    "Сайн уу! 🤗 Англи хэл сурахад чинь би тусална.\n\n"
    "Чамд яг одоо аль нь хэрэгтэй вэ? Доороос сонгоорой 👇\n"
    "1️⃣ Үг цээжлэх (өдөрт 10 шинэ үг жишээ өгүүлбэртэй)\n"
    "2️⃣ Ярих дадлага (чөлөөтэй ярихад зориулсан асуултууд)\n"
    "3️⃣ Шалгалт / түвшин тогтоох (чиний одоогийн түвшинг оношлоод зөвлөмж өгнө)\n\n"
    "Дугаарыг нь бичээд явуулчих: 1, 2 эсвэл 3 ✍️"
)

RESPONSE_SPEAKING = (
    "Гайхалтай сонголт 🗣️\n\n"
    "Ярих чадварыг сайжруулахын тулд бид ингэж ажиллана:\n"
    "- Би асуулт асууна (жишээ нь: \"Өнөөдөр өдөр нь ямар байсан бэ?\")\n"
    "- Чи богино хариулт англиар бичнэ\n"
    "- Би чиний өгүүлбэрийг засаж, илүү natural хувилбар санал болгоно\n\n"
    "Бэлэн үү? 😎 Тэгвэл эхний асуулт:\n"
    "👉 What did you do today?\n"
    "Англиар 1-2 өгүүлбэрээр бичээд явуул. "
)

RESPONSE_VOCAB = (
    "Үгнээс нь эхэлье 📚\n\n"
    "Day 1-ийн 3 үг:\n"
    "1. improve – сайжруулах\n"
    "   Example: I want to improve my English.\n"
    "2. confident – итгэлтэй, өөртөө итгэлтэй\n"
    "   Example: I feel confident when I speak English.\n"
    "3. practice – дадлага хийх\n"
    "   Example: I practice English every day.\n\n"
    "Дахиад 3 үг авах уу? \"тэгье\" гэж бичээрэй 💪"
)

RESPONSE_FALLBACK = (
    "Сайн уу! 😊 Би англи хэл сурахад чинь чиглүүлэхээр энд байна.\n\n"
    "Доорх сонголтоос алийг нь хүсэж байна вэ?\n"
    "1️⃣ Үг цээжлэх\n"
    "2️⃣ Ярианы дадлага\n"
    "3️⃣ Түвшин тогтоох шалгалт\n\n"
    "Зөвхөн дугаарыг бичээд явуулчих 💬"
)

# -------------------------
# MAIN HANDLER
# -------------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text.strip()
    intent = detect_intent(user_input)

    if intent == "greeting":
        reply = RESPONSE_GREETING
    elif intent == "learn_english":
        reply = RESPONSE_LEARN_ENGLISH
    elif intent == "speaking":
        reply = RESPONSE_SPEAKING
    elif intent == "vocab":
        reply = RESPONSE_VOCAB
    else:
        reply = RESPONSE_FALLBACK

    bot.send_message(message.chat.id, reply)

# -------------------------
# BOT START
# -------------------------
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
