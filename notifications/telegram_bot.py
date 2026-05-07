"""
Telegram bot for AutoService Pro.
Beautiful UI with images, inline keyboards, and formatted messages.
Run via: python manage.py run_telegram_bot
"""
import logging
import os
import re

from asgiref.sync import sync_to_async
from django.conf import settings
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)

logger = logging.getLogger(__name__)

IMG_DIR = os.path.join(settings.BASE_DIR, 'static', 'img')
WELCOME_IMG = os.path.join(IMG_DIR, 'bot_welcome.png')
BANNER_IMG = os.path.join(IMG_DIR, 'bot_banner.png')

LINE = '\u2500' * 24


# ─── DB helpers ───────────────────────────────────────────────

@sync_to_async
def find_client_by_phone(phone):
    from clients.models import Client
    phone = re.sub(r'[^\d+]', '', phone)
    if phone.startswith('8') and len(phone) == 11:
        phone = '+7' + phone[1:]
    elif not phone.startswith('+'):
        phone = '+' + phone
    try:
        return Client.objects.get(phone=phone, is_active=True)
    except Client.DoesNotExist:
        return None


@sync_to_async
def find_client_by_chat_id(chat_id):
    from clients.models import Client
    try:
        return Client.objects.get(telegram_chat_id=chat_id, is_active=True)
    except Client.DoesNotExist:
        return None


@sync_to_async
def link_client_telegram(client, chat_id):
    client.telegram_chat_id = chat_id
    prefs = client.notification_preferences or {}
    prefs['telegram'] = True
    client.notification_preferences = prefs
    client.save(update_fields=['telegram_chat_id', 'notification_preferences'])


@sync_to_async
def get_active_orders(client):
    return list(
        client.orders
        .filter(status__in=['new', 'diagnostics', 'approved', 'in_progress',
                            'waiting_parts', 'completed', 'ready'])
        .select_related('vehicle').order_by('-created_at')
    )


@sync_to_async
def get_recent_orders(client, limit=5):
    return list(
        client.orders
        .filter(status__in=['delivered', 'cancelled'])
        .select_related('vehicle').order_by('-created_at')[:limit]
    )


@sync_to_async
def get_order_detail(order_id):
    from orders.models import WorkOrder
    try:
        return WorkOrder.objects.select_related('client', 'vehicle').get(pk=order_id)
    except WorkOrder.DoesNotExist:
        return None


@sync_to_async
def get_client_name(client):
    return client.get_full_name()


# ─── Visual helpers ───────────────────────────────────────────

STATUS_EMOJI = {
    'new': '\U0001f195', 'diagnostics': '\U0001f50d', 'approved': '\u2705',
    'in_progress': '\U0001f527', 'waiting_parts': '\u23f3',
    'completed': '\u2714\ufe0f', 'ready': '\U0001f3c1',
    'delivered': '\U0001f91d', 'cancelled': '\u274c',
}

PROGRESS = {
    'new':           '\u25c9\u25cb\u25cb\u25cb\u25cb\u25cb',
    'diagnostics':   '\u25c9\u25c9\u25cb\u25cb\u25cb\u25cb',
    'approved':      '\u25c9\u25c9\u25c9\u25cb\u25cb\u25cb',
    'in_progress':   '\u25c9\u25c9\u25c9\u25c9\u25cb\u25cb',
    'waiting_parts': '\u25c9\u25c9\u25c9\u25c9\u25cb\u25cb',
    'completed':     '\u25c9\u25c9\u25c9\u25c9\u25c9\u25cb',
    'ready':         '\u25c9\u25c9\u25c9\u25c9\u25c9\u25c9',
    'delivered':     '\u25c9\u25c9\u25c9\u25c9\u25c9\u25c9',
    'cancelled':     '\u25cb\u25cb\u25cb\u25cb\u25cb\u25cb',
}


async def send_photo_safe(message, photo_path, caption, **kwargs):
    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as f:
            await message.reply_photo(photo=f, caption=caption, parse_mode='HTML', **kwargs)
    else:
        await message.reply_text(caption, parse_mode='HTML', **kwargs)


