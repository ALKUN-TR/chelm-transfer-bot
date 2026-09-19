import os
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# --- FLASK WEB SERVER FOR RENDER HEALTH CHECKS ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- BOT CONFIGURATION & LOGIC ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

(
    LANGUAGE,
    ROUTE,
    ADDRESS,
    DATE,
    TIME,
    PASSENGERS,
    LUGGAGE,
    TRANSFER_TYPE,
    PHONE,
) = range(9)

LANG_TEXTS = {
    'UA': {
        'welcome': "Вітаємо! Оберіть мову обслуговування:",
        'choose_route': "Оберіть маршрут трансферу:",
        'btn_custom_route': "Інший маршрут ✍️",
        'custom_route_prompt': "Введіть свій маршрут (наприклад: Хелм - Варшава):",
        'enter_address': "Укажіть точну адресу відправлення та прибуття:",
        'enter_date': "Укажіть дату поїздки (наприклад: 25.10.2026):",
        'enter_time': "Укажіть бажаний час виїзду (наприклад: 14:30):",
        'choose_passengers': "Оберіть кількість пасажирів:",
        'btn_custom_passengers': "Своя кількість ✏️",
        'custom_passengers_prompt': "Введіть кількість пасажирів числом:",
        'choose_luggage': "Оберіть кількість багажу:",
        'btn_custom_luggage': "Свій варіант ✏️",
        'custom_luggage_prompt': "Опишіть ваш багаж (кількість валіз/сумки):",
        'choose_transfer_type': "Оберіть тип трансферу:",
        'transfer_types': [['Стандарт', 'VIP / Індивідуальний'], ['Груповий / Автобус']],
        'enter_phone': "Будь ласка, поділіться номером телефону для зв'язку:",
        'btn_phone': "Надіслати номер телефону 📱",
        'success': "Дякуємо! Вашу заявку прийнято. Менеджер зв'яжеться з вами найближчим часом.\n\nДля термінових питань: @ALKUNTR",
    },
    'PL': {
        'welcome': "Witamy! Wybierz język obsługi:",
        'choose_route': "Wybierz trasę transferu:",
        'btn_custom_route': "Inna trasa ✍️",
        'custom_route_prompt': "Wpisz swoją trasę (np. Chełm - Warszawa):",
        'enter_address': "Podaj dokładny adres odbioru i docelowy:",
        'enter_date': "Podaj datę podróży (np. 25.10.2026):",
        'enter_time': "Podaj preferowaną godzinę wyjazdu (np. 14:30):",
        'choose_passengers': "Wybierz liczbę pasażerów:",
        'btn_custom_passengers': "Inna liczba ✏️",
        'custom_passengers_prompt': "Wpisz liczbę pasażerów cyfrą:",
        'choose_luggage': "Wybierz ilość bagażu:",
        'btn_custom_luggage': "Inny wariant ✏️",
        'custom_luggage_prompt': "Opisz swój bagaż (liczba walizek/torby):",
        'choose_transfer_type': "Wybierz typ transferu:",
        'transfer_types': [['Standardowy', 'VIP / Indywidualny'], ['Grupowy / Autobus']],
        'enter_phone': "Proszę podać numer telefonu do kontaktu:",
        'btn_phone': "Udostępnij numer telefonu 📱",
        'success': "Dziękujemy! Twoje zgłoszenie zostało przyjęte. Menedżer skontaktuje się z Tobą wkrótce.\n\nW pilnych sprawach: @ALKUNTR",
    },
    'EN': {
        'welcome': "Welcome! Select your language:",
        'choose_route': "Select your transfer route:",
        'btn_custom_route': "Other route ✍️",
        'custom_route_prompt': "Enter your route (e.g. Chełm - Warsaw):",
        'enter_address': "Provide pickup and drop-off addresses:",
        'enter_date': "Enter travel date (e.g. 25.10.2026):",
        'enter_time': "Enter preferred departure time (e.g. 14:30):",
        'choose_passengers': "Select number of passengers:",
        'btn_custom_passengers': "Custom number ✏️",
        'custom_passengers_prompt': "Enter number of passengers as a digit:",
        'choose_luggage': "Select luggage amount:",
        'btn_custom_luggage': "Custom amount ✏️",
        'custom_luggage_prompt': "Describe your luggage (number of suitcases/bags):",
        'choose_transfer_type': "Select transfer type:",
        'transfer_types': [['Standard', 'VIP / Individual'], ['Group / Bus']],
        'enter_phone': "Please share your phone number for contact:",
        'btn_phone': "Share Phone Number 📱",
        'success': "Thank you! Your request has been received. A manager will contact you shortly.\n\nFor urgent inquiries: @ALKUNTR",
    },
    'RU': {
        'welcome': "Добро пожаловать! Выберите язык обслуживания:",
        'choose_route': "Выберите маршрут трансфера:",
        'btn_custom_route': "Другой маршрут ✍️",
        'custom_route_prompt': "Введите ваш маршрут (например: Хелм - Варшава):",
        'enter_address': "Укажите точный адрес отправления и прибытия:",
        'enter_date': "Укажите дату поездки (например: 25.10.2026):",
        'enter_time': "Укажите желаемое время выезда (например: 14:30):",
        'choose_passengers': "Выберите количество пассажиров:",
        'btn_custom_passengers': "Свое количество ✏️",
        'custom_passengers_prompt': "Введите количество пассажиров числом:",
        'choose_luggage': "Выберите количество багажа:",
        'btn_custom_luggage': "Свой вариант ✏️",
        'custom_luggage_prompt': "Опишите ваш багаж (количество чемоданов/сумок):",
        'choose_transfer_type': "Выберите тип трансфера:",
        'transfer_types': [['Стандарт', 'VIP / Индивидуальный'], ['Групповой / Автобус']],
        'enter_phone': "Пожалуйста, поделитесь номером телефона для связи:",
        'btn_phone': "Отправить номер телефона 📱",
        'success': "Спасибо! Ваша заявка принята. Менеджер свяжется с вами в ближайшее время.\n\nДля срочных вопросов: @ALKUNTR",
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['🇺🇦 Українська', '🇵🇱 Polski'], ['🇬🇧 English', '🇷🇺 Русский']]
    await update.message.reply_text(
        "Вітаємо / Witamy / Welcome / Добро пожаловать!\nОберіть мову / Wybierz język / Select language / Выберите язык:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if 'Українська' in text:
        lang = 'UA'
    elif 'Polski' in text:
        lang = 'PL'
    elif 'English' in text:
        lang = 'EN'
    else:
        lang = 'RU'
    
    context.user_data['lang'] = lang
    texts = LANG_TEXTS[lang]

    routes = [
        ['Chełm - Lublin', 'Chełm - Warszawa'],
        ['Chełm - Kraków', texts['btn_custom_route']]
    ]
    await update.message.reply_text(
        texts['choose_route'],
        reply_markup=ReplyKeyboardMarkup(routes, one_time_keyboard=True, resize_keyboard=True)
    )
    return ROUTE

async def set_route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    route = update.message.text
    lang = context.user_data.get('lang', 'UA')
    texts = LANG_TEXTS[lang]

    if route == texts['btn_custom_route']:
        await update.message.reply_text(texts['custom_route_prompt'], reply_markup=ReplyKeyboardRemove())
        return ROUTE

    context.user_data['route'] = route
    await update.message.reply_text(texts['enter_address'], reply_markup=ReplyKeyboardRemove())
    return ADDRESS

async def set_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    lang = context.user_data.get('lang', 'UA')
    texts = LANG_TEXTS[lang]
    await update.message.reply_text(texts['enter_date'])
    return DATE

async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    lang = context.user_data.get('lang', 'UA')
    texts = LANG_TEXTS[lang]
    await update.message.reply_text(texts['enter_time'])
    return TIME

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    lang = context.user_data.get('lang', 'UA')
    texts = LANG_TEXTS[lang]

    passengers = [['1', '2', '3', '4'], ['5+', texts['btn_custom_passengers']]]
    await update.message.reply_text(
        texts['choose_passengers'],
        reply_markup=ReplyKeyboardMarkup(passengers, one_time_keyboard=True, resize_keyboard=True)
    )
    return PASSENGERS

async def set_passengers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass_num = update.message.text
    lang = context.user_data.get('lang', 'UA')
    texts = LANG_TEXTS[lang]

    if pass_num == texts['btn_custom_passengers']:
        await update.message.reply_text(texts['custom_passengers_prompt'], reply_markup=ReplyKeyboardRemove())
        return PASSENGERS

    context.user_data['passengers'] = pass_num
    luggage_opts = [['1-2', '3-4'], ['5+', texts['btn_custom_luggage']]]
    await update.message.reply_text(
        texts['choose_luggage'],
        reply_markup=ReplyKeyboardMarkup(luggage_opts, one_time_keyboard=True, resize_keyboard=True)
    )
    return LUGGAGE

async def set_luggage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lugg = update.message.text
    lang = context.user_data.get('lang', 'UA')
    texts = LANG_TEXTS[lang]

    if lugg == texts['btn_custom_luggage']:
        await update.message.reply_text(texts['custom_luggage_prompt'], reply_markup=ReplyKeyboardRemove())
        return LUGGAGE

    context.user_data['luggage'] = lugg
    await update.message.reply_text(
        texts['choose_transfer_type'],
        reply_markup=ReplyKeyboardMarkup(texts['transfer_types'], one_time_keyboard=True, resize_keyboard=True)
    )
    return TRANSFER_TYPE

async def set_transfer_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['transfer_type'] = update.message.text
    lang = context.user_data.get('lang', 'UA')
    texts = LANG_TEXTS[lang]

    phone_btn = ReplyKeyboardMarkup(
        [[KeyboardButton(texts['btn_phone'], request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text(texts['enter_phone'], reply_markup=phone_btn)
    return PHONE

async def set_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text
    context.user_data['phone'] = phone

    lang = context.user_data.get('lang', 'UA')
    texts = LANG_TEXTS[lang]

    user = update.effective_user
    username = f"@{user.username}" if user.username else "No username"

    admin_msg = (
        f"🚨 **НОВА ЗАЯВКА НА ТРАНСФЕР** 🚨\n\n"
        f"👤 **Клієнт:** {user.full_name} ({username})\n"
        f"📞 **Телефон:** {phone}\n"
        f"🌐 **Мова:** {lang}\n"
        f"🗺 **Маршрут:** {context.user_data.get('route')}\n"
        f"📍 **Адреса:** {context.user_data.get('address')}\n"
        f"📅 **Дата:** {context.user_data.get('date')}\n"
        f"⏰ **Час:** {context.user_data.get('time')}\n"
        f"👥 **Пасажири:** {context.user_data.get('passengers')}\n"
        f"🧳 **Багаж:** {context.user_data.get('luggage')}\n"
        f"🚘 **Тип:** {context.user_data.get('transfer_type')}"
    )

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode='Markdown')
        except Exception as e:
            print(f"Error sending to admin: {e}")

    await update.message.reply_text(texts['success'], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Дію скасовано / Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            ROUTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_route)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_address)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time)],
            PASSENGERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_passengers)],
            LUGGAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_luggage)],
            TRANSFER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_transfer_type)],
            PHONE: [
                MessageHandler(filters.CONTACT, set_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_phone)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app_bot.add_handler(conv_handler)
    app_bot.run_polling()

if __name__ == '__main__':
    main()
