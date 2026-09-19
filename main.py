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

# --- BOT CONFIGURATION & STATES ---
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
    'RU': {
        'welcome': "Приветствуем! 🚖 Сервис трансфера Хелм ↔️ Польша.\nВыберите направление:",
        'routes': [['🚆 Из Хелма', '🚉 В Хелм'], ['🚘 Другой маршрут']],
        'address_prompt_standard': "📍 Укажите точный адрес, вокзал или аэропорт назначения/отправления:\n(Например: Аэропорт Шопена, вокзал Западный в Варшаве или ул. Маршалковская 10)",
        'address_prompt_custom': "📍 Укажите, откуда и куда вам нужно доехать (пункт А и пункт Б):\n(Например: Люблин ↔ Аэропорт Модлин)",
        'date_prompt': "Выберите дату поездки:",
        'dates': [['📅 Сегодня', '📅 Завтра'], ['🗓 Другая дата']],
        'time_prompt': "⏰ Укажите точное время отправления или номер поезда/рейса:\n(Например: 14:30 или поезд №119, прибытие в 16:45)",
        'passengers_prompt': "Укажите количество пассажиров:",
        'passengers': [['👤 1 пассажир', '👥 2 пассажира'], ['👥 3 пассажира', '👨‍👩‍👧‍👦 4 пассажира'], ['✏️ Свой вариант']],
        'passengers_custom_prompt': "Введите количество пассажиров вручную (например: 5 взрослых и ребенок):",
        'luggage_prompt': "Укажите количество багажа:",
        'luggage': [['🧳 1 чемодан', '🧳 2 чемодана'], ['🧳 3 чемодана', '🧳 4 чемодана'], ['✏️ Свой вариант']],
        'luggage_custom_prompt': "Введите описание багажа вручную (например: 2 большие сумки + детская коляска):",
        'transfer_prompt': "Выберите предпочтительный тип трансфера:",
        'transfer_types': [['🚘 Индивидуальный (отдельное авто)'], ['👥 Совместная поездка (с попутчиками)'], ['🤷‍♂️ Любой вариант']],
        'phone_prompt': "📱 Нажмите кнопку ниже, чтобы поделиться номером телефона для связи:",
        'phone_btn': "📱 Поделиться номером телефона",
        'success': "Спасибо за заказ! Менеджер свяжется с Вами в максимально короткое время.\n💡 Если у Вас срочный вопрос, Вы можете написать диспетчеру напрямую: @ALKUNTR",
    },
    'UA': {
        'welcome': "Вітаємо! 🚖 Сервіс трансферу Хелм ↔️ Польща.\nОберіть напрямок:",
        'routes': [['🚆 З Хелма', '🚉 До Хелма'], ['🚘 Інший маршрут']],
        'address_prompt_standard': "📍 Вкажіть точну адресу, вокзал або аеропорт призначення/відправлення:\n(Наприклад: Аеропорт Шопена, вокзал Західний у Варшаві або вул. Маршалковська 10)",
        'address_prompt_custom': "📍 Вкажіть, звідки і куди вам нужно доїхати (пункт А та пункт Б):\n(Наприклад: Люблін ↔ Аеропорт Модлін)",
        'date_prompt': "Оберіть дату поїздки:",
        'dates': [['📅 Сьогодні', '📅 Завтра'], ['🗓 Інша дата']],
        'time_prompt': "⏰ Вкажіть точний час відправлення або номер поїзда/рейсу:\n(Наприклад: 14:30 або поїзд №119, прибуття о 16:45)",
        'passengers_prompt': "Вкажіть кількість пасажирів:",
        'passengers': [['👤 1 пасажир', '👥 2 пасажири'], ['👥 3 пасажири', '👨‍👩‍👧‍👦 4 пасажири'], ['✏️ Свій варіант']],
        'passengers_custom_prompt': "Введіть кількість пасажирів вручну (наприклад: 5 дорослих і дитина):",
        'luggage_prompt': "Вкажіть кількість багажу:",
        'luggage': [['🧳 1 валіза', '🧳 2 валізи'], ['🧳 3 валізи', '🧳 4 валізи'], ['✏️ Свій варіант']],
        'luggage_custom_prompt': "Введіть опис багажу вручну (наприклад: 2 великі сумки + дитячий візок):",
        'transfer_prompt': "Оберіть бажаний тип трансферу:",
        'transfer_types': [['🚘 Індивідуальний (окреме авто)'], ['👥 Спільна поїздка (з попутниками)'], ['🤷‍♂️ Будь-який варіант']],
        'phone_prompt': "📱 Натисніть кнопку нижче, щоб поділитися номером телефону для зв'язку:",
        'phone_btn': "📱 Поділитися номером телефону",
        'success': "Дякуємо за замовлення! Менеджер зв'яжеться з Вами в найкоротший термін.\n💡 Якщо у Вас термінове питання, Ви можете написати диспетчеру напряму: @ALKUNTR",
    },
    'PL': {
        'welcome': "Witamy! 🚖 Usługa transferu Chełm ↔️ Polska.\nWybierz kierunek:",
        'routes': [['🚆 Z Chełma', '🚉 Do Chełma'], ['🚘 Inna trasa']],
        'address_prompt_standard': "📍 Podaj dokładny adres, dworzec lub lotnisko docelowe/odbioru:\n(Np.: Lotnisko Chopina, Dworzec Zachodni w Warszawie lub ul. Marszałkowska 10)",
        'address_prompt_custom': "📍 Podaj, skąd i dokąd chcesz jechać (punkt A i punkt B):\n(Np.: Lublin ↔ Lotnisko Modlin)",
        'date_prompt': "Wybierz datę podróży:",
        'dates': [['📅 Dzisiaj', '📅 Jutro'], ['🗓 Inna data']],
        'time_prompt': "⏰ Podaj dokładną godzinę odjazdu lub numer pociągu/lotu:\n(Np.: 14:30 lub pociąg nr 119, przyjazd o 16:45)",
        'passengers_prompt': "Podaj liczbę pasażerów:",
        'passengers': [['👤 1 pasażer', '👥 2 pasażerów'], ['👥 3 pasażerów', '👨‍👩‍👧‍👦 4 pasażerów'], ['✏️ Inna opcja']],
        'passengers_custom_prompt': "Wpisz liczbę pasażerów ręcznie (np.: 5 dorosłych i dziecko):",
        'luggage_prompt': "Podaj ilość bagażu:",
        'luggage': [['🧳 1 walizka', '🧳 2 walizki'], ['🧳 3 walizki', '🧳 4 walizki'], ['✏️ Inna opcja']],
        'luggage_custom_prompt': "Opisz swój bagaż ręcznie (np.: 2 duże torby + wózek dziecięcy):",
        'transfer_prompt': "Wybierz preferowany typ transferu:",
        'transfer_types': [['🚘 Indywidualny (prywatne auto)'], ['👥 Wspólny przejazd (z współpasażerami)'], ['🤷‍♂️ Dowolna opcja']],
        'phone_prompt': "📱 Kliknij poniższy przycisk, aby udostępnić numer telefonu do kontaktu:",
        'phone_btn': "📱 Udostępnij numer telefonu",
        'success': "Dziękujemy za zamówienie! Menedżer skontaktuje się z Tobą jak najszybciej.\n💡 W pilnych sprawach możesz napisać bezpośrednio do dyspozytora: @ALKUNTR",
    },
    'EN': {
        'welcome': "Welcome! 🚖 Transfer service Chełm ↔️ Poland.\nSelect direction:",
        'routes': [['🚆 From Chełm', '🚉 To Chełm'], ['🚘 Other route']],
        'address_prompt_standard': "📍 Specify exact address, station, or airport of pickup/destination:\n(e.g., Chopin Airport, Warsaw West Station, or Marszałkowska 10)",
        'address_prompt_custom': "📍 Specify where from and where to you need to go (Point A and Point B):\n(e.g., Lublin ↔ Modlin Airport)",
        'date_prompt': "Select travel date:",
        'dates': [['📅 Today', '📅 Tomorrow'], ['🗓 Other date']],
        'time_prompt': "⏰ Specify exact departure time or train/flight number:\n(e.g., 14:30 or Train #119, arrival at 16:45)",
        'passengers_prompt': "Specify number of passengers:",
        'passengers': [['👤 1 passenger', '👥 2 passengers'], ['👥 3 passengers', '👨‍👩‍👧‍👦 4 passengers'], ['✏️ Custom option']],
        'passengers_custom_prompt': "Enter number of passengers manually (e.g., 5 adults and a child):",
        'luggage_prompt': "Specify luggage amount:",
        'luggage': [['🧳 1 suitcase', '🧳 2 suitcases'], ['🧳 3 suitcases', '🧳 4 suitcases'], ['✏️ Custom option']],
        'luggage_custom_prompt': "Describe luggage manually (e.g., 2 large bags + baby stroller):",
        'transfer_prompt': "Select preferred transfer type:",
        'transfer_types': [['🚘 Private (individual car)'], ['👥 Shared ride (with fellow passengers)'], ['🤷‍♂️ Any option']],
        'phone_prompt': "📱 Press the button below to share your contact phone number:",
        'phone_btn': "📱 Share phone number",
        'success': "Thank you for your order! Manager will contact you as soon as possible.\n💡 For urgent inquiries, contact dispatch directly: @ALKUNTR",
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['🇺🇦 Українська', '🇵🇱 Polski'], ['🇬🇧 English', '🇷🇺 Русский']]
    await update.message.reply_text(
        "Оберіть мову / Wybierz język / Choose language / Выберите язык:",
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

    await update.message.reply_text(
        texts['welcome'],
        reply_markup=ReplyKeyboardMarkup(texts['routes'], one_time_keyboard=True, resize_keyboard=True)
    )
    return ROUTE

async def set_route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    route = update.message.text
    lang = context.user_data.get('lang', 'RU')
    texts = LANG_TEXTS[lang]

    context.user_data['route'] = route

    # Проверка на «Другой маршрут» на всех 4 языках
    if any(keyword in route for keyword in ['Інший', 'Inna', 'Other', 'Другой']):
        context.user_data['is_custom_route'] = True
        await update.message.reply_text(texts['address_prompt_custom'], reply_markup=ReplyKeyboardRemove())
    else:
        context.user_data['is_custom_route'] = False
        await update.message.reply_text(texts['address_prompt_standard'], reply_markup=ReplyKeyboardRemove())

    return ADDRESS

async def set_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    lang = context.user_data.get('lang', 'RU')
    texts = LANG_TEXTS[lang]

    await update.message.reply_text(
        texts['date_prompt'],
        reply_markup=ReplyKeyboardMarkup(texts['dates'], one_time_keyboard=True, resize_keyboard=True)
    )
    return DATE

async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_choice = update.message.text
    lang = context.user_data.get('lang', 'RU')
    texts = LANG_TEXTS[lang]

    if any(keyword in date_choice for keyword in ['Інша', 'Inna', 'Other', 'Другая']):
        await update.message.reply_text("Вкажіть дату поїздки (наприклад: 25.10.2026):", reply_markup=ReplyKeyboardRemove())
        return DATE

    context.user_data['date'] = date_choice
    await update.message.reply_text(texts['time_prompt'], reply_markup=ReplyKeyboardRemove())
    return TIME

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    lang = context.user_data.get('lang', 'RU')
    texts = LANG_TEXTS[lang]

    await update.message.reply_text(
        texts['passengers_prompt'],
        reply_markup=ReplyKeyboardMarkup(texts['passengers'], one_time_keyboard=True, resize_keyboard=True)
    )
    return PASSENGERS

async def set_passengers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass_choice = update.message.text
    lang = context.user_data.get('lang', 'RU')
    texts = LANG_TEXTS[lang]

    if '✏️' in pass_choice:
        await update.message.reply_text(texts['passengers_custom_prompt'], reply_markup=ReplyKeyboardRemove())
        return PASSENGERS

    context.user_data['passengers'] = pass_choice
    await update.message.reply_text(
        texts['luggage_prompt'],
        reply_markup=ReplyKeyboardMarkup(texts['luggage'], one_time_keyboard=True, resize_keyboard=True)
    )
    return LUGGAGE

async def set_luggage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lugg_choice = update.message.text
    lang = context.user_data.get('lang', 'RU')
    texts = LANG_TEXTS[lang]

    if '✏️' in lugg_choice:
        await update.message.reply_text(texts['luggage_custom_prompt'], reply_markup=ReplyKeyboardRemove())
        return LUGGAGE

    context.user_data['luggage'] = lugg_choice
    await update.message.reply_text(
        texts['transfer_prompt'],
        reply_markup=ReplyKeyboardMarkup(texts['transfer_types'], one_time_keyboard=True, resize_keyboard=True)
    )
    return TRANSFER_TYPE

async def set_transfer_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['transfer_type'] = update.message.text
    lang = context.user_data.get('lang', 'RU')
    texts = LANG_TEXTS[lang]

    phone_btn = ReplyKeyboardMarkup(
        [[KeyboardButton(texts['phone_btn'], request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text(texts['phone_prompt'], reply_markup=phone_btn)
    return PHONE

async def set_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text
    context.user_data['phone'] = phone

    lang = context.user_data.get('lang', 'RU')
    texts = LANG_TEXTS[lang]

    user = update.effective_user
    username = f"@{user.username}" if user.username else "нет username"

    admin_card = (
        "📥 НОВАЯ ЗАЯВКА НА ТРАНСФЕР!\n\n"
        f"👤 Клиент: {user.full_name} ({username})\n"
        f"🌐 Язык: {lang}\n"
        f"🛣 Маршрут: {context.user_data.get('route')}\n"
        f"📍 Адрес: {context.user_data.get('address')}\n"
        f"📅 Дата: {context.user_data.get('date')}\n"
        f"⏰ Время/Рейс: {context.user_data.get('time')}\n"
        f"👥 Пассажиры: {context.user_data.get('passengers')}\n"
        f"🧳 Багаж: {context.user_data.get('luggage')}\n"
        f"🚘 Тип: {context.user_data.get('transfer_type')}\n"
        f"📞 Телефон: {phone}"
    )

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=admin_card)
        except Exception as e:
            print(f"Ошибка отправки администратору: {e}")

    await update.message.reply_text(texts['success'], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено / Cancelled.", reply_markup=ReplyKeyboardRemove())
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
