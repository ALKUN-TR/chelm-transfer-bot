import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

LANGUAGE, ROUTE, ADDRESS, DATE, TIME, PASSENGERS, CUSTOM_PASSENGERS, LUGGAGE, CUSTOM_LUGGAGE, TRANSFER_TYPE, CONTACT = range(11)

TEXTS = {
    'UA': {
        'welcome': "Вітаємо! 🚖 Сервіс трансферу Хелм ↔️ Польща.\nОберіть напрямок вашої поїздки:",
        'routes': [["🚆 З Хелма", "🚉 До Хелма"], ["🚘 Інший маршрут"]],
        'ask_address_chelm': "📍 Вкажіть точну адресу, вокзал або аеропорт призначення/відправлення:\n(Наприклад: Аеропорт Шопена, вокзал Західний у Варшаві)",
        'ask_address_other': "📍 Вкажіть, звідки і куди вам потрібно доїхати (пункт А та пункт Б):\n(Наприклад: Люблін ↔ Аеропорт Модлін)",
        'dates': [["📅 Сьогодні", "📅 Завтра"], ["🗓 Вказати іншу дату"]],
        'ask_time': "⏰ Вкажіть точний час відправлення або номер потягу/рейсу:\n(Наприклад: 14:30 або потяг №119, прибуття о 16:45)",
        'passengers': [["👤 1 пасажир", "👥 2 пасажири"], ["👥 3 пасажири", "👨‍👩‍👧‍👦 4 пасажири"], ["✏️ Свій варіант"]],
        'ask_custom_passengers': "Вкажіть кількість пасажирів (наприклад: 5 дорослих і дитина):",
        'luggage': [["🧳 1 валіза", "🧳 2 валізи"], ["🧳 3 валізи", "🧳 4 валізи"], ["✏️ Свій варіант"]],
        'ask_custom_luggage': "Вкажіть кількість багажу (наприклад: 2 великі сумки + дитячий візок):",
        'transfer_type': [["🚘 Індивідуальний", "👥 Спільна поїздка"], ["🤷‍♂️ Будь-який варіант"]],
        'ask_contact': "📱 Натисніть кнопку нижче, щоб поділитися номером телефону:",
        'share_phone': "📱 Поділитися номером телефону",
        'thanks': "Дякуємо за замовлення! У максимально короткий час з Вами зв'яжеться менеджер для підтвердження та уточнення деталей.\n\n💡 *Якщо у Вас термінове питання, Ви можете написати диспетчеру напряму:* @ALKUNTR"
    },
    'PL': {
        'welcome': "Witamy! 🚖 Transfer Chełm ↔️ Polska.\nWybierz kierunek jazdy:",
        'routes': [["🚆 Z Chełma", "🚉 Do Chełma"], ["🚘 Inna trasa"]],
        'ask_address_chelm': "📍 Podaj dokładny adres, dworzec lub lotnisko:",
        'ask_address_other': "📍 Podaj skąd i dokąd chcesz jechać (punkt A i punkt B):\n(Np. Lublin ↔ Lotnisko Modlin)",
        'dates': [["📅 Dzisiaj", "📅 Jutro"], ["🗓 Inna data"]],
        'ask_time': "⏰ Podaj dokładną godzinę odjazdu lub numer pociągu/lotu:",
        'passengers': [["👤 1 pasażer", "👥 2 pasażerów"], ["👥 3 pasażerów", "👨‍👩‍👧‍👦 4 pasażerów"], ["✏️ Inny wariant"]],
        'ask_custom_passengers': "Podaj liczbę pasażerów:",
        'luggage': [["🧳 1 walizka", "🧳 2 walizki"], ["🧳 3 walizki", "🧳 4 walizki"], ["✏️ Inny wariant"]],
        'ask_custom_luggage': "Podaj ilość bagażu:",
        'transfer_type': [["🚘 Indywidualny", "👥 Wspólny przejazd"], ["🤷‍♂️ Dowolny wariant"]],
        'ask_contact': "📱 Kliknij przycisk poniżej, aby udostępnić numer telefonu:",
        'share_phone': "📱 Udostępnij numer telefonu",
        'thanks': "Dziękujemy za zamówienie! Manager skontaktuje się z Tobą w najkrótszym możliwym czasie.\n\n💡 *Jeśli masz pilne pytanie, możesz napisać bezpośrednio do dyspozytora:* @ALKUNTR"
    },
    'EN': {
        'welcome': "Welcome! 🚖 Transfer Service Chełm ↔️ Poland.\nSelect your route:",
        'routes': [["🚆 From Chełm", "🚉 To Chełm"], ["🚘 Other route"]],
        'ask_address_chelm': "📍 Enter exact address, station, or airport:",
        'ask_address_other': "📍 Please specify where from and where to (Point A to Point B):\n(e.g., Lublin ↔ Modlin Airport)",
        'dates': [["📅 Today", "📅 Tomorrow"], ["🗓 Other date"]],
        'ask_time': "⏰ Enter departure time or train/flight number:",
        'passengers': [["👤 1 passenger", "👥 2 passengers"], ["👥 3 passengers", "👨‍👩‍👧‍👦 4 passengers"], ["✏️ Custom"]],
        'ask_custom_passengers': "Enter passenger count:",
        'luggage': [["🧳 1 suitcase", "🧳 2 suitcases"], ["🧳 3 suitcases", "🧳 4 suitcases"], ["✏️ Custom"]],
        'ask_custom_luggage': "Enter luggage details:",
        'transfer_type': [["🚘 Individual", "👥 Shared trip"], ["🤷‍♂️ Any option"]],
        'ask_contact': "📱 Tap the button below to share your phone number:",
        'share_phone': "📱 Share phone number",
        'thanks': "Thank you for your order! A manager will contact you as soon as possible.\n\n💡 *If you have an urgent question, you can message the dispatcher directly:* @ALKUNTR"
    },
    'RU': {
        'welcome': "Приветствуем! 🚖 Сервис трансфера Хелм ↔️ Польша.\nВыберите направление:",
        'routes': [["🚆 Из Хелма", "🚉 В Хелм"], ["🚘 Другой маршрут"]],
        'ask_address_chelm': "📍 Укажите точный адрес, вокзал или аэропорт назначения/отправления:",
        'ask_address_other': "📍 Укажите, откуда и куда вам нужно доехать (пункт А и пункт Б):\n(Например: Люблин ↔ Аэропорт Модлин)",
        'dates': [["📅 Сегодня", "📅 Завтра"], ["🗓 Другая дата"]],
        'ask_time': "⏰ Укажите точное время отправления или номер поезда/рейса:",
        'passengers': [["👤 1 пассажир", "👥 2 пассажира"], ["👥 3 пассажира", "👨‍👩‍👧‍👦 4 пассажира"], ["✏️ Свой вариант"]],
        'ask_custom_passengers': "Укажите количество пассажиров:",
        'luggage': [["🧳 1 чемодан", "🧳 2 чемодана"], ["🧳 3 чемодана", "🧳 4 чемодана"], ["✏️ Свой вариант"]],
        'ask_custom_luggage': "Укажите количество багажа:",
        'transfer_type': [["🚘 Индивидуальный", "👥 Совместная поездка"], ["🤷‍♂️ Любой вариант"]],
        'ask_contact': "📱 Нажмите кнопку ниже, чтобы поделиться номером телефона:",
        'share_phone': "📱 Поделиться номером телефона",
        'thanks': "Спасибо за заказ! В максимально короткое время с Вами свяжется менеджер для подтверждения и уточнения деталей.\n\n💡 *Если у Вас срочный вопрос, Вы можете написать диспетчеру напрямую:* @ALKUNTR"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["🇺🇦 Українська", "🇵🇱 Polski"], ["🇬🇧 English", "🇷🇺 Русский"]]
    await update.message.reply_text(
        "Оберіть мову / Wybierz język / Choose language / Выберите язык:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = update.message.text
    if "🇺🇦" in lang_code:
        context.user_data['lang'] = 'UA'
    elif "🇵🇱" in lang_code:
        context.user_data['lang'] = 'PL'
    elif "🇬🇧" in lang_code:
        context.user_data['lang'] = 'EN'
    else:
        context.user_data['lang'] = 'RU'
    
    lang = context.user_data['lang']
    t = TEXTS[lang]
    await update.message.reply_text(
        t['welcome'],
        reply_markup=ReplyKeyboardMarkup(t['routes'], resize_keyboard=True)
    )
    return ROUTE

async def set_route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    route_choice = update.message.text
    context.user_data['route'] = route_choice
    lang = context.user_data['lang']
    t = TEXTS[lang]
    
    if "🚘" in route_choice:
        prompt = t['ask_address_other']
    else:
        prompt = t['ask_address_chelm']

    await update.message.reply_text(prompt, reply_markup=ReplyKeyboardRemove())
    return ADDRESS

async def set_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    lang = context.user_data['lang']
    t = TEXTS[lang]
    await update.message.reply_text(
        "Дата:",
        reply_markup=ReplyKeyboardMarkup(t['dates'], resize_keyboard=True)
    )
    return DATE

async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    lang = context.user_data['lang']
    t = TEXTS[lang]
    await update.message.reply_text(t['ask_time'], reply_markup=ReplyKeyboardRemove())
    return TIME

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    lang = context.user_data['lang']
    t = TEXTS[lang]
    await update.message.reply_text(
        "Пассажиры:",
        reply_markup=ReplyKeyboardMarkup(t['passengers'], resize_keyboard=True)
    )
    return PASSENGERS

async def set_passengers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang = context.user_data['lang']
    t = TEXTS[lang]
    if "✏️" in text:
        await update.message.reply_text(t['ask_custom_passengers'], reply_markup=ReplyKeyboardRemove())
        return CUSTOM_PASSENGERS
    context.user_data['passengers'] = text
    await update.message.reply_text(
        "Багаж:",
        reply_markup=ReplyKeyboardMarkup(t['luggage'], resize_keyboard=True)
    )
    return LUGGAGE

async def set_custom_passengers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['passengers'] = update.message.text
    lang = context.user_data['lang']
    t = TEXTS[lang]
    await update.message.reply_text(
        "Багаж:",
        reply_markup=ReplyKeyboardMarkup(t['luggage'], resize_keyboard=True)
    )
    return LUGGAGE

async def set_luggage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lang = context.user_data['lang']
    t = TEXTS[lang]
    if "✏️" in text:
        await update.message.reply_text(t['ask_custom_luggage'], reply_markup=ReplyKeyboardRemove())
        return CUSTOM_LUGGAGE
    context.user_data['luggage'] = text
    await update.message.reply_text(
        "Тип трансферу:",
        reply_markup=ReplyKeyboardMarkup(t['transfer_type'], resize_keyboard=True)
    )
    return TRANSFER_TYPE

async def set_custom_luggage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['luggage'] = update.message.text
    lang = context.user_data['lang']
    t = TEXTS[lang]
    await update.message.reply_text(
        "Тип трансферу:",
        reply_markup=ReplyKeyboardMarkup(t['transfer_type'], resize_keyboard=True)
    )
    return TRANSFER_TYPE

async def set_transfer_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['transfer_type'] = update.message.text
    lang = context.user_data['lang']
    t = TEXTS[lang]
    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(t['share_phone'], request_contact=True)]],
        resize_keyboard=True
    )
    await update.message.reply_text(t['ask_contact'], reply_markup=contact_keyboard)
    return CONTACT

