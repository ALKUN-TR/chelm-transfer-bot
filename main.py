import os
import logging
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

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Flask для Render
app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Контакт менеджера для срочной связи
MANAGER_CONTACT = "@ALKUNTR"

def escape_markdown(text) -> str:
    """Безопасное экранирование специальных символов Markdown V1"""
    if text is None or text == "":
        return "-"
    text_str = str(text)
    for char in ['_', '*', '`', '[']:
        text_str = text_str.replace(char, f'\\{char}')
    return text_str

LANGUAGES = {
    'ua': {
        'welcome': "Вітаємо! Оберіть напрямок поїздки:",
        'routes': ["Хелм ➔ Польща", "Польща ➔ Хелм", "🚘 Інший маршрут"],
        'select_type': "Оберіть тип трансферу:",
        'types': ["🚗 Індивідуальний трансфер", "👥 З попутниками (помісно)", "🤷 Не має значення"],
        'select_date': "Оберіть дату поїздки:",
        'dates': ["Сьогодні", "Завтра", "📅 Інша дата"],
        'enter_date': "Будь ласка, напишіть дату поїздки у чат (наприклад, 25.10):",
        'enter_time': "Введіть зручний для вас час у чат (наприклад, 14:30):",
        'select_passengers': "Вкажіть кількість пасажирів:",
        'passengers': ["1", "2", "3", "4", "✏️ Свій варіант"],
        'enter_passengers': "Введіть кількість пасажирів у чат:",
        'select_luggage': "Оберіть кількість багажу:",
        'luggages': ["1 чемодан", "2 чемодани", "3 чемодани", "4 чемодани", "🧳 Свій варіант"],
        'enter_luggage': "Опишіть ваш багаж у чат:",
        'enter_pickup': "Введіть точну адресу або місце ПОСАДКИ у чат:",
        'enter_dropoff': "Введіть точну адресу або місце ВЫСАДКИ у чат:",
        'select_comm': "Як з вами краще зв'язатися?",
        'comms': ["💬 Telegram", "🟢 WhatsApp", "📞 Дзвінок"],
        'share_phone': "📱 Натисніть кнопку нижче, щоб передати номер телефону:",
        'btn_phone': "📱 Поділитися номером телефону",
        'summary_title': "📋 **Перевірте дані вашої заявки:**",
        'urgent_contact': f"⚡️ У разі терміновості ви можете зв'язатися з менеджером напряму: {escape_markdown(MANAGER_CONTACT)}",
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
        'select_type': "Wybierz typ transferu:",
        'types': ["🚗 Transfer indywidualny", "👥 Z współpasażerami", "🤷 Bez znaczenia"],
        'select_date': "Wybierz datę przejazdu:",
        'dates': ["Dzisiaj", "Jutro", "📅 Inna data"],
        'enter_date': "Proszę wpisać datę przejazdu na czacie (np. 25.10):",
        'enter_time': "Wpisz dogodną godzinę na czacie (np. 14:30):",
        'select_passengers': "Wybierz liczbę pasażerów:",
        'passengers': ["1", "2", "3", "4", "✏️ Inna opcja"],
        'enter_passengers': "Wpisz liczbę pasażerów na czacie:",
        'select_luggage': "Wybierz ilość bagażu:",
        'luggages': ["1 walizka", "2 walizki", "3 walizki", "4 walizki", "🧳 Inna opcja"],
        'enter_luggage': "Opisz swój bagaż na czacie:",
        'enter_pickup': "Wpisz dokładny adres/miejsce ODBIORU na czacie:",
        'enter_dropoff': "Wpisz dokładny adres/miejsce DOJAZDU na czacie:",
        'select_comm': "Jak najlepiej się z Tobą skontaktować?",
        'comms': ["💬 Telegram", "🟢 WhatsApp", "📞 Połączenie telefoniczne"],
        'share_phone': "📱 Kliknij przycisk poniżej, aby udostępnić numer:",
        'btn_phone': "📱 Udostępnij numer telefonu",
        'summary_title': "📋 **Sprawdź szczegóły zamówienia:**",
        'urgent_contact': f"⚡️ W pilnych sprawach możesz skontaktować się bezpośrednio z menedżerem: {escape_markdown(MANAGER_CONTACT)}",
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
        'select_type': "Select transfer type:",
        'types': ["🚗 Private transfer", "👥 Shared transfer", "🤷 No preference"],
        'select_date': "Select date of trip:",
        'dates': ["Today", "Tomorrow", "📅 Other date"],
        'enter_date': "Please type the date in chat (e.g., 25.10):",
        'enter_time': "Type your preferred time in chat (e.g., 14:30):",
        'select_passengers': "Select number of passengers:",
        'passengers': ["1", "2", "3", "4", "✏️ Custom option"],
        'enter_passengers': "Type number of passengers in chat:",
        'select_luggage': "Select luggage amount:",
        'luggages': ["1 suitcase", "2 suitcases", "3 suitcases", "4 suitcases", "🧳 Custom option"],
        'enter_luggage': "Describe your luggage in chat:",
        'enter_pickup': "Type exact PICK-UP address or location in chat:",
        'enter_dropoff': "Type exact DROP-OFF address or location in chat:",
        'select_comm': "How should we contact you?",
        'comms': ["💬 Telegram", "🟢 WhatsApp", "📞 Phone call"],
        'share_phone': "📱 Press the button below to share your phone number:",
        'btn_phone': "📱 Share phone number",
        'summary_title': "📋 **Please review your booking:**",
        'urgent_contact': f"⚡️ In case of urgency, you can contact the manager directly: {escape_markdown(MANAGER_CONTACT)}",
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
        'select_type': "Выберите тип трансфера:",
        'types': ["🚗 Индивидуальный трансфер", "👥 С попутчиками (поместно)", "🤷 Без разницы"],
        'select_date': "Выберите дату поездки:",
        'dates': ["Сегодня", "Завтра", "📅 Другая дата"],
        'enter_date': "Пожалуйста, напишите дату поездки в чат (например, 25.10):",
        'enter_time': "Введите удобное время в чат (например, 14:30):",
        'select_passengers': "Укажите количество пассажиров:",
        'passengers': ["1", "2", "3", "4", "✏️ Свой вариант"],
        'enter_passengers': "Введите количество пассажиров в чат:",
        'select_luggage': "Выберите количество багажа:",
        'luggages': ["1 чемодан", "2 чемодана", "3 чемодана", "4 чемодана", "🧳 Свой вариант"],
        'enter_luggage': "Опишите ваш багаж в чат:",
        'enter_pickup': "Введите точный адрес или место ПОСАДКИ в чат:",
        'enter_dropoff': "Введите точный адрес или место ВЫСАДКИ в чат:",
        'select_comm': "Как с вами лучше связаться?",
        'comms': ["💬 Telegram", "🟢 WhatsApp", "📞 Звонок"],
        'share_phone': "📱 Нажмите кнопку внизу, чтобы передать номер телефона:",
        'btn_phone': "📱 Поделиться номером телефона",
        'summary_title': "📋 **Проверьте данные вашей заявки:**",
        'urgent_contact': f"⚡️ В случае срочности вы можете связаться с менеджером напрямую: {escape_markdown(MANAGER_CONTACT)}",
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

def build_summary_text(context_data, lang_code):
    txt = LANGUAGES[lang_code]
    summary = (
        f"{txt['summary_title']}\n\n"
        f"🛣 **Маршрут:** {escape_markdown(context_data.get('route'))}\n"
        f"🚘 **Тип трансфера:** {escape_markdown(context_data.get('transfer_type'))}\n"
        f"📅 **Дата:** {escape_markdown(context_data.get('date'))}\n"
        f"⏰ **Время:** {escape_markdown(context_data.get('time'))}\n"
        f"👥 **Пассажиры:** {escape_markdown(context_data.get('passengers'))}\n"
        f"🧳 **Багаж:** {escape_markdown(context_data.get('luggage'))}\n"
        f"📍 **Посадка:** {escape_markdown(context_data.get('pickup'))}\n"
        f"🏁 **Высадка:** {escape_markdown(context_data.get('dropoff'))}\n"
        f"💬 **Связь:** {escape_markdown(context_data.get('comm_channel'))}\n"
        f"📞 **Телефон:** `{escape_markdown(context_data.get('phone'))}`\n\n"
        f"{txt['success']}\n\n"
        f"{txt['urgent_contact']}"
    )
    return summary

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
        steps_order = ['route', 'transfer_type', 'date', 'time', 'passengers', 'luggage', 'pickup', 'dropoff', 'comm_channel', 'phone']
        if step in steps_order:
            idx = steps_order.index(step)
            if idx > 0:
                prev_step = steps_order[idx - 1]
                context.user_data['step'] = prev_step
            else:
                await start_command(update, context)
                return
        await render_step(query, context)
        return

    step = context.user_data.get('step')
    
    if step == 'route':
        context.user_data['route'] = data
        context.user_data['step'] = 'transfer_type'
    elif step == 'transfer_type':
        context.user_data['transfer_type'] = data
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
    elif step == 'passengers':
        if data == "custom_passengers":
            context.user_data['awaiting_text'] = 'passengers'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_passengers'], reply_markup=markup)
            return
        context.user_data['passengers'] = data
        context.user_data['step'] = 'luggage'
    elif step == 'luggage':
        if data == "custom_luggage":
            context.user_data['awaiting_text'] = 'luggage'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_luggage'], reply_markup=markup)
            return
        context.user_data['luggage'] = data
        context.user_data['step'] = 'pickup'
    elif step == 'comm_channel':
        context.user_data['comm_channel'] = data
        context.user_data['step'] = 'phone'
    elif data == "ask_cancel":
        txt = LANGUAGES[lang]
        keyboard = [
            [InlineKeyboardButton(txt['yes_cancel'], callback_data="confirm_cancel")],
            [InlineKeyboardButton(txt['no_keep'], callback_data="keep_order")]
        ]
        await query.edit_message_text(txt['confirm_cancel'], reply_markup=InlineKeyboardMarkup(keyboard))
        return
    elif data == "keep_order":
        summary_text = build_summary_text(context.user_data, lang)
        txt = LANGUAGES[lang]
        keyboard = [
            [InlineKeyboardButton(txt['btn_new_order'], callback_data="nav_restart")],
            [InlineKeyboardButton(txt['btn_cancel_order'], callback_data="ask_cancel")]
        ]
        await query.edit_message_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return
    elif data == "confirm_cancel":
        txt = LANGUAGES[lang]
        keyboard = [
            [InlineKeyboardButton(txt['btn_new_order'], callback_data="nav_restart")]
        ]
        await query.edit_message_text(txt['cancelled'], reply_markup=InlineKeyboardMarkup(keyboard))
        
        if ADMIN_CHAT_ID:
            user = update.effective_user
            cancel_msg = (
                f"🚫 **ЗАЯВКА ОТМЕНЕНА КЛИЕНТОМ!**\n"
                f"👤 Клиент: {escape_markdown(user.full_name)} (@{escape_markdown(user.username or 'нет')})\n"
                f"🛣 Маршрут: {escape_markdown(context.user_data.get('route', 'Не указан'))}\n"
                f"📅 Дата: {escape_markdown(context.user_data.get('date', 'Не указана'))}\n"
                f"📞 Телефон: `{escape_markdown(context.user_data.get('phone', 'Не указан'))}`"
            )
            try:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=cancel_msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Error sending cancellation to admin: {e}")
        return

    await render_step(query, context)

async def render_step(query_or_dummy, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ua')
    txt = LANGUAGES[lang]
    step = context.user_data.get('step', 'route')
    
    keyboard = []
    
    if step == 'route':
        context.user_data['awaiting_text'] = None
        text = txt['welcome']
        for r in txt['routes']:
            keyboard.append([InlineKeyboardButton(r, callback_data=r)])
        keyboard.append(get_nav_buttons(lang, show_back=False))
        
    elif step == 'transfer_type':
        context.user_data['awaiting_text'] = None
        text = txt['select_type']
        for t in txt['types']:
            keyboard.append([InlineKeyboardButton(t, callback_data=t)])
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'date':
        context.user_data['awaiting_text'] = None
        text = txt['select_date']
        keyboard.append([InlineKeyboardButton(txt['dates'][0], callback_data=txt['dates'][0]),
                         InlineKeyboardButton(txt['dates'][1], callback_data=txt['dates'][1])])
        keyboard.append([InlineKeyboardButton(txt['dates'][2], callback_data="custom_date")])
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'time':
        text = txt['enter_time']
        context.user_data['awaiting_text'] = 'time'
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'passengers':
        context.user_data['awaiting_text'] = None
        text = txt['select_passengers']
        p_list = txt['passengers']
        row = [InlineKeyboardButton(p_list[i], callback_data=p_list[i]) for i in range(4)]
        keyboard.append(row)
        keyboard.append([InlineKeyboardButton(p_list[4], callback_data="custom_passengers")])
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'luggage':
        context.user_data['awaiting_text'] = None
        text = txt['select_luggage']
        l_list = txt['luggages']
        keyboard.append([InlineKeyboardButton(l_list[0], callback_data=l_list[0]),
                         InlineKeyboardButton(l_list[1], callback_data=l_list[1])])
        keyboard.append([InlineKeyboardButton(l_list[2], callback_data=l_list[2]),
                         InlineKeyboardButton(l_list[3], callback_data=l_list[3])])
        keyboard.append([InlineKeyboardButton(l_list[4], callback_data="custom_luggage")])
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'pickup':
        text = txt['enter_pickup']
        context.user_data['awaiting_text'] = 'pickup'
        keyboard.append(get_nav_buttons(lang))

    elif step == 'dropoff':
        text = txt['enter_dropoff']
        context.user_data['awaiting_text'] = 'dropoff'
        keyboard.append(get_nav_buttons(lang))

    elif step == 'comm_channel':
        context.user_data['awaiting_text'] = None
        text = txt['select_comm']
        for c in txt['comms']:
            keyboard.append([InlineKeyboardButton(c, callback_data=c)])
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'phone':
        context.user_data['awaiting_text'] = None
        text = txt['share_phone']
        keyboard.append(get_nav_buttons(lang))
        markup = InlineKeyboardMarkup(keyboard)
        await query_or_dummy.edit_message_text(text=text, reply_markup=markup)
        
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton(txt['btn_phone'], request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        chat_id = context.user_data.get('chat_id', query_or_dummy.message.chat_id if hasattr(query_or_dummy, 'message') else query_or_dummy.chat_id)
        
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=txt['share_phone'],
            reply_markup=reply_markup
        )
        context.user_data['phone_msg_id'] = msg.message_id
        return

    markup = InlineKeyboardMarkup(keyboard)
    await query_or_dummy.edit_message_text(text=text, reply_markup=markup)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_delete_user_msg(context, update.effective_chat.id, update.message.message_id)
    
    awaiting = context.user_data.get('awaiting_text')
    card_msg_id = context.user_data.get('card_msg_id')
    user_text = update.message.text
    context.user_data['chat_id'] = update.effective_chat.id
    
    if not awaiting or not card_msg_id:
        return
        
    if awaiting == 'date':
        context.user_data['date'] = user_text
        context.user_data['step'] = 'time'
    elif awaiting == 'time':
        context.user_data['time'] = user_text
        context.user_data['step'] = 'passengers'
    elif awaiting == 'passengers':
        context.user_data['passengers'] = user_text
        context.user_data['step'] = 'luggage'
    elif awaiting == 'luggage':
        context.user_data['luggage'] = user_text
        context.user_data['step'] = 'pickup'
    elif awaiting == 'pickup':
        context.user_data['pickup'] = user_text
        context.user_data['step'] = 'dropoff'
    elif awaiting == 'dropoff':
        context.user_data['dropoff'] = user_text
        context.user_data['step'] = 'comm_channel'
        
    class DummyQuery:
        def __init__(self, chat_id, msg_id):
            self.chat_id = chat_id
            self.message_id = msg_id
        async def edit_message_text(self, text, reply_markup=None):
            await context.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=text,
                reply_markup=reply_markup
            )
            
    dummy = DummyQuery(update.effective_chat.id, card_msg_id)
    await render_step(dummy, context)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_delete_user_msg(context, update.effective_chat.id, update.message.message_id)
    
    if 'phone_msg_id' in context.user_data:
        await safe_delete_user_msg(context, update.effective_chat.id, context.user_data['phone_msg_id'])
    
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text
    context.user_data['phone'] = phone
    lang = context.user_data.get('lang', 'ua')
    txt = LANGUAGES[lang]

    if ADMIN_CHAT_ID:
        user = update.effective_user
        order_msg = (
            f"📥 **НОВАЯ ЗАЯВКА НА ТРАНСФЕР!**\n\n"
            f"👤 **Пассажир:** {escape_markdown(user.full_name)} (@{escape_markdown(user.username or 'нет')})\n"
            f"📞 **Телефон:** `{escape_markdown(phone)}`\n"
            f"🚘 **Тип поездки:** {escape_markdown(context.user_data.get('transfer_type', 'Не указан'))}\n"
            f"🛣 **Маршрут:** {escape_markdown(context.user_data.get('route', 'Не указан'))}\n"
            f"📅 **Дата:** {escape_markdown(context.user_data.get('date', 'Не указана'))}\n"
            f"⏰ **Время:** {escape_markdown(context.user_data.get('time', 'Не указано'))}\n"
            f"👥 **Пассажиры:** {escape_markdown(context.user_data.get('passengers', 'Не указано'))}\n"
            f"🧳 **Багаж:** {escape_markdown(context.user_data.get('luggage', 'Не указан'))}\n"
            f"📍 **Место посадки:** {escape_markdown(context.user_data.get('pickup', 'Не указано'))}\n"
            f"🏁 **Место высадки:** {escape_markdown(context.user_data.get('dropoff', 'Не указано'))}\n"
            f"💬 **Предпочтительный канал:** {escape_markdown(context.user_data.get('comm_channel', 'Не указан'))}"
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
    
    summary_text = build_summary_text(context.user_data, lang)

    if card_msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=card_msg_id,
                text=summary_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error updating card message: {e}")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=txt['success'],
        reply_markup=ReplyKeyboardRemove()
    )

# Роут веб-сервера для Render
@app.route('/')
def index():
    return "Bot is alive!", 200

def run_flask():
    """Фоновый запуск веб-сервера Flask"""
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def main():
    """Главная точка входа"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN variable is missing!")
        return

    # Запуск Flask в фоновом потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    tg_app = Application.builder().token(BOT_TOKEN).build()

    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(CallbackQueryHandler(handle_callback))
    tg_app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logger.info("Bot starting polling...")
    tg_app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