def order_card(o):
    e = STATUS_EMOJI.get(o.status, '\U0001f4cb')
    p = PROGRESS.get(o.status, '')
    cost = f'\U0001f4b0 {o.final_cost:,.0f} \u20bd\n' if o.final_cost else ''
    return (
        f'{e} <b>\u2116{o.order_number}</b>\n'
        f'\U0001f697 {o.vehicle.make} {o.vehicle.model} \u2022 {o.vehicle.license_plate}\n'
        f'\U0001f4ca {o.get_status_display()}  {p}\n'
        f'{cost}'
    )


# ─── /start ───────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton('\U0001f4f1 Отправить номер телефона', request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    caption = (
        f'\U0001f3ce <b>AutoService Pro</b>\n{LINE}\n\n'
        '\U0001f44b <b>Добро пожаловать!</b>\n\n'
        'Я \u2014 бот автосервиса. Помогу\n'
        'отслеживать ремонт вашего авто.\n\n'
        '\U0001f4a1 <b>Что я умею:</b>\n'
        '\u2022 \U0001f4cb Статус заказов онлайн\n'
        '\u2022 \U0001f514 Push-уведомления\n'
        '\u2022 \U0001f4b0 Стоимость работ\n'
        '\u2022 \U0001f4dc История ремонтов\n\n'
        f'{LINE}\n'
        '\U0001f447 <b>Нажмите кнопку для привязки аккаунта</b>'
    )
    await send_photo_safe(update.message, WELCOME_IMG, caption, reply_markup=kb)


# ─── Contact ──────────────────────────────────────────────────

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number
    chat_id = update.effective_chat.id
    client = await find_client_by_phone(phone)

    if client:
        await link_client_telegram(client, chat_id)
        name = await get_client_name(client)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton('\U0001f4cb Мои заказы', callback_data='go_status')],
            [InlineKeyboardButton('\u2753 Помощь', callback_data='go_help')],
        ])
        await update.message.reply_text(
            f'\u2705 <b>Аккаунт привязан!</b>\n{LINE}\n\n'
            f'\U0001f464 {name}\n\n'
            'Теперь вы будете получать уведомления\n'
            'о статусе ваших заказов.\n\n'
            f'{LINE}\n\U0001f447 <b>Выберите действие:</b>',
            parse_mode='HTML', reply_markup=kb,
        )
        await update.message.reply_text('\u200b', reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text(
            f'\u274c <b>Клиент не найден</b>\n{LINE}\n\n'
            'Номер не зарегистрирован в системе.\n\n'
            '\U0001f4de Позвоните нам:\n<b>+7 (000) 123-45-67</b>\n\n'
            '\U0001f4cd г. Москва, ул. Примерная, д. 1',
            parse_mode='HTML', reply_markup=ReplyKeyboardRemove(),
        )


# ─── /status ──────────────────────────────────────────────────

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    chat_id = update.effective_chat.id
    client = await find_client_by_chat_id(chat_id)

    if not client:
        await msg.reply_text(
            '\u26a0\ufe0f <b>Аккаунт не привязан</b>\n\nОтправьте /start',
            parse_mode='HTML')
        return

    orders = await get_active_orders(client)
    name = await get_client_name(client)

    if not orders:
        await msg.reply_text(
            f'\U0001f4cb <b>Заказы \u2014 {name}</b>\n{LINE}\n\n'
            '\U0001f389 Нет активных заказов!\nВсё выполнено. Хорошего дня!',
            parse_mode='HTML')
        return

    text = f'\U0001f4cb <b>Активные заказы</b>\n{LINE}\n\n'
    buttons = []
    for o in orders:
        text += order_card(o) + '\n'
        buttons.append([InlineKeyboardButton(
            f'\U0001f50e {o.order_number}', callback_data=f'detail_{o.pk}')])

    buttons.append([InlineKeyboardButton('\U0001f504 Обновить', callback_data='go_status')])
    await msg.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))


# ─── /history ─────────────────────────────────────────────────