async def set_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text
    user = update.message.from_user
    lang = context.user_data['lang']
    t = TEXTS[lang]

    summary = (
        f"📥 **НОВА ЗАЯВКА НА ТРАНСФЕР!**\n\n"
        f"👤 **Клієнт:** {user.full_name} (@{user.username})\n"
        f"🌐 **Мова:** {lang}\n"
        f"🛣 **Маршрут:** {context.user_data.get('route')}\n"
        f"📍 **Адреса / Пункти:** {context.user_data.get('address')}\n"
        f"📅 **Дата:** {context.user_data.get('date')}\n"
        f"⏰ **Час/Рейс:** {context.user_data.get('time')}\n"
        f"👥 **Пасажири:** {context.user_data.get('passengers')}\n"
        f"🧳 **Багаж:** {context.user_data.get('luggage')}\n"
        f"🚘 **Тип:** {context.user_data.get('transfer_type')}\n"
        f"📞 **Телефон:** {phone}"
    )

    admin_id = os.environ.get('ADMIN_CHAT_ID')
    if admin_id:
        try:
            await context.bot.send_message(chat_id=admin_id, text=summary, parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Error sending message to admin: {e}")

    await update.message.reply_text(t['thanks'], reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
    return ConversationHandler.END

def main():
    token = os.environ.get('BOT_TOKEN')
    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            ROUTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_route)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_address)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time)],
            PASSENGERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_passengers)],
            CUSTOM_PASSENGERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_custom_passengers)],
            LUGGAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_luggage)],
            CUSTOM_LUGGAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_custom_luggage)],
            TRANSFER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_transfer_type)],
            CONTACT: [MessageHandler(filters.TEXT | filters.CONTACT, set_contact)],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
