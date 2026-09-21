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
from telegram_bot_calendar import DetailedTelegramCalendar

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
MANAGER_CONTACT = "@ALKUNTR"

CALENDAR_LANGS = {
    'ua': 'uk',
    'pl': 'pl',
    'en': 'en',
    'ru': 'ru'
}

def escape_markdown(text) -> str:
    if text is None or text == "":
        return "-"
    text_str = str(text)
    # Исправлено безопасное экранирование Markdown V1
    for char in ['_', '*', '`', '[', ']', '(', ')']:
        text_str = text_str.replace(char, f'\\{char}')
    return text_str

LANGUAGES = {
    'ua': {
        'select_type': "🚖 Оберіть тип трансферу:",
        'types': ["🚗 Індивідуальний", "👥 Груповий (попутники)"],
        'enter_pickup': "📍 Напишіть **адресу або місце ВІДПРАВЛЕННЯ** (місто, вулиця, вокзал тощо):",
        'enter_dropoff': "🏁 Напишіть **адресу або місце ПРИБУТТЯ**:",
        'select_date': "📅 Оберіть **дату поїздки**:",
        'select_hour': "⏰ Оберіть **годину відправлення**:",
        'select_minute': "⏱ Оберіть **хвилини**:",
        'btn_custom_time': "✏️ Ввести дату та час текстом",
        'enter_datetime_custom': "Введіть дату та час у чат (наприклад, 25.10 о 14:30):",
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
        'field_transfer_type': "Тип трансферу:",
        'field_pickup': "Відправлення:",
        'field_dropoff': "Прибуття:",
        'field_datetime': "Дата та час:",
        'field_passengers': "Пасажири:",
        'field_children': "Діти:",
        'field_luggage': "Багаж:",
        'field_details': "Деталі поїздки:",
        'field_phone': "Телефон:",
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
        'select_date': "📅 Wybierz **datę przejazdu**:",
        'select_hour': "⏰ Wybierz **godzinę odjazdu**:",
        'select_minute': "⏱ Wybierz **minuty**:",
        'btn_custom_time': "✏️ Wpisz datę i godzinę na czacie",
        'enter_datetime_custom': "Wpisz datę i godzinę na czacie (np. 25.10 o 14:30):",
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
        'field_transfer_type': "Typ transferu:",
        'field_pickup': "Miejsce odbioru:",
        'field_dropoff': "Miejsce dojazdu:",
        'field_datetime': "Data i godzina:",
        'field_passengers': "Pasażerowie:",
        'field_children': "Dzieci:",
        'field_luggage': "Bagaż:",
        'field_details': "Szczegóły przejazdu:",
        'field_phone': "Telefon:",
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
        'select_date': "📅 Select **trip date**:",
        'select_hour': "⏰ Select **departure hour**:",
        'select_minute': "⏱ Select **minutes**:",
        'btn_custom_time': "✏️ Type date & time manually",
        'enter_datetime_custom': "Type date and time in chat (e.g., 25.10 at 14:30):",
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
        'field_transfer_type': "Transfer type:",
        'field_pickup': "Pick-up:",
        'field_dropoff': "Drop-off:",
        'field_datetime': "Date and time:",
        'field_passengers': "Passengers:",
        'field_children': "Children:",
        'field_luggage': "Luggage:",
        'field_details': "Trip details:",
        'field_phone': "Phone:",
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
        'select_date': "📅 Выберите **дату поездки**:",
        'select_hour': "⏰ Выберите **час отправления**:",
        'select_minute': "⏱ Выберите **минуты**:",
        'btn_custom_time': "✏️ Ввести дату и время текстом",
        'enter_datetime_custom': "Введите дату и время в чат (например, 25.10 в 14:30):",
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
        'field_transfer_type': "Тип трансфера:",
        'field_pickup': "Отправление:",
        'field_dropoff': "Прибытие:",
        'field_datetime': "Дата и время:",
        'field_passengers': "Пассажиры:",
        'field_children': "Дети:",
        'field_luggage': "Багаж:",
        'field_details': "Детали поездки:",
        'field_phone': "Телефон:",
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
        f"🚘 **{txt['field_transfer_type']}** {escape_markdown(context_data.get('transfer_type'))}\n"
        f"📍 **{txt['field_pickup']}** {escape_markdown(context_data.get('pickup'))}\n"
        f"🏁 **{txt['field_dropoff']}** {escape_markdown(context_data.get('dropoff'))}\n"
        f"📅 **{txt['field_datetime']}** {escape_markdown(context_data.get('datetime'))}\n"
        f"👥 **{txt['field_passengers']}** {escape_markdown(context_data.get('passengers'))}\n"
        f"👶 **{txt['field_children']}** {escape_markdown(context_data.get('children'))}\n"
        f"🧳 **{txt['field_luggage']}** {escape_markdown(context_data.get('luggage'))}\n"
        f"📝 **{txt['field_details']}** {escape_markdown(context_data.get('details', '-'))}\n"
        f"📞 **{txt['field_phone']}** `{escape_markdown(context_data.get('phone'))}`\n\n"
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
    chat_id = update.effective_chat.id
    
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
        msg = await update.callback_query.edit_message_text(text=text, reply_markup=markup)
        context.user_data['card_msg_id'] = msg.message_id
    else:
        msg = await update.message.reply_text(text=text, reply_markup=markup)
        context.user_data['card_msg_id'] = msg.message_id

async def render_step(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ua')
    txt = LANGUAGES[lang]
    step = context.user_data.get('step', 'transfer_type')
    card_msg_id = context.user_data.get('card_msg_id')

    if not card_msg_id:
        return

    keyboard = []

    if step == 'transfer_type':
        text = txt['select_type']
        for t in txt['types']:
            keyboard.append([InlineKeyboardButton(t, callback_data=t)])
        keyboard.append(get_nav_buttons(lang, show_back=False))

    elif step == 'pickup':
        text = txt['enter_pickup']
        keyboard.append(get_nav_buttons(lang))

    elif step == 'dropoff':
        text = txt['enter_dropoff']
        keyboard.append(get_nav_buttons(lang))

    elif step == 'datetime':
        cal_lang = CALENDAR_LANGS.get(lang, 'en')
        calendar, step_type = DetailedTelegramCalendar(calendar_id=1, locale=cal_lang).build()
        text = txt['select_date']
        keyboard = calendar.inline_keyboard + [[InlineKeyboardButton(txt['btn_custom_time'], callback_data="custom_datetime")]] + [get_nav_buttons(lang)]

    elif step == 'time_hour':
        text = f"📅 **{context.user_data.get('selected_date', '')}**\n\n{txt['select_hour']}"
        for h_row in [range(0, 6), range(6, 12), range(12, 18), range(18, 24)]:
            keyboard.append([InlineKeyboardButton(f"{h:02d}", callback_data=f"hour_{h:02d}") for h in h_row])
        keyboard.append([InlineKeyboardButton(txt['btn_custom_time'], callback_data="custom_datetime")])
        keyboard.append(get_nav_buttons(lang))

    elif step == 'time_minute':
        text = f"📅 **{context.user_data.get('selected_date', '')}** ⏰ **{context.user_data.get('temp_hour', '')}:XX**\n\n{txt['select_minute']}"
        keyboard.append([
            InlineKeyboardButton("00", callback_data="min_00"),
            InlineKeyboardButton("15", callback_data="min_15"),
            InlineKeyboardButton("30", callback_data="min_30"),
            InlineKeyboardButton("45", callback_data="min_45")
        ])
        keyboard.append([InlineKeyboardButton(txt['btn_custom_time'], callback_data="custom_datetime")])
        keyboard.append(get_nav_buttons(lang))

    elif step == 'passengers':
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
        text = txt['ask_children']
        keyboard.append([InlineKeyboardButton(txt['btn_yes_children'], callback_data="has_children"),
                         InlineKeyboardButton(txt['btn_no_children'], callback_data="no_children")])
        keyboard.append(get_nav_buttons(lang))

    elif step == 'luggage':
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
        keyboard.append([InlineKeyboardButton(txt['btn_skip_details'], callback_data="skip_details")])
        keyboard.append(get_nav_buttons(lang))

    elif step == 'phone':
        text = txt['share_phone']
        keyboard.append(get_nav_buttons(lang))
        markup = InlineKeyboardMarkup(keyboard)
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=card_msg_id, text=text, reply_markup=markup, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error editing phone step card: {e}")

        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton(txt['btn_phone'], request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        msg = await context.bot.send_message(chat_id=chat_id, text=txt['share_phone'], reply_markup=reply_markup)
        context.user_data['phone_msg_id'] = msg.message_id
        return

    markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=card_msg_id,
            text=text,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Render step error: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = update.effective_chat.id
    lang = context.user_data.get('lang', 'ua')

    if data == "nav_restart":
        await start_command(update, context)
        return

    if data.startswith("lang_"):
        lang = data.split("_")[1]
        context.user_data['lang'] = lang
        context.user_data['step'] = 'transfer_type'
        await render_step(chat_id, context)
        return

    if data.startswith("cbcal_"):
        cal_lang = CALENDAR_LANGS.get(lang, 'en')
        result, key, step_type = DetailedTelegramCalendar(calendar_id=1, locale=cal_lang).process(data)
        if not result and key:
            txt = LANGUAGES[lang]
            await query.edit_message_text(
                txt['select_date'],
                reply_markup=InlineKeyboardMarkup(key.inline_keyboard + [get_nav_buttons(lang)]),
                parse_mode='Markdown'
            )
            return
        elif result:
            context.user_data['selected_date'] = result.strftime("%d.%m.%Y")
            context.user_data['step'] = 'time_hour'
            await render_step(chat_id, context)
            return

    if data == "nav_back":
        step = context.user_data.get('step')
        steps_order = ['transfer_type', 'pickup', 'dropoff', 'datetime', 'passengers', 'children', 'luggage', 'details', 'phone']
        if step in ['time_hour', 'time_minute', 'custom_datetime']:
            context.user_data['step'] = 'datetime'
        elif step in ['custom_passengers']:
            context.user_data['step'] = 'passengers'
        elif step in ['custom_children']:
            context.user_data['step'] = 'children'
        elif step in ['custom_luggage']:
            context.user_data['step'] = 'luggage'
        elif step in steps_order:
            idx = steps_order.index(step)
            if idx > 0:
                context.user_data['step'] = steps_order[idx - 1]
            else:
                await start_command(update, context)
                return
        await render_step(chat_id, context)
        return

    step = context.user_data.get('step')

    if step == 'transfer_type':
        context.user_data['transfer_type'] = data
        context.user_data['step'] = 'pickup'
    elif step == 'datetime' and data == "custom_datetime":
        context.user_data['step'] = 'custom_datetime'
        txt = LANGUAGES[lang]
        markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
        await query.edit_message_text(txt['enter_datetime_custom'], reply_markup=markup)
        return
    elif step == 'time_hour':
        if data.startswith("hour_"):
            hour = data.split("_")[1]
            context.user_data['temp_hour'] = hour
            context.user_data['step'] = 'time_minute'
        elif data == "custom_datetime":
            context.user_data['step'] = 'custom_datetime'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_datetime_custom'], reply_markup=markup)
            return
    elif step == 'time_minute':
        if data.startswith("min_"):
            minute = data.split("_")[1]
            full_dt = f"{context.user_data['selected_date']} {context.user_data['temp_hour']}:{minute}"
            context.user_data['datetime'] = full_dt
            context.user_data['step'] = 'passengers'
        elif data == "custom_datetime":
            context.user_data['step'] = 'custom_datetime'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_datetime_custom'], reply_markup=markup)
            return
    elif step == 'passengers':
        if data == "custom_passengers":
            context.user_data['step'] = 'custom_passengers'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_passengers_custom'], reply_markup=markup)
            return
        context.user_data['passengers'] = data
        context.user_data['step'] = 'children'
    elif step == 'children':
        if data == "has_children":
            context.user_data['step'] = 'custom_children'
            txt = LANGUAGES[lang]
            markup = InlineKeyboardMarkup([get_nav_buttons(lang)])
            await query.edit_message_text(txt['enter_children_info'], reply_markup=markup)
            return
        elif data == "no_children":
            context.user_data['children'] = "Нет" if lang == 'ru' else ("Ні" if lang == 'ua' else ("Nie" if lang == 'pl' else "No"))
            context.user_data['step'] = 'luggage'
    elif step == 'luggage':
        if data == "custom_luggage":
            context.user_data['step'] = 'custom_luggage'
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

    await render_step(chat_id, context)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await safe_delete_user_msg(context, chat_id, update.message.message_id)
    
    card_msg_id = context.user_data.get('card_msg_id')
    user_text = update.message.text
    
    if not card_msg_id:
        return
        
    step = context.user_data.get('step')
    
    if step == 'pickup':
        context.user_data['pickup'] = user_text
        context.user_data['step'] = 'dropoff'
    elif step == 'dropoff':
        context.user_data['dropoff'] = user_text
        context.user_data['step'] = 'datetime'
    elif step == 'custom_datetime':
        context.user_data['datetime'] = user_text
        context.user_data['step'] = 'passengers'
    elif step == 'custom_passengers':
        context.user_data['passengers'] = user_text
        context.user_data['step'] = 'children'
    elif step == 'custom_children':
        context.user_data['children'] = user_text
        context.user_data['step'] = 'luggage'
    elif step == 'custom_luggage':
        context.user_data['luggage'] = user_text
        context.user_data['step'] = 'details'
    elif step == 'details':
        context.user_data['details'] = user_text
        context.user_data['step'] = 'phone'
    else:
        return

    # Вызов перерисовки карточки после ввода текста
    await render_step(chat_id, context)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await safe_delete_user_msg(context, chat_id, update.message.message_id)
    
    if 'phone_msg_id' in context.user_data:
        await safe_delete_user_msg(context, chat_id, context.user_data['phone_msg_id'])
    
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
                chat_id=chat_id,
                message_id=card_msg_id,
                text=summary_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error updating card message: {e}")

    # Удаляем физическую кнопку отправки контакта
    remove_keyboard_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=txt['success'],
        reply_markup=ReplyKeyboardRemove()
    )
    # Удаляем техническое сообщение об удалении клавиатуры
    await safe_delete_user_msg(context, chat_id, remove_keyboard_msg.message_id)

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
