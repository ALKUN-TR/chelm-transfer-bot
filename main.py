import os
import logging
import asyncio
import threading
from flask import Flask
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

# Настройка логов
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask для поддержания порта на Render
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

LANGUAGES = {
    'ua': {
        'welcome': "Вітаємо! Оберіть напрямок поїздки:",
        'routes': ["Хелм ➔ Польща", "Польща ➔ Хелм", "🚘 Інший маршрут"],
        'select_date': "Оберіть дату поїздки:",
        'dates': ["Сьогодні", "Завтра", "📅 Інша дата"],
        'enter_date': "Будь ласка, напишіть дату поїздки у чат (наприклад, 25.10):",
        'select_time': "Оберіть або введіть час:",
        'times': ["08:00", "12:00", "16:00", "20:00", "✏️ Свій час"],
        'enter_time': "Введіть зручний для вас час у чат:",
        'select_passengers': "Вкажіть кількість пасажирів:",
        'passengers': ["1", "2", "3", "4+"],
        'select_luggage': "Оберіть кількість багажу:",
        'luggages': ["Без багажу", "1 валіза", "2 валізи", "🧳 Багато багажу"],
        'enter_address': "Введіть точну адресу посадки/висадки у чат:",
        'share_phone': "📱 Натисніть кнопку нижче, щоб передати номер телефону:",
        'btn_phone': "📱 Поділитися номером телефону",
        'success': "✅ Дякуємо! Вашу заявку прийнято. Менеджер зв'яжеться з вами найближчим часом.",
        'cancelled': "❌ Вашу заявку скасовано.",
        'btn_back': "⬅️ Назад",
        'btn_restart': "🔄 Почати спочатку",
        'btn_new_order': "➕ Оформити нову заявку",
        'btn_cancel_order': "❌ Скасувати заявку",
        'confirm_cancel': "Ви впевнені, що хочете скасувати цю заявку?",
        'yes_cancel': "Так, скасувати",
        'no_keep': "Ні, залишити"
    },
    'pl': {
        'welcome': "Witamy! Wybierz kierunek jazdy:",
        'routes': ["Chełm ➔ Polska", "Polska ➔ Chełm", "🚘 Inna trasa"],
        'select_date': "Wybierz datę przejazdu:",
        'dates': ["Dzisiaj", "Jutro", "📅 Inna data"],
        'enter_date': "Proszę wpisać datę przejazdu na czacie (np. 25.10):",
        'select_time': "Wybierz lub wpisz godzinę:",
        'times': ["08:00", "12:00", "16:00", "20:00", "✏️ Inna godzina"],
        'enter_time': "Wpisz dogodną godzinę na czacie:",
        'select_passengers': "Wybierz liczbę pasażerów:",
        'passengers': ["1", "2", "3", "4+"],
        'select_luggage': "Wybierz ilość bagażu:",
        'luggages': ["Bez bagażu", "1 walizka", "2 walizki", "🧳 Dużo bagażu"],
        'enter_address': "Wpisz dokładny adres odbioru/dojazdu na czacie:",
        'share_phone': "📱 Kliknij przycisk poniżej, aby udostępnić numer:",
        'btn_phone': "📱 Udostępnij numer telefonu",
        'success': "✅ Dziękujemy! Zgłoszenie zostało przyjęte. Menedżer skontaktuje się z Tobą.",
        'cancelled': "❌ Twoje zgłoszenie zostało anulowane.",
        'btn_back': "⬅️ Wstecz",
        'btn_restart': "🔄 Zacznij od nowa",
        'btn_new_order': "➕ Nowe zamówienie",
        'btn_cancel_order': "❌ Anuluj zamówienie",
        'confirm_cancel': "Czy na pewno chcesz anulować to zamówienie?",
        'yes_cancel': "Tak, anuluj",
        'no_keep': "Nie, zostaw"
    },
    'en': {
        'welcome': "Welcome! Select your route:",
        'routes': ["Chełm ➔ Poland", "Poland ➔ Chełm", "🚘 Custom route"],
        'select_date': "Select date of trip:",
        'dates': ["Today", "Tomorrow", "📅 Other date"],
        'enter_date': "Please type the date in chat (e.g., 25.10):",
        'select_time': "Select or type time:",
        'times': ["08:00", "12:00", "16:00", "20:00", "✏️ Custom time"],
        'enter_time': "Type your preferred time in chat:",
        'select_passengers': "Select number of passengers:",
        'passengers': ["1", "2", "3", "4+"],
        'select_luggage': "Select luggage amount:",
        'luggages': ["No luggage", "1 suitcase", "2 suitcases", "🧳 Heavy luggage"],
        'enter_address': "Type exact pick-up/drop-off address in chat:",
        'share_phone': "📱 Press the button below to share your phone number:",
        'btn_phone': "📱 Share phone number",
        'success': "✅ Thank you! Your booking is received. Manager will contact you shortly.",
        'cancelled': "❌ Your booking has been cancelled.",
        'btn_back': "⬅️ Back",
        'btn_restart': "🔄 Start over",
        'btn_new_order': "➕ New booking",
        'btn_cancel_order': "❌ Cancel booking",
        'confirm_cancel': "Are you sure you want to cancel this booking?",
        'yes_cancel': "Yes, cancel",
        'no_keep': "No, keep"
    },
    'ru': {
        'welcome': "Добро пожаловать! Выберите направление поездки:",
        'routes': ["Хелм ➔ Польша", "Польша ➔ Хелм", "🚘 Другой маршрут"],
        'select_date': "Выберите дату поездки:",
        'dates': ["Сегодня", "Завтра", "📅 Другая дата"],
        'enter_date': "Пожалуйста, напишите дату поездки в чат (например, 25.10):",
        'select_time': "Выберите или введите время:",
        'times': ["08:00", "12:00", "16:00", "20:00", "✏️ Свое время"],
        'enter_time': "Введите удобное время в чат:",
        'select_passengers': "Укажите количество пассажиров:",
        'passengers': ["1", "2", "3", "4+"],
        'select_luggage': "Выберите количество багажа:",
        'luggages': ["Без багажа", "1 чемодан", "2 чемодана", "🧳 Много багажа"],
        'enter_address': "Введите точный адрес посадки/высадки в чат:",
        'share_phone': "📱 Нажмите кнопку внизу, чтобы передать номер телефона:",
        'btn_phone': "📱 Поделиться номером телефона",
        'success': "✅ Спасибо! Ваша заявка принята. Менеджер свяжется с вами в ближайшее время.",
        'cancelled': "❌ Ваша заявка отменена.",
        'btn_back': "⬅️ Назад",
        'btn_restart': "🔄 Начать сначала",
        'btn_new_order': "➕ Оформить новую заявку",
        'btn_cancel_order': "❌ Отменить заявку",
        'confirm_cancel': "Вы уверены, что хотите отменить заявку?",
        'yes_cancel': "Да, отменить",
        'no_keep': "Нет, оставить"
    }
}