async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    client = await find_client_by_chat_id(chat_id)

    if not client:
        await update.message.reply_text('\u26a0\ufe0f Не привязан. /start', parse_mode='HTML')
        return

    orders = await get_recent_orders(client)
    if not orders:
        await update.message.reply_text(
            f'\U0001f4dc <b>История</b>\n{LINE}\n\nПусто.',
            parse_mode='HTML')
        return

    text = f'\U0001f4dc <b>История заказов</b>\n{LINE}\n\n'
    buttons = []
    for o in orders:
        text += order_card(o) + '\n'
        buttons.append([InlineKeyboardButton(
            f'\U0001f4cb {o.order_number}', callback_data=f'detail_{o.pk}')])

    await update.message.reply_text(
        text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(buttons))


# ─── Callbacks ────────────────────────────────────────────────

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == 'go_status':
        await cmd_status(update, context)
        return
    if data == 'go_help':
        await q.edit_message_text(help_text(), parse_mode='HTML')
        return

    if data.startswith('detail_'):
        order = await get_order_detail(int(data.split('_')[1]))
        if not order:
            await q.edit_message_text('\u274c Заказ не найден.')
            return

        e = STATUS_EMOJI.get(order.status, '\U0001f4cb')
        p = PROGRESS.get(order.status, '')
        desc = f'\n\U0001f4dd <i>{order.description[:150]}</i>\n' if order.description else ''

        text = (
            f'{e} <b>Заказ \u2116{order.order_number}</b>\n{LINE}\n\n'
            f'\U0001f697 <b>{order.vehicle.make} {order.vehicle.model}</b>\n'
            f'\U0001f4c5 {order.vehicle.year} \u2022 \U0001f3f7 {order.vehicle.license_plate}\n\n'
            f'\U0001f4ca Статус: <b>{order.get_status_display()}</b>\n'
            f'{p}\n\n'
            f'\U0001f4b0 Сумма: <b>{order.final_cost:,.0f} \u20bd</b>\n'
            f'\U0001f4c6 Создан: {order.created_at.strftime("%d.%m.%Y %H:%M")}\n'
            f'{desc}\n{LINE}'
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton('\u2b05 К заказам', callback_data='go_status')],
        ])
        await q.edit_message_text(text, parse_mode='HTML', reply_markup=kb)


# ─── /help ────────────────────────────────────────────────────

def help_text():
    return (
        f'\U0001f527 <b>AutoService Pro</b>\n{LINE}\n\n'
        '\U0001f4ac <b>Команды:</b>\n\n'
        '/start \u2014 \U0001f517 Привязка аккаунта\n'
        '/status \u2014 \U0001f4cb Активные заказы\n'
        '/history \u2014 \U0001f4dc История ремонтов\n'
        '/help \u2014 \u2753 Справка\n\n'
        f'{LINE}\n'
        '\U0001f4de <b>+7 (000) 123-45-67</b>\n'
        '\U0001f55c Пн\u2013Пт 9:00\u201319:00 | Сб 9:00\u201315:00\n'
        '\U0001f4cd г. Москва, ул. Примерная, д. 1'
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton('\U0001f4cb Мои заказы', callback_data='go_status')],
    ])
    await send_photo_safe(update.message, BANNER_IMG, help_text(), reply_markup=kb)


# ─── Unknown ──────────────────────────────────────────────────

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton('\U0001f4cb Заказы', callback_data='go_status'),
         InlineKeyboardButton('\u2753 Помощь', callback_data='go_help')],
    ])
    await update.message.reply_text(
        '\U0001f527 <b>AutoService Pro</b>\n\n'
        'Не понимаю это сообщение.\nВыберите действие:',
        parse_mode='HTML', reply_markup=kb)


# ─── Builder ──────────────────────────────────────────────────

def create_bot_application(token: str) -> Application:
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(CommandHandler('status', cmd_status))
    app.add_handler(CommandHandler('history', cmd_history))
    app.add_handler(CommandHandler('help', cmd_help))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))
    return app
