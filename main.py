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
        'select_type': "🚖 Оберіть тип трансферу:",
        'types': ["🚗 Індивідуальний", "👥 Груповий (попутники)"],
        'enter_pickup': "📍 Напишіть **адресу або місце ВІДПРАВЛЕННЯ** (місто, вулиця, вокзал тощо):",
        'enter_dropoff': "🏁 Напишіть **адресу або місце ПРИБУТТЯ**:",
        'enter_datetime': "📅 Вкажіть **дату та час** поїздки (наприклад, 25.10 о 14:30):",
        'select_passengers': "👥 Вкажіть кількість дорослих пасажирів:",
        'passengers_opts': ["1", "2", "3", "4", "✏️ Свій варіант"],
        'enter_passengers_custom': "Вкажіть кількість пасажирів текстом:",
        'ask_children': "👶 Чи будуть з вами діти?",
        'btn_yes_children': "Так, будуть",
        'btn_no_children': "Ні, без дітей",
        'enter_children_info': "Введіть кількість дітей та їхній вік (наприклад: 2 дитини, 3 и 7 років):",
        'select_luggage': "🧳 Вкажіть кількість багажу:",
        'luggage_opts': ["1", "2", "3", "4", "✏️ Свій варіант"],
        'enter_luggage_custom': "Опишіть ваш багаж текстом:",
        'enter_details': "📝 **Деталі та побажання до поїздки:**\n\nВкажіть додаткові зупинки, Wi-Fi, наявність тварин або інші побажання:",
        'btn_skip_details': "Нічого / Пропустити ➡️",
        'share_phone': "📱 Натисніть кнопку нижче, щоб передати номер телефону:",
        'btn_phone': "📱 Поділитися номером телефону",
        'summary_title': "📋 **Перевірте дані вашої заявки:**",
        'urgent_contact': f"⚡️ У разі терміновості зв'яжіться з менеджером: {escape_markdown(MANAGER_CONTACT)}",
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
        'select_type': "🚖 Wybierz typ transferu:",
        'types': ["🚗 Indywidualny", "👥 Grupowe (współpasażerowie)"],
        'enter_pickup': "📍 Wpisz **adres/miejsce ODBIORU** (miasto, ulica, dworzec itp.):",
        'enter_dropoff': "🏁 Wpisz **adres/miejsce DOJAZDU**:",
        'enter_datetime': "📅 Wpisz **datę i godzinę** przejazdu (np. 25.10 o 14:30):",
        'select_passengers': "👥 Wybierz liczbę dorosłych pasażerów:",
        'passengers_opts': ["1", "2", "3", "4", "✏️ Inna opcja"],
        'enter_passengers_custom': "Wpisz liczbę pasażerów na czacie:",
        'ask_children': "👶 Czy będą z Tobą dzieci?",
        'btn_yes_children': "Tak, będą",
        'btn_no_children': "Nie, bez dzieci",
        'enter_children_info': "Wpisz liczbę dzieci i ich wiek (np. 2 dzieci, 3 i 7 lat):",
        'select_luggage': "🧳 Wybierz ilość bagażu:",
        'luggage_opts': ["1", "2", "3", "4", "✏️ Inna opcja"],
        'enter_luggage_custom': "Opisz swój bagaż na czacie:",
        'enter_details': "📝 **Szczegóły i życzenia dotyczące przejazdu:**\n\nWpisz dodatkowe przystanki, Wi-Fi, zwierzęta itp.:",
        'btn_skip_details': "Brak / Pomiń ➡️",
        'share_phone': "📱 Kliknij przycisk poniżej, aby udostępnić numer:",
        'btn_phone': "📱 Udostępnij numer telefonu",
        'summary_title': "📋 **Sprawdź szczegóły zamówienia:**",
        'urgent_contact': f"⚡️ W pilnych sprawach skontaktuj się z menedżerem: {escape_markdown(MANAGER_CONTACT)}",
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
        'select_type': "🚖 Select transfer type:",
        'types': ["🚗 Private", "👥 Shared"],
        'enter_pickup': "📍 Type your **PICK-UP location/address** (city, street, station, etc.):",
        'enter_dropoff': "🏁 Type your **DROP-OFF location/address**:",
        'enter_datetime': "📅 Type the **date and time** of your trip (e.g., 25.10 at 14:30):",
        'select_passengers': "👥 Select number of adult passengers:",
        'passengers_opts': ["1", "2", "3", "4", "✏️ Custom option"],
        'enter_passengers_custom': "Type the number of passengers in chat:",
        'ask_children': "👶 Will there be children travelling with you?",
        'btn_yes_children': "Yes, with children",
        'btn_no_children': "No children",
        'enter_children_info': "Please enter the number of children and their ages (e.g., 2 kids, 3 & 7 y.o.):",
        'select_luggage': "🧳 Select luggage amount:",
        'luggage_opts': ["1", "2", "3", "4", "✏️ Custom option"],
        'enter_luggage_custom': "Describe your luggage in chat:",
        'enter_details': "📝 **Trip details & special requests:**\n\nSpecify extra stops, Wi-Fi, pets, or other notes:",
        'btn_skip_details': "None / Skip ➡️",
        'share_phone': "📱 Press the button below to share your phone number:",
        'btn_phone': "📱 Share phone number",
        'summary_title': "📋 **Please review your booking:**",
        'urgent_contact': f"⚡️ In case of urgency, contact the manager: {escape_markdown(MANAGER_CONTACT)}",
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
        'select_type': "🚖 Выберите тип трансфера:",
        'types': ["🚗 Индивидуальный", "👥 Групповой (попутчики)"],
        'enter_pickup': "📍 Напишите **адрес или место ОТПРАВЛЕНИЯ** (город, улица, вокзал и т.д.):",
        'enter_dropoff': "🏁 Напишите **адрес или место НАЗНАЧЕНИЯ**:",
        'enter_datetime': "📅 Напишите **дату и время** поездки (например, 25.10 в 14:30):",
        'select_passengers': "👥 Укажите количество взрослых пассажиров:",
        'passengers_opts': ["1", "2", "3", "4", "✏️ Свой вариант"],
        'enter_passengers_custom': "Введите количество пассажиров в чат:",
        'ask_children': "👶 Будут ли с вами дети?",
        'btn_yes_children': "Да, будут",
        'btn_no_children': "Нет, без детей",
        'enter_children_info': "Введите количество детей и их возраст (например: 2 ребенка, 3 и 7 лет):",
        'select_luggage': "🧳 Укажите количество багажа:",
        'luggage_opts': ["1", "2", "3", "4", "✏️ Свой вариант"],
        'enter_luggage_custom': "Опишите ваш багаж в чат:",
        'enter_details': "📝 **Детали поездки и пожелания:**\n\nУкажите дополнительные точки, Wi-Fi, животных или другие заметки:",
        'btn_skip_details': "Нет / Пропустить ➡️",
        'share_phone': "📱 Нажмите кнопку внизу, чтобы передать номер телефона:",
        'btn_phone': "📱 Поделиться номером телефона",
        'summary_title': "📋 **Проверьте данные вашей заявки:**",
        'urgent_contact': f"⚡️ В случае срочности свяжитесь с менеджером: {escape_markdown(MANAGER_CONTACT)}",
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
        f"🚘 **Тип трансфера:** {escape_markdown(context_data.get('transfer_type'))}\n"
        f"📍 **Отправление:** {escape_markdown(context_data.get('pickup'))}\n"
        f"🏁 **Прибытие:** {escape_markdown(context_data.get('dropoff'))}\n"
        f"📅 **Дата и время:** {escape_markdown(context_data.get('datetime'))}\n"
        f"👥 **Пассажиры:** {escape_markdown(context_data.get('passengers'))}\n"
        f"👶 **Дети:** {escape_markdown(context_data.get('children'))}\n"
        f"🧳 **Багаж:** {escape_markdown(context_data.get('luggage'))}\n"
        f"📝 **Детали поездки:** {escape_markdown(context_data.get('details', '-'))}\n"
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
        context.user_data['step'] = 'transfer_type'
        await render_step(query, context)
        return

    lang = context.user_data.get('lang', 'ua')

    if data == "nav_back":
        step = context.user_data.get('step')
        steps_order = ['transfer_type', 'pickup', 'dropoff', 'datetime', 'passengers', 'children', 'luggage', 'details', 'phone']
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

    if step == 'transfer_type':
        context.user_data['transfer_type'] = data
        context.user_data['step'] = 'pickup'
    elif step == 'passengers':
        if data == "custom_passengers":
            context.user_data['awaiting_text'] = 'passengers'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_passengers_custom'], reply_markup=markup)
            return
        context.user_data['passengers'] = data
        context.user_data['step'] = 'children'
    elif step == 'children':
        if data == "has_children":
            context.user_data['awaiting_text'] = 'children'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_children_info'], reply_markup=markup)
            return
        elif data == "no_children":
            context.user_data['children'] = "Нет" if lang == 'ru' else ("Ні" if lang == 'ua' else "No")
            context.user_data['step'] = 'luggage'
    elif step == 'luggage':
        if data == "custom_luggage":
            context.user_data['awaiting_text'] = 'luggage'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_luggage_custom'], reply_markup=markup)
            return
        context.user_data['luggage'] = data
        context.user_data['step'] = 'details'
    elif step == 'details':
        if data == "skip_details":
            context.user_data['details'] = "-"
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
                f"📍 Посадка: {escape_markdown(context.user_data.get('pickup'))}\n"
                f"🏁 Высадка: {escape_markdown(context.user_data.get('dropoff'))}\n"
                f"📞 Телефон: `{escape_markdown(context.user_data.get('phone'))}`"
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
    step = context.user_data.get('step', 'transfer_type')
    
    keyboard = []
    
    if step == 'transfer_type':
        context.user_data['awaiting_text'] = None
        text = txt['select_type']
        for t in txt['types']:
            keyboard.append([InlineKeyboardButton(t, callback_data=t)])
        keyboard.append(get_nav_buttons(lang, show_back=False))

    elif step == 'pickup':
        text = txt['enter_pickup']
        context.user_data['awaiting_text'] = 'pickup'
        keyboard.append(get_nav_buttons(lang))

    elif step == 'dropoff':
        text = txt['enter_dropoff']
        context.user_data['awaiting_text'] = 'dropoff'
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'datetime':
        text = txt['enter_datetime']
        context.user_data['awaiting_text'] = 'datetime'
        keyboard.append(get_nav_buttons(lang))
        
    elif step == 'passengers':
        context.user_data['awaiting_text'] = None
        text = txt['select_passengers']
        opts = txt['passengers_opts']
        keyboard.append([
            InlineKeyboardButton(opts[0], callback_data=opts[0]),
            InlineKeyboardButton(opts[1], callback_data=opts[1]),
            InlineKeyboardButton(opts[2], callback_data=opts[2]),
            InlineKeyboardButton(opts[3], callback_data=opts[3])
        ])
        keyboard.append([InlineKeyboardButton(opts[4], callback_data="custom_passengers")])
        keyboard.append(get_nav_buttons(lang))

    elif step == 'children':
        context.user_data['awaiting_text'] = None
        text = txt['ask_children']
        keyboard.append([InlineKeyboardButton(txt['btn_yes_children'], callback_data="has_children"),
                         InlineKeyboardButton(txt['btn_no_children'], callback_data="no_children")])
        keyboard.append(get_nav_buttons(lang))

    elif step == 'luggage':
        context.user_data['awaiting_text'] = None
        text = txt['select_luggage']
        opts = txt['luggage_opts']
        keyboard.append([
            InlineKeyboardButton(opts[0], callback_data=opts[0]),
            InlineKeyboardButton(opts[1], callback_data=opts[1]),
            InlineKeyboardButton(opts[2], callback_data=opts[2]),
            InlineKeyboardButton(opts[3], callback_data=opts[3])
        ])
        keyboard.append([InlineKeyboardButton(opts[4], callback_data="custom_luggage")])
        keyboard.append(get_nav_buttons(lang))

    elif step == 'details':
        text = txt['enter_details']
        context.user_data['awaiting_text'] = 'details'
        keyboard.append([InlineKeyboardButton(txt['btn_skip_details'], callback_data="skip_details")])
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
    await query_or_dummy.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_delete_user_msg(context, update.effective_chat.id, update.message.message_id)
    
    awaiting = context.user_data.get('awaiting_text')
    card_msg_id = context.user_data.get('card_msg_id')
    user_text = update.message.text
    context.user_data['chat_id'] = update.effective_chat.id
    
    if not awaiting or not card_msg_id:
        return
        
    if awaiting == 'pickup':
        context.user_data['pickup'] = user_text
        context.user_data['step'] = 'dropoff'
    elif awaiting == 'dropoff':
        context.user_data['dropoff'] = user_text
        context.user_data['step'] = 'datetime'
    elif awaiting == 'datetime':
        context.user_data['datetime'] = user_text
        context.user_data['step'] = 'passengers'
    elif awaiting == 'passengers':
        context.user_data['passengers'] = user_text
        context.user_data['step'] = 'children'
    elif awaiting == 'children':
        context.user_data['children'] = user_text
        context.user_data['step'] = 'luggage'
    elif awaiting == 'luggage':
        context.user_data['luggage'] = user_text
        context.user_data['step'] = 'details'
    elif awaiting == 'details':
        context.user_data['details'] = user_text
        context.user_data['step'] = 'phone'
        
    class DummyQuery:
        def __init__(self, chat_id, msg_id):
            self.chat_id = chat_id
            self.message_id = msg_id
        async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
            await context.bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=self.message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
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
            f"🚘 **Тип трансфера:** {escape_markdown(context.user_data.get('transfer_type'))}\n"
            f"📍 **Место посадки:** {escape_markdown(context.user_data.get('pickup'))}\n"
            f"🏁 **Место высадки:** {escape_markdown(context.user_data.get('dropoff'))}\n"
            f"📅 **Дата и время:** {escape_markdown(context.user_data.get('datetime'))}\n"
            f"👥 **Взрослые пассажиры:** {escape_markdown(context.user_data.get('passengers'))}\n"
            f"👶 **Дети:** {escape_markdown(context.user_data.get('children'))}\n"
            f"🧳 **Багаж:** {escape_markdown(context.user_data.get('luggage'))}\n"
            f"📝 **Детали поездки:** {escape_markdown(context.user_data.get('details', '-'))}"
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

@app.route('/')
def index():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN variable is missing!")
        return

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
