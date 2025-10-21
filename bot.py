import telebot
from telebot import types
import requests
from datetime import datetime
from database import create_tables, add_or_update_user, get_user, set_subscription, save_user_message, all_users
from config import BOT_TOKEN, WEATHER_API_KEY, CHANNEL_ID, ADMIN_CHAT_ID

bot = telebot.TeleBot(BOT_TOKEN)
create_tables()

YOUR_CHANNEL_USERNAME = CHANNEL_ID.replace("@", "")

# ====================== LANGUAGES ======================
LANGUAGES = {
    "uz": "🇺🇿 O‘zbek",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский"
}

# ====================== TRANSLATIONS ======================
TRANSLATIONS = {
    "uz": {
        "select_language": "Tilni tanlang:",
        "language_selected": "Siz {lang} tilini tanladingiz ✅",
        "subscribe_message": "Ob-havoni ko‘rish uchun kanalga obuna bo‘ling!",
        "select_option": "Tanlang:",
        "city_not_found": "Shahar topilmadi ❌",
        "write_message": "Xabaringizni yozing:",
        "message_sent": "Xabaringiz adminga yuborildi ✅",
        "welcome_admin": "Admin panelga xush kelibsiz 👑",
        "send_news": "Foydalanuvchilarga yuboradigan xabaringizni yuboring:",
        "enter_city": "Shahar nomini yozing (masalan: Tashkent):",
        "back": "Orqaga",
        "menu_weather": "Ob-havo 🌤",
        "menu_admin": "Adminga habar yuborish ✉️",
        "menu_week": "1 haftalik ob-havo 🌦",
        "menu_today": "Bugungi ob-havo ☀️"
    },
    "en": {
        "select_language": "Select language:",
        "language_selected": "You selected {lang} ✅",
        "subscribe_message": "Subscribe to the channel to see weather info!",
        "select_option": "Choose:",
        "city_not_found": "City not found ❌",
        "write_message": "Write your message:",
        "message_sent": "Your message has been sent to admin ✅",
        "welcome_admin": "Welcome to admin panel 👑",
        "send_news": "Send message to all users:",
        "enter_city": "Enter city name (e.g., London):",
        "back": "Back",
        "menu_weather": "Weather 🌤",
        "menu_admin": "Message admin ✉️",
        "menu_week": "Weekly forecast 🌦",
        "menu_today": "Today's weather ☀️"
    },
    "ru": {
        "select_language": "Выберите язык:",
        "language_selected": "Вы выбрали {lang} ✅",
        "subscribe_message": "Подпишитесь на канал, чтобы увидеть погоду!",
        "select_option": "Выберите:",
        "city_not_found": "Город не найден ❌",
        "write_message": "Напишите сообщение:",
        "message_sent": "Ваше сообщение отправлено админу ✅",
        "welcome_admin": "Добро пожаловать в админ-панель 👑",
        "send_news": "Отправьте сообщение всем пользователям:",
        "enter_city": "Введите название города (например: Москва):",
        "back": "Назад",
        "menu_weather": "Погода 🌤",
        "menu_admin": "Сообщение админу ✉️",
        "menu_week": "Погода на неделю 🌦",
        "menu_today": "Погода на сегодня ☀️"
    }
}

# ====================== START ======================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for code, name in LANGUAGES.items():
        markup.add(types.KeyboardButton(name))
    bot.send_message(chat_id, "Tilni tanlang:", reply_markup=markup)
    add_or_update_user(chat_id, message.from_user.username, message.from_user.first_name)

# ====================== LANGUAGE ======================
@bot.message_handler(func=lambda m: m.text in LANGUAGES.values())
def set_language(message):
    chat_id = message.chat.id
    lang_code = [k for k, v in LANGUAGES.items() if v == message.text][0]
    add_or_update_user(chat_id, message.from_user.username, message.from_user.first_name, language=lang_code)
    bot.send_message(chat_id, TRANSLATIONS[lang_code]["language_selected"].format(lang=message.text), reply_markup=types.ReplyKeyboardRemove())
    ask_subscription(chat_id)

# ====================== SUBSCRIPTION ======================
def ask_subscription(chat_id):
    if chat_id == ADMIN_CHAT_ID:
        set_subscription(chat_id, True)
        show_main_buttons(chat_id)
        return

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={chat_id}"
        r = requests.get(url).json()
        status = r.get("result", {}).get("status", "")
        if status in ["left", "kicked", ""]:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔗 Kanalga obuna bo‘lish", url=f"https://t.me/{YOUR_CHANNEL_USERNAME}"))
            bot.send_message(chat_id, "❗ Ob-havoni ko‘rish uchun kanalga obuna bo‘ling!", reply_markup=markup)
            return
        set_subscription(chat_id, True)
        show_main_buttons(chat_id)
    except Exception as e:
        print("Subscription error:", e)