def get_nav_buttons(lang_code, show_back=True):
    txt = LANGUAGES[lang_code]
    row = []
    if show_back:
        row.append(InlineKeyboardButton(txt['btn_back'], callback_data="nav_back"))
    row.append(InlineKeyboardButton(txt['btn_restart'], callback_data="nav_restart"))
    return row

async def safe_delete_user_msg(context, chat_id, message_id):
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua"),
         InlineKeyboardButton("🇵🇱 Polski", callback_data="lang_pl")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = "🌐 Please select your language / Оберіть мову:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=markup)
    else:
        msg = await update.message.reply_text(text=text, reply_markup=markup)
        context.user_data['card_msg_id'] = msg.message_id

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "nav_restart":
        await start_command(update, context)
        return

    if data.startswith("lang_"):
        lang = data.split("_")[1]
        context.user_data['lang'] = lang
        context.user_data['step'] = 'route'
        await render_step(query, context)
        return

    lang = context.user_data.get('lang', 'ua')

    if data == "nav_back":
        step = context.user_data.get('step')
        steps_order = ['route', 'date', 'time', 'passengers', 'luggage', 'address', 'phone']
        if step in steps_order:
            idx = steps_order.index(step)
            if idx > 0:
                context.user_data['step'] = steps_order[idx - 1]
            else:
                await start_command(update, context)
                return
        await render_step(query, context)
        return

    step = context.user_data.get('step')
    
    if step == 'route':
        context.user_data['route'] = data
        context.user_data['step'] = 'date'
    elif step == 'date':
        if data == "custom_date":
            context.user_data['awaiting_text'] = 'date'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_date'], reply_markup=markup)
            return
        context.user_data['date'] = data
        context.user_data['step'] = 'time'
    elif step == 'time':
        if data == "custom_time":
            context.user_data['awaiting_text'] = 'time'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_time'], reply_markup=markup)
            return
        context.user_data['time'] = data
        context.user_data['step'] = 'passengers'
    elif step == 'passengers':
        context.user_data['passengers'] = data
        context.user_data['step'] = 'luggage'
    elif step == 'luggage':
        context.user_data['luggage'] = data
        context.user_data['step'] = 'address'
        context.user_data['awaiting_text'] = 'address'
        txt = LANGUAGES[lang]
        markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
        await query.edit_message_text(txt['enter_address'], reply_markup=markup)
        return
    elif data == "ask_cancel":
        txt = LANGUAGES[lang]
        keyboard = [
            [InlineKeyboardButton(txt['yes_cancel'], callback_data="confirm_cancel")],
            [InlineKeyboardButton(txt['no_keep'], callback_data="keep_order")]
        ]
        await query.edit_message_text(txt['confirm_cancel'], reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data == "keep_order":
        txt = LANGUAGES[lang]
        keyboard = [
            [InlineKeyboardButton(txt['btn_new_order'], callback_data="nav_restart")],
            [InlineKeyboardButton(txt['btn_cancel_order'], callback_data="ask_cancel")]
        ]
        await query.edit_message_text(txt['success'], reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data == "confirm_cancel":
        txt = LANGUAGES[lang]
        await query.edit_message_text(txt['cancelled'])
        
        if ADMIN_CHAT_ID:
            user = update.effective_user
            cancel_msg = (
                f"🚫 **ЗАЯВКА ОТМЕНЕНА КЛИЕНТОМ!**\n"
                f"👤 Клиент: {user.full_name} (@{user.username or 'нет'})\n"
                f"🛣 Маршрут: {context.user_data.get('route')}\n"
                f"📅 Дата: {context.user_data.get('date')}\n"
                f"📞 Телефон: {context.user_data.get('phone')}"
            )
            try:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=cancel_msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Error sending cancellation to admin: {e}")
        return

    await render_step(query, context)

async def render_step(query, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ua')
    txt = LANGUAGES[lang]
    step = context.user_data.get('step', 'route')
    
    keyboard = []
    
    if step == 'route':
        text = txt['welcome']
        for r in txt['routes']:
            keyboard.append([InlineKeyboardButton(r, callback_data=r)])
        keyboard.append(get_nav_buttons(lang, show_back=False))
        
    elif step == 'date':
        text = txt['select_date']
        keyboard.append([InlineKeyboardButton(txt['dates'][0], callback_data=txt['dates'][0]),
                         InlineKeyboardButton(txt['dates'][1], callback_data=txt['dates'][1])])
        keyboard.append([InlineKeyboardButton(txt['dates'][2], callback_data="custom_date")])
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'time':
        text = txt['select_time']
        row = [InlineKeyboardButton(t, callback_data=t) for t in txt['times'][:4]]
        keyboard.append(row)
        keyboard.append([InlineKeyboardButton(txt['times'][4], callback_data="custom_time")])
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'passengers':
        text = txt['select_passengers']
        row = [InlineKeyboardButton(p, callback_data=p) for p in txt['passengers']]
        keyboard.append(row)
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'luggage':
        text = txt['select_luggage']
        for l in txt['luggages']:
            keyboard.append([InlineKeyboardButton(l, callback_data=l)])
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'phone':
        text = txt['share_phone']
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton(txt['btn_phone'], request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await query.message.reply_text(text, reply_markup=reply_markup)
        return

    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=markup)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_delete_user_msg(context, update.effective_chat.id, update.message.message_id)
    
    awaiting = context.user_data.get('awaiting_text')
    card_msg_id = context.user_data.get('card_msg_id')
    user_text = update.message.text
    
    if not awaiting or not card_msg_id:
        return
        
    if awaiting == 'date':
        context.user_data['date'] = user_text
        context.user_data['step'] = 'time'
    elif awaiting == 'time':
        context.user_data['time'] = user_text
        context.user_data['step'] = 'passengers'
    elif awaiting == 'address':
        context.user_data['address'] = user_text
        context.user_data['step'] = 'phone'
        
    context.user_data['awaiting_text'] = None
    
    class DummyQuery:
        def __init__(self, msg):
            self.message = msg
        async def edit_message_text(self, text, reply_markup=None):
            await context.bot.edit_message_text(
                chat_id=self.message.chat_id,
                message_id=self.message.message_id,
                text=text,
                reply_markup=reply_markup
            )
            
    dummy_msg = type('Msg', (), {'chat_id': update.effective_chat.id, 'message_id': card_msg_id})()
    await render_step(DummyQuery(dummy_msg), context)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_delete_user_msg(context, update.effective_chat.id, update.message.message_id)
    
    contact = update.message.contact
    phone = contact.phone_number
    context.user_data['phone'] = phone
    lang = context.user_data.get('lang', 'ua')
    txt = LANGUAGES[lang]

    hide_kb = await update.message.reply_text(".", reply_markup=ReplyKeyboardRemove())
    await safe_delete_user_msg(context, update.effective_chat.id, hide_kb.message_id)

    if ADMIN_CHAT_ID:
        user = update.effective_user
        order_msg = (
            f"📥 **НОВАЯ ЗАЯВКА НА ТРАНСФЕР!**\n\n"
            f"👤 **Пассажир:** {user.full_name} (@{user.username or 'нет'})\n"
            f"📞 **Телефон:** `{phone}`\n"
            f"🛣 **Маршрут:** {context.user_data.get('route')}\n"
            f"📅 **Дата:** {context.user_data.get('date')}\n"
            f"⏰ **Время:** {context.user_data.get('time')}\n"
            f"👥 **Пассажиры:** {context.user_data.get('passengers')}\n"
            f"🧳 **Багаж:** {context.user_data.get('luggage')}\n"
            f"📍 **Адрес:** {context.user_data.get('address')}"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error sending order to admin: {e}")

    card_msg_id = context.user_data.get('card_msg_id')
    keyboard = [
        [InlineKeyboardButton(txt['btn_new_order'], callback_data="nav_restart")],
        [InlineKeyboardButton(txt['btn_cancel_order'], callback_data="ask_cancel")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    
    if card_msg_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=card_msg_id,
            text=txt['success'],
            reply_markup=markup
        )

# Роут веб-сервера
@app.route('/')
def index():
    return "Bot is alive!", 200

def run_flask():
    """Фоновый запуск веб-сервера Flask для Render"""
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

async def main():
    """Главная асинхронная точка входа для запуска бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN variable is missing!")
        return

    tg_app = Application.builder().token(BOT_TOKEN).build()

    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(CallbackQueryHandler(handle_callback))
    tg_app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Сброс старых обновлений/вебхуков при старте
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling(drop_pending_updates=True)
    
    logger.info("Bot successfully started in polling mode!")

    # Держим событийный цикл активным
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        await tg_app.updater.stop()
        await tg_app.stop()

if __name__ == '__main__':
    # Запускаем Flask на отдельном фоне
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Основной поток передаем под асинхронную работу Telegram-бота
    asyncio.run(main())
