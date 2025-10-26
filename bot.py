import os
import openai
import telebot
from dotenv import load_dotenv
from datetime import datetime, timedelta
import threading
import time

# -------------------------
# ТОХИРГОО
# -------------------------
load_dotenv("bot.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

# -------------------------
# CONTEXT, STATE
# -------------------------
user_context = {}  # хэрэглэгчийн чат түүх
user_stage = {}    # хэрэглэгчийн шат
subscribed_users = set()  # өдөр бүрийн хичээл авах хэрэглэгчид

# -------------------------
# INTENT DETECTION
# -------------------------
def detect_intent(txt):
    t = txt.lower()

    if any(x in t for x in ["сайн уу", "sain uu", "hi", "hello"]):
        return "greeting"
    if any(x in t for x in ["3", "түвшин", "placement", "exam", "test"]):
        return "placement_test"
    if "translate" in t or "орчуул" in t:
        return "translate"
    if "жишээ" in t or "example" in t:
        return "example_request"
    if any(x in t for x in ["алдаа", "зас", "grammar", "correct", "fix"]):
        return "correction"
    if any(x in t for x in ["тест", "шалгалт", "quiz"]):
        return "quiz"
    if any(x in t for x in ["subscribe", "өдөр бүр", "day lesson"]):
        return "subscribe"
    if "unsubscribe" in t:
        return "unsubscribe"
    if any(x in t for x in ["speaking", "ярих", "ярьж", "говорить"]):
        return "speaking"
    if any(x in t for x in ["үг", "vocab", "vocabulary", "үг цээж"]):
        return "vocab"
    return "fallback"

# -------------------------
# READY TEXTS
# -------------------------
RESPONSE_GREETING = (
    "Сайн уу! 👋 Би AI англи хэлний багш байна.\n\n"
    "Юу хийх вэ? 👇\n"
    "1️⃣ Үг цээжлэх\n"
    "2️⃣ Ярианы дадлага\n"
    "3️⃣ Түвшин тогтоох шалгалт\n"
    "4️⃣ Монгол ↔ Англи орчуулга\n"
    "5️⃣ Өдөр бүрийн AI хичээл (subscribe)\n"
    "Сонголтоо бичээрэй (жишээ: 3)"
)

RESPONSE_FALLBACK = (
    "Би туслахад бэлэн байна 😊\n"
    "Та юу хийхийг хүсэж байна вэ?\n"
    "1️⃣ Үг цээжлэх\n"
    "2️⃣ Ярианы дадлага\n"
    "3️⃣ Түвшин тогтоох шалгалт\n"
    "4️⃣ Монгол ↔ Англи орчуулга"
)

# -------------------------
# DAILY LESSON THREAD
# -------------------------
def send_daily_lessons():
    while True:
        now = datetime.now()
        if now.hour == 8 and now.minute == 0:  # өглөө 08:00 бүрт илгээнэ
            for chat_id in subscribed_users:
                try:
                    prompt = "Create a short English lesson (vocabulary + sentence + exercise) for a Mongolian learner."
                    completion = openai.ChatCompletion.create(
                        model="gpt-4-turbo",
                        messages=[{"role": "system", "content": prompt}],
                        temperature=0.8
                    )
                    lesson = completion.choices[0].message["content"]
                    bot.send_message(chat_id, "🌅 Өглөөний AI хичээл:\n\n" + lesson)
                except Exception:
                    pass
        time.sleep(60)

threading.Thread(target=send_daily_lessons, daemon=True).start()

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
                "Та англи хэл сурагчдад тусалдаг AI багш. "
                "Хариулт чинь ойлгомжтой, найрсаг, товч, зааварлаг байх ёстой. "
                "Монгол хэлээр тайлбар хийж, англи жишээ өгүүлбэр оруул."
            )}
        ]

    # -------- 1. DAILY LESSON SUBSCRIPTION --------
    if intent == "subscribe":
        subscribed_users.add(chat_id)
        bot.send_message(chat_id, "🎯 Та өдөр бүрийн AI хичээл хүлээн авахад бүртгэгдлээ!")
        return
    if intent == "unsubscribe":
        subscribed_users.discard(chat_id)
        bot.send_message(chat_id, "❌ Та өдөр бүрийн хичээлээс хасагдлаа.")
        return

    # -------- 2. TRANSLATION --------
    if intent == "translate":
        try:
            direction = "Mongolian to English" if any(" " in user_input and all('\u0400' <= c <= '\u04FF' or c == ' ' for c in user_input)) else "English to Mongolian"
            completion = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": f"Translate between {direction}. Keep meaning accurate and natural."},
                    {"role": "user", "content": user_input}
                ]
            )
            reply = completion.choices[0].message["content"]
        except Exception:
            reply = "⚠️ Орчуулга хийхэд алдаа гарлаа."
        bot.send_message(chat_id, reply)
        return

    # -------- 3. PLACEMENT TEST --------
    if intent == "placement_test":
        user_stage[chat_id] = {"mode": "placement", "q_index": 0, "answers": []}
        bot.send_message(chat_id, "🎯 Түвшинг чинь шалгая.\n5 асуултад англиар хариулаарай!\n")
        bot.send_message(chat_id, LEVEL_QUESTIONS[0])
        return

    # -------- 4. PLACEMENT TEST ANSWERS --------
    if chat_id in user_stage and user_stage[chat_id].get("mode") == "placement":
        stage = user_stage[chat_id]
        stage["answers"].append(user_input)
        stage["q_index"] += 1

        if stage["q_index"] < len(LEVEL_QUESTIONS):
            bot.send_message(chat_id, LEVEL_QUESTIONS[stage["q_index"]])
        else:
            try:
                summary_prompt = (
                    "Analyze student's English level (A1–C1) and create a custom 7-day learning plan "
                    "with vocabulary, grammar focus, and practice ideas. "
                    f"Answers: {stage['answers']}"
                )
                completion = openai.ChatCompletion.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "system", "content": summary_prompt}],
                    temperature=0.7
                )
                result = completion.choices[0].message["content"]
                bot.send_message(chat_id, "✅ Шалгалт дууслаа!\n\n" + result)
            except Exception:
                bot.send_message(chat_id, "⚠️ AI дүгнэлт хийхэд алдаа гарлаа.")
            user_stage.pop(chat_id)
        return

    # -------- 5. EXAMPLE REQUEST / GRAMMAR CORRECTION / QUIZ --------
    if intent in ["example_request", "correction", "quiz", "speaking", "vocab", "learn_english"]:
        try:
            context_prompt = {
                "example_request": "Generate clear example sentences on this topic with Mongolian translations.",
                "correction": "Correct grammar errors and explain in Mongolian.",
                "quiz": "Create a short 3-question quiz from the latest vocabulary or grammar concept. Provide correct answers with explanations.",
                "speaking": "Give a speaking exercise and follow-up question for practice.",
                "vocab": "Teach 5 useful words with meaning, part of speech, and example sentences.",
                "learn_english": "Give short lesson with vocabulary, grammar point, and practice question."
            }
            prompt = context_prompt[intent]
            completion = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.8
            )
            reply = completion.choices[0].message["content"]
        except Exception:
            reply = "⚠️ AI боловсруулалт амжилтгүй боллоо."
        bot.send_message(chat_id, reply)
        return

    # -------- 6. DEFAULT / GREETING --------
    if intent == "greeting":
        reply = RESPONSE_GREETING
    else:
        reply = RESPONSE_FALLBACK
    bot.send_message(chat_id, reply)

# -------------------------
# BOT START
# -------------------------
if __name__ == "__main__":
    print("🤖 Eduhub AI Teacher v2.0 is running...")
    bot.infinity_polling()