# ====================== MAIN MENU ======================
def show_main_buttons(chat_id):
    user = get_user(chat_id)
    lang = user.get("language", "uz")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(TRANSLATIONS[lang]["menu_today"], TRANSLATIONS[lang]["menu_week"])
    markup.add(TRANSLATIONS[lang]["menu_admin"])
    bot.send_message(chat_id, TRANSLATIONS[lang]["select_option"], reply_markup=markup)

# ====================== WEATHER ======================
@bot.message_handler(func=lambda m: "ob-havo" in m.text.lower() or "weather" in m.text.lower())
def ask_city(message):
    user = get_user(message.chat.id)
    lang = user.get("language", "uz")
    bot.send_message(message.chat.id, TRANSLATIONS[lang]["enter_city"])
    if "haftalik" in message.text.lower() or "week" in message.text.lower():
        bot.register_next_step_handler(message, get_weekly_weather)
    else:
        bot.register_next_step_handler(message, get_today_weather)

def get_today_weather(message):
    chat_id = message.chat.id
    city = message.text
    user = get_user(chat_id)
    lang = user.get("language", "uz")

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang={lang}"
    r = requests.get(url).json()

    if r.get("cod") != 200:
        bot.send_message(chat_id, TRANSLATIONS[lang]["city_not_found"])
        return

    desc = r['weather'][0]['description'].capitalize()
    temp = r['main']['temp']
    humidity = r['main']['humidity']
    wind = r['wind']['speed']
    feels = r['main']['feels_like']

    text = (
        f"📍 {r['name']}\n"
        f"🌡 {temp}°C (Seziladi: {feels}°C)\n"
        f"💧 Namlik: {humidity}%\n"
        f"💨 Shamol: {wind} m/s\n"
        f"☁️ Holat: {desc}"
    )
    bot.send_message(chat_id, text)

def get_weekly_weather(message):
    chat_id = message.chat.id
    city = message.text
    user = get_user(chat_id)
    lang = user.get("language", "uz")

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang={lang}"
    r = requests.get(url).json()

    if r.get("cod") != "200":
        bot.send_message(chat_id, TRANSLATIONS[lang]["city_not_found"])
        return

    text = f"📅 1 haftalik ob-havo — {r['city']['name']}:\n\n"
    last_date = ""
    for i in range(0, len(r["list"]), 8):
        d = r["list"][i]
        date = datetime.fromtimestamp(d["dt"]).strftime("%d-%m (%A)")
        temp = d["main"]["temp"]
        desc = d["weather"][0]["description"]
        text += f"📆 {date}\n🌡 {temp}°C — {desc}\n\n"

    bot.send_message(chat_id, text)

# ====================== USER → ADMIN ======================
@bot.message_handler(func=lambda m: "adminga" in m.text.lower() or "admin" in m.text.lower())
def send_message_to_admin(message):
    user = get_user(message.chat.id)
    lang = user.get("language", "uz")
    msg = bot.send_message(message.chat.id, TRANSLATIONS[lang]["write_message"])
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(message):
    chat_id = message.chat.id
    save_user_message(chat_id, message.text)
    bot.send_message(ADMIN_CHAT_ID, f"📩 @{message.from_user.username} dan xabar:\n{message.text}")
    user = get_user(chat_id)
    lang = user.get("language", "uz")
    bot.send_message(chat_id, TRANSLATIONS[lang]["message_sent"])
    show_main_buttons(chat_id)

# ====================== ADMIN PANEL ======================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    chat_id = message.chat.id
    if chat_id != ADMIN_CHAT_ID:
        bot.send_message(chat_id, "⛔ Sizda ruxsat yo‘q!")
        return

    bot.send_message(chat_id, "👑 Admin panelga xush kelibsiz!", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, handle_admin_panel)

def handle_admin_panel(message):
    msg = bot.send_message(message.chat.id, "Xabar matnini yuboring:")
    bot.register_next_step_handler(msg, broadcast_to_users)

def broadcast_to_users(message):
    users = all_users()
    count = 0
    for u in users:
        try:
            if u['chat_id'] != ADMIN_CHAT_ID:
                bot.send_message(u['chat_id'], message.text)
                count += 1
        except:
            continue
    bot.send_message(ADMIN_CHAT_ID, f"✅ {count} ta foydalanuvchiga yuborildi!")

# ====================== RUN ======================
bot.infinity_polling()
