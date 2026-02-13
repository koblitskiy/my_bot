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
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
ADMIN_ID = int(os.getenv("ADMIN_ID", "ВАШ_ID_ЗДЕСЬ"))
ORDERS_FILE = "orders.json"

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# ================= FSM =================
class LeadFSM(StatesGroup):
    choose_role = State()
    choose_goal = State()
    business_type = State()
    volume = State()
    integrations = State()
    budget = State()
    deadline = State()
    final_comment = State()

class AdminReplyFSM(StatesGroup):
    reply_text = State()

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

# ================= START =================
@dp.message(Command(commands=["start"]))
async def start(message: Message, state: FSMContext):
    await state.set_state(LeadFSM.choose_role)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 У меня бизнес", callback_data="role_business")],
        [InlineKeyboardButton(text="📣 Я агентство", callback_data="role_agency")],
        [InlineKeyboardButton(text="💡 Есть идея", callback_data="role_idea")]
    ])
    await message.answer(
        "Здравствуйте.\n\n"
        "Помогаю бизнесу и агентствам внедрять Telegram-ботов для увеличения заявок и автоматизации процессов.\n\n"
        "Выберите формат работы:",
        reply_markup=kb
    )

# ================= FSM HANDLERS =================

# 1️⃣ Выбор роли
@dp.callback_query(lambda c: c.data.startswith("role_"))
async def choose_role(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    role = callback.data.replace("role_", "")
    await state.update_data(role=role)
    await state.set_state(LeadFSM.choose_goal)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Увеличить заявки", callback_data="goal_leads")],
        [InlineKeyboardButton(text="🤖 Автоматизация", callback_data="goal_auto")],
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="goal_support")],
        [InlineKeyboardButton(text="💰 Приём оплат", callback_data="goal_pay")]
    ])

    await callback.message.answer(
        "Какая основная цель проекта?",
        reply_markup=kb
    )

# 2️⃣ Выбор цели
@dp.callback_query(lambda c: c.data.startswith("goal_"))
async def choose_goal(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    goal = callback.data.replace("goal_", "")
    await state.update_data(goal=goal)
    await state.set_state(LeadFSM.business_type)

    await callback.message.answer(
        "Чем занимается компания?\n(коротко укажите нишу)"
    )

# 3️⃣ Ниша
@dp.message(LeadFSM.business_type)
async def get_business_type(message: Message, state: FSMContext):
    await state.update_data(business_type=message.text)
    await state.set_state(LeadFSM.volume)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="До 50", callback_data="vol_50")],
        [InlineKeyboardButton(text="50–200", callback_data="vol_200")],
        [InlineKeyboardButton(text="200–1000", callback_data="vol_1000")],
        [InlineKeyboardButton(text="1000+", callback_data="vol_1000p")]
    ])
    await message.answer(
        "Сколько заявок / клиентов в месяц?",
        reply_markup=kb
    )

# 4️⃣ Объем
@dp.callback_query(lambda c: c.data.startswith("vol_"))
async def choose_volume(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    volume = callback.data.replace("vol_", "")
    await state.update_data(volume=volume)
    await state.set_state(LeadFSM.integrations)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="CRM", callback_data="int_crm")],
        [InlineKeyboardButton(text="Платежи", callback_data="int_pay")],
        [InlineKeyboardButton(text="Google Sheets", callback_data="int_sheets")],
        [InlineKeyboardButton(text="Пока не знаю", callback_data="int_none")]
    ])
    await callback.message.answer(
        "Нужны ли интеграции?",
        reply_markup=kb
    )

# 5️⃣ Интеграции
@dp.callback_query(lambda c: c.data.startswith("int_"))
async def choose_integrations(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    integrations = callback.data.replace("int_", "")
    await state.update_data(integrations=integrations)
    await state.set_state(LeadFSM.budget)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="До 30 000 ₽", callback_data="bud_30")],
        [InlineKeyboardButton(text="30–80 000 ₽", callback_data="bud_80")],
        [InlineKeyboardButton(text="80 000 ₽ +", callback_data="bud_80p")],
        [InlineKeyboardButton(text="Нужна оценка", callback_data="bud_est")]
    ])
    await callback.message.answer(
        "Ориентировочный бюджет проекта:",
        reply_markup=kb
    )

# 6️⃣ Бюджет
@dp.callback_query(lambda c: c.data.startswith("bud_"))
async def choose_budget(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    budget = callback.data.replace("bud_", "")
    await state.update_data(budget=budget)
    await state.set_state(LeadFSM.deadline)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Срочно", callback_data="dead_now")],
        [InlineKeyboardButton(text="1–2 недели", callback_data="dead_2w")],
        [InlineKeyboardButton(text="В течение месяца", callback_data="dead_month")],
        [InlineKeyboardButton(text="Пока изучаю", callback_data="dead_later")]
    ])
    await callback.message.answer(
        "Когда планируете запуск?",
        reply_markup=kb
    )

# 7️⃣ Сроки
@dp.callback_query(lambda c: c.data.startswith("dead_"))
async def choose_deadline(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    deadline = callback.data.replace("dead_", "")
    await state.update_data(deadline=deadline)
    await state.set_state(LeadFSM.final_comment)

    await callback.message.answer(
        "Если есть дополнительные требования или примеры — напишите одним сообщением."
    )

# 8️⃣ Финальный комментарий и отправка админу
@dp.message(LeadFSM.final_comment)
async def finish_lead(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    data = await state.get_data()

    lead_text = (
        "🔥 <b>Новый B2B-лид</b>\n\n"
        f"Роль: {data.get('role')}\n"
        f"Цель: {data.get('goal')}\n"
        f"Ниша: {data.get('business_type')}\n"
        f"Объем: {data.get('volume')}\n"
        f"Интеграции: {data.get('integrations')}\n"
        f"Бюджет: {data.get('budget')}\n"
        f"Сроки: {data.get('deadline')}\n\n"
        f"Комментарий:\n{data.get('comment')}\n\n"
        f"👤 @{message.from_user.username} ({message.from_user.id})"
    )

    await bot.send_message(ADMIN_ID, lead_text)
    await message.answer(
        "Заявка получена.\n"
        "Подготовлю предложение и свяжусь с вами в ближайшее время."
    )
    await state.clear()

# ================= ADMIN REPLIES =================
@dp.callback_query(lambda c: c.data.startswith("tpl_"))
async def admin_template(callback: CallbackQuery):
    await callback.answer()
    _, _, user_id = callback.data.split("_")
    await bot.send_message(int(user_id), "Спасибо за обращение! Мы скоро свяжемся с вами.")
    await callback.message.answer("Ответ отправлен ✅")

@dp.callback_query(lambda c: c.data.startswith("manual_"))
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

# ================= RUN =================
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
