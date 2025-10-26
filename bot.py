import os
import openai
import telebot
from dotenv import load_dotenv
from datetime import datetime
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
# GLOBAL STATES
# -------------------------
user_context = {}
user_stage = {}
user_profile = {}
last_message_sent = {}

# -------------------------
# MESSAGE DUPLICATE PROTECTOR
# -------------------------
def safe_send(chat_id, text):
    """Prevent sending duplicate messages"""
    if last_message_sent.get(chat_id) != text:
        bot.send_message(chat_id, text)
        last_message_sent[chat_id] = text

# -------------------------
# INITIALIZER
# -------------------------
def ensure_user(chat_id):
    if chat_id not in user_context:
        user_context[chat_id] = [
            {"role": "system", "content": (
                "You are an encouraging English teacher for Mongolian learners. "
                "Respond clearly, kindly, and in mixed Mongolian + English. "
                "Always motivate the learner to study every day a little bit."
            )}
        ]
    if chat_id not in user_profile:
        user_profile[chat_id] = {
            "goal": None,
            "level": None,
            "last_topic": None,
            "last_updated": None
        }

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
# INTENT DETECTION
# -------------------------
def detect_intent(txt):
    t = txt.lower()
    if any(x in t for x in ["сайн уу", "hi", "hello", "hey"]):
        return "greeting"
    if any(x in t for x in ["3", "түвшин", "placement", "exam", "test"]):
        return "placement_test"
    if "сурмаар" in t or "i want" in t or "хүсэж байна" in t:
        return "goal_response"
    if any(x in t for x in ["үг", "vocab", "vocabulary"]):
        return "vocab"
    if any(x in t for x in ["ярих", "speaking"]):
        return "speaking"
    return "fallback"

# -------------------------
# MAIN HANDLER
# -------------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.is_bot:
        return

    chat_id = message.chat.id
    text = message.text.strip()
    intent = detect_intent(text)
    ensure_user(chat_id)

    # -------------------------
    # GREETING
    # -------------------------
    if intent == "greeting":
        safe_send(chat_id,
            "Сайн уу! 👋 Би чиний AI англи хэлний багш байна.\n\n"
            "Юу хийх вэ?\n"
            "1️⃣ Үг цээжлэх\n"
            "2️⃣ Ярианы дадлага\n"
            "3️⃣ Түвшин тогтоох шалгалт (3 гэж бичээрэй)\n\n"
            "Бэлтгэлтэй байна уу? 😎"
        )
        return

    # -------------------------
    # LEVEL TEST START
    # -------------------------
    if intent == "placement_test":
        user_stage[chat_id] = {"mode": "placement", "q_index": 0, "answers": []}
        safe_send(chat_id, "🎯 Түвшинг чинь шалгая! 5 асуултад англиар хариулаарай 👇")
        safe_send(chat_id, LEVEL_QUESTIONS[0])
        return

    # -------------------------
    # LEVEL TEST PROGRESS
    # -------------------------
    if chat_id in user_stage and user_stage[chat_id].get("mode") == "placement":
        stage = user_stage[chat_id]
        stage["answers"].append(text)
        stage["q_index"] += 1

        # дараагийн асуулт байгаа бол
        if stage["q_index"] < len(LEVEL_QUESTIONS):
            safe_send(chat_id, LEVEL_QUESTIONS[stage["q_index"]])
        else:
            safe_send(chat_id, "🕓 Түвшинг боловсруулж байна... түр хүлээнэ үү.")

            # AI дүгнэлт
            try:
                prompt = (
                    "You are an English teacher for a Mongolian student.\n"
                    "Evaluate the answers below to determine their CEFR level (A1–C1). "
                    "Then explain the result in Mongolian clearly, with encouragement. "
                    "After giving the result, ask them what they want to focus on next (grammar, speaking, vocabulary, writing, etc.).\n"
                    f"Answers: {stage['answers']}"
                )

                completion = openai.ChatCompletion.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "system", "content": prompt}],
                    temperature=0.7
                )
                result = completion.choices[0].message["content"]

                safe_send(chat_id, "✅ Шалгалт дууслаа!\n\n" + result)

                user_profile[chat_id]["level"] = result.split()[0]
                user_profile[chat_id]["last_topic"] = "placement_result"
                user_profile[chat_id]["last_updated"] = datetime.now().isoformat()

                safe_send(chat_id, "🧠 Одоо чи юу сурмаар байна? (жишээ нь: 'ярианы чадвараа сайжруулах', 'үг цээжлэх', 'IELTS бэлдэх')")
            except Exception:
                safe_send(chat_id, "⚠️ AI-д холбогдоход алдаа гарлаа. Түр хүлээгээд дахин оролдоорой.")
            user_stage.pop(chat_id)
        return

    # -------------------------
    # GOAL RESPONSE → Personalized Lesson
    # -------------------------
    if intent == "goal_response":
        safe_send(chat_id, "🕓 Хичээл боловсруулж байна... түр хүлээнэ үү.")
        try:
            goal = text
            user_profile[chat_id]["goal"] = goal
            level = user_profile[chat_id].get("level", "A2")

            prompt = (
                f"The student is level {level}. They said their goal: {goal}. "
                "Create a personalized short lesson with:\n"
                "- A warm greeting in Mongolian\n"
                "- 3 key vocabulary words with English + Mongolian meaning + example sentence\n"
                "- 1 grammar point (simple but clear)\n"
                "- 1 short speaking task\n"
                "Always end by saying:\n"
                "'Одоо байгаа түвшнээсээ илүү сайжрахын тулд өдөр бүр бага багаар давтвал илүү үр дүнтэй шүү 💪'"
            )

            completion = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.8
            )

            lesson = completion.choices[0].message["content"]
            safe_send(chat_id, "📘 Таний хувийн хичээл бэлэн боллоо:\n\n" + lesson)

            user_profile[chat_id]["last_topic"] = "custom_lesson"
            user_profile[chat_id]["last_updated"] = datetime.now().isoformat()
        except Exception:
            safe_send(chat_id, "⚠️ Хичээл боловсруулахад алдаа гарлаа. Дахин оролдоно уу.")
        return

    # -------------------------
    # VOCAB / SPEAKING REQUESTS
    # -------------------------
    if intent in ["vocab", "speaking"]:
        topic = "Speaking" if intent == "speaking" else "Vocabulary"
        safe_send(chat_id, f"🕓 {topic} хичээл боловсруулж байна...")
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[{"role": "system", "content": f"Create a short {topic} practice lesson for Mongolian learners."}],
                temperature=0.8
            )
            reply = completion.choices[0].message["content"]
            safe_send(chat_id, f"🎯 {topic} хичээл:\n\n" + reply)
            safe_send(chat_id, "💡 Сануулга: өдөр бүр бага багаар давтвал илүү үр дүнтэй шүү 💪")
        except Exception:
            safe_send(chat_id, "⚠️ Хичээл боловсруулахад алдаа гарлаа.")
        return

    # -------------------------
    # FALLBACK
    # -------------------------
    safe_send(chat_id,
        "Би туслахад бэлэн байна 😊\n"
        "Та юу хүсэж байна вэ?\n"
        "1️⃣ Үг цээжлэх\n"
        "2️⃣ Ярианы дадлага\n"
        "3️⃣ Түвшин тогтоох шалгалт"
    )

# -------------------------
# START BOT
# -------------------------
if __name__ == "__main__":
    print("🤖 Eduhub AI Teacher v5.0 running...")
    bot.infinity_polling()
