import asyncio
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
ADMIN_ID = int(os.getenv("ADMIN_ID", "ВАШ_ID_ЗДЕСЬ"))
ORDERS_FILE = "orders.json"

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# ================= FSM =================
class OrderFSM(StatesGroup):
    describe_task = State()

class AdminReplyFSM(StatesGroup):
    reply_text = State()

# ================= КЛАВИАТУРЫ =================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🤖 Услуги"), KeyboardButton(text="❓ Задать вопрос")]
    ],
    resize_keyboard=True
)

services_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💼 Бот для бизнеса", callback_data="service_business")],
    [InlineKeyboardButton(text="🛒 Бот для продаж", callback_data="service_sales")],
    [InlineKeyboardButton(text="📦 Бот для заявок", callback_data="service_leads")],
    [InlineKeyboardButton(text="🧠 AI-бот", callback_data="service_ai")],
    [InlineKeyboardButton(text="🛠 Поддержка и доработка", callback_data="service_support")]
])

QUESTIONS_MAP = {
    "q_price": "интересует стоимость",
    "q_deadline": "интересует сроки реализации",
    "q_features": "интересуют возможности бота",
    "q_support": "интересует поддержка после запуска",
    "q_crm": "интересует интеграция с CRM",
    "q_ai": "интересует AI-функционал",
    "q_notify": "интересует настройка уведомлений",
    "q_security": "интересует безопасность данных",
    "q_mobile": "интересует мобильная версия",
    "q_custom": "интересует индивидуальная разработка"
}

questions_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Стоимость проекта", callback_data="q_price")],
    [InlineKeyboardButton(text="⏰ Сроки реализации", callback_data="q_deadline")],
    [InlineKeyboardButton(text="🛠 Возможности бота", callback_data="q_features")],
    [InlineKeyboardButton(text="🛡 Поддержка после запуска", callback_data="q_support")],
    [InlineKeyboardButton(text="🔗 Интеграции с CRM", callback_data="q_crm")],
    [InlineKeyboardButton(text="🤖 AI-функционал", callback_data="q_ai")],
    [InlineKeyboardButton(text="🔔 Уведомления", callback_data="q_notify")],
    [InlineKeyboardButton(text="🔒 Безопасность", callback_data="q_security")],
    [InlineKeyboardButton(text="📱 Мобильность", callback_data="q_mobile")],
    [InlineKeyboardButton(text="⚙️ Индивидуально", callback_data="q_custom")]
])

# ================= HELPERS =================
def save_order(order: dict):
    if not os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    data.append(order)
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def admin_reply_kb(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Спасибо", callback_data=f"tpl_ok_{user_id}"),
            InlineKeyboardButton(text="✏️ Уточнить", callback_data=f"tpl_more_{user_id}")
        ],
        [
            InlineKeyboardButton(text="✍ Ответить вручную", callback_data=f"manual_{user_id}")
        ]
    ])

def admin_reply_question_kb(user_id: int, q_key: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ответить", callback_data=f"answer_{user_id}_{q_key}")]
    ])

# ================= HANDLERS =================
@dp.message(Command(commands=["start"]))
async def start(message: Message):
    await message.answer(
        "👋 <b>Добро пожаловать</b>\n\nЯ помогу подобрать лучшее решение под вашу задачу.",
        reply_markup=main_menu
    )

@dp.message(Text(equals="🤖 Услуги"))
async def show_services(message: Message):
    await message.answer("Выберите услугу 👇", reply_markup=services_kb)

@dp.callback_query(Text(startswith="service_"))
async def service_clicked(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    service = callback.data.replace("service_", "")
    await state.set_state(OrderFSM.describe_task)
    await state.update_data(service=service)
    await callback.message.answer(
        "Мы уже знаем, что вам предложить 👍\nОпишите задачу одним сообщением."
    )

@dp.message(OrderFSM.describe_task)
async def get_task(message: Message, state: FSMContext):
    data = await state.get_data()
    order = {
        "date": datetime.now().isoformat(),
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "service": data["service"],
        "message": message.text
    }
    save_order(order)
    await bot.send_message(
        ADMIN_ID,
        f"📩 <b>Новая заявка</b>\n\n👤 @{order['username']} ({order['user_id']})\n"
        f"🛠 Услуга: {order['service']}\n\n📌 {order['message']}",
        reply_markup=admin_reply_kb(order["user_id"])
    )
    await message.answer("✅ Заявка отправлена специалисту", reply_markup=main_menu)
    await state.clear()

@dp.message(Text(equals="❓ Задать вопрос"))
async def ask_question(message: Message):
    await message.answer("Выберите вопрос 👇", reply_markup=questions_kb)

@dp.callback_query(Text(startswith="q_"))
async def question_sent(callback: CallbackQuery):
    await callback.answer()
    q_text = QUESTIONS_MAP.get(callback.data, callback.data)
    await bot.send_message(
        ADMIN_ID,
        f"❓ Вопрос от @{callback.from_user.username} ({callback.from_user.id})\nТема: {q_text}",
        reply_markup=admin_reply_question_kb(callback.from_user.id, callback.data)
    )
    await callback.message.answer("Вопрос отправлен 👌", reply_markup=main_menu)

@dp.callback_query(Text(startswith="tpl_"))
async def admin_template(callback: CallbackQuery):
    await callback.answer()
    _, _, user_id = callback.data.split("_")
    await bot.send_message(int(user_id), "Спасибо за обращение! Мы скоро свяжемся с вами.")
    await callback.message.answer("Ответ отправлен ✅")

@dp.callback_query(Text(startswith="manual_"))
async def admin_manual(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = int(callback.data.split("_")[1])
    await state.set_state(AdminReplyFSM.reply_text)
    await state.update_data(user_id=user_id)
    await callback.message.answer("Введите ответ клиенту:")

@dp.message(AdminReplyFSM.reply_text)
async def send_manual(message: Message, state: FSMContext):
    data = await state.get_data()
    await bot.send_message(data["user_id"], message.text)
    await message.answer("Ответ отправлен ✅")
    await state.clear()

@dp.callback_query(Text(startswith="answer_"))
async def admin_reply_question(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_", 2)
    user_id = int(parts[1])
    q_key = parts[2]
    q_text = QUESTIONS_MAP.get(q_key, q_key)
    await state.set_state(AdminReplyFSM.reply_text)
    await state.update_data(user_id=user_id, question=q_text)
    await callback.message.answer(f"Введите ответ на вопрос: «{q_text}»")

# ================= RUN =================
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
