import os
import openai
import telebot
from dotenv import load_dotenv

# -------------------------
# ТОХИРГОО
# -------------------------
load_dotenv("bot.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

# -------------------------
# CONTEXT / STATE ХАДГАЛАХ MAP
# -------------------------
user_context = {}  # хэрэглэгчийн чат түүх
user_stage = {}    # хэрэглэгчийн одоогийн шат (e.g. placement test)

# -------------------------
# INTENT DETECTION
# -------------------------
def detect_intent(txt):
    t = txt.lower()

    if any(x in t for x in ["сайн уу", "sain uu", "hi", "hello"]):
        return "greeting"

    if any(x in t for x in ["3", "түвшин", "test", "exam", "placement"]):
        return "placement_test"

    if "англи" in t or "english" in t:
        return "learn_english"

    if any(x in t for x in ["speaking", "ярих", "ярьж", "говорить"]):
        return "speaking"

    if any(x in t for x in ["үг", "vocab", "vocabulary", "үг цээж", "word"]):
        return "vocab"

    return "fallback"

# -------------------------
# READY-MADE RESPONSES
# -------------------------
RESPONSE_GREETING = (
    "Сайн байна уу! 👋\n"
    "Би англи хэл сурахад чинь туслах AI багш байна.\n\n"
    "Та яг одоо юу хүсэж байна вэ? 😊\n"
    "1️⃣ Үг цээжлэх\n"
    "2️⃣ Ярианы дадлага\n"
    "3️⃣ Түвшин тогтоох шалгалт\n\n"
    "Тохирох дугаарыг бичээд явуулаарай (жишээ: 3)"
)

RESPONSE_FALLBACK = (
    "Би туслахад бэлэн байна 😊\n"
    "Та яг юу хийхийг хүсэж байна вэ?\n"
    "1️⃣ Үг цээжлэх\n"
    "2️⃣ Ярианы дадлага\n"
    "3️⃣ Түвшин тогтоох шалгалт"
)

# -------------------------
# LEVEL TEST QUESTIONS
# -------------------------
LEVEL_QUESTIONS = [
    "1️⃣ What time do you usually wake up?",
    "2️⃣ Complete this sentence: 'If I had more time, I ______.'",
    "3️⃣ Translate this: 'Би өдөр бүр англи хэл сурдаг.'",
    "4️⃣ Which is correct: 'He go to work' or 'He goes to work'?",
    "5️⃣ Write one short sentence about your favorite hobby."
]

# -------------------------
# MAIN HANDLER
# -------------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.is_bot:
        return

    chat_id = message.chat.id
    user_input = message.text.strip()
    intent = detect_intent(user_input)

    # Хэрэглэгчийн context эхлүүлэх
    if chat_id not in user_context:
        user_context[chat_id] = [
            {"role": "system", "content": (
                "Та англи хэл сурагчид тусалдаг AI багш. "
                "Хариулт чинь ойлгомжтой, найрсаг, товч, зааварлаг байх ёстой. "
                "Монгол хэлээр тайлбар хийж, англи хэлний жишээг оруул. "
                "Хэрвээ сурагч түвшин тогтоох шалгалт хийсэн бол, "
                "түүний түвшинг тодорхойлж, түүнд тохирсон дараагийн шатны сургалтын төлөвлөгөө гарга."
            )}
        ]

    # -------------------------
    # 🎯 ТҮВШИН ШАЛГАЛТЫН ГОРИМ
    # -------------------------
    if intent == "placement_test":
        user_stage[chat_id] = {"mode": "placement", "q_index": 0, "answers": []}
        bot.send_message(chat_id, "🎯 Гайхалтай! Түвшинг чинь шалгацгаая.\n5 асуулт асууна. Хариултаа англиар бичээрэй.\n")
        bot.send_message(chat_id, LEVEL_QUESTIONS[0])
        return

    # -------------------------
    # 🧩 Хэрвээ хэрэглэгч түвшин шалгалтандаа хариулж байгаа бол
    # -------------------------
    if chat_id in user_stage and user_stage[chat_id].get("mode") == "placement":
        stage = user_stage[chat_id]
        stage["answers"].append(user_input)
        stage["q_index"] += 1

        if stage["q_index"] < len(LEVEL_QUESTIONS):
            next_q = LEVEL_QUESTIONS[stage["q_index"]]
            bot.send_message(chat_id, next_q)
        else:
            # ✅ 5 асуултын дараа түвшин дүгнэх
            try:
                summary_prompt = (
                    "Сурагчийн түвшин шалгалтын хариултуудыг дүгнэ. "
                    "Доорх хариултуудыг үндэслээд A1–C1 түвшинг тогтоон тайлбар өг. "
                    "Түвшин тогтоосны дараа дараагийн шатны сургалтын төлөвлөгөөг гарга: "
                    "өөрөөр хэлбэл, түвшинд нь тохирсон үгс, ярианы дасгал, богино зорилго санал болго. "
                    f"Хариултууд: {stage['answers']}"
                )

                user_context[chat_id].append({"role": "user", "content": summary_prompt})
                completion = openai.ChatCompletion.create(
                    model="gpt-4-turbo",  # GPT-4 илүү нарийвчлалтай
                    messages=user_context[chat_id],
                    temperature=0.7
                )
                result = completion.choices[0].message["content"]

                bot.send_message(chat_id, "✅ Шалгалт дууслаа!\n\n🎓 Түвшин ба төлөвлөгөө:\n\n" + result)

            except Exception:
                bot.send_message(chat_id, "⚠️ AI сервертэй холбогдоход алдаа гарлаа. Түр хүлээгээд дахин оролдоорой.")

            # state reset
            user_stage.pop(chat_id)
        return

    # -------------------------
    # 💬 AI БАГШИЙН ХАРИУЛТ (Speaking / Vocab / Learning)
    # -------------------------
    if intent in ["speaking", "learn_english", "vocab"]:
        try:
            user_context[chat_id].append({"role": "user", "content": user_input})
            completion = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=user_context[chat_id],
                temperature=0.8
            )
            reply = completion.choices[0].message["content"]
            user_context[chat_id].append({"role": "assistant", "content": reply})
        except Exception:
            reply = "⚠️ AI сервертэй холбогдоход алдаа гарлаа."
    elif intent == "greeting":
        reply = RESPONSE_GREETING
    else:
        reply = RESPONSE_FALLBACK

    bot.send_message(chat_id, reply)

# -------------------------
# BOT START
# -------------------------
if __name__ == "__main__":
    print("🤖 Eduhub AI Teacher is running...")
    bot.infinity_polling()
