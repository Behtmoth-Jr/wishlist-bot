import asyncio
import sqlite3
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ID пользователей
MY_ID = int(os.getenv('MY_ID'))      # Кот 🐱
HER_ID = int(os.getenv('HER_ID'))    # Солнце 💖

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('wishes.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            link TEXT,
            comment TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Клавиатура главного меню
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐱 Мои хотелки (Кот)", callback_data="show_kot")],
        [InlineKeyboardButton(text="💖 Хотелки Солнце", callback_data="show_sun")],
        [InlineKeyboardButton(text="➕ Добавить хотелку", callback_data="add_wish")]
    ])
    return keyboard

# Команда /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🐱💖 Привет! Это бот для совместных хотелок!\n\n"
        "📌 Что умею:\n"
        "• Отправь ссылку на Ozon/WB в чат — я сохраню её\n"
        "• /kot — показать твои хотелки\n"
        "• /sun — показать хотелки Солнце\n"
        "• /add — добавить хотелку\n"
        "• /help — помощь\n\n"
        "💡 Просто кидай ссылки в чат, и они автоматически добавятся в твой список!",
        reply_markup=get_main_keyboard()
    )

# Команда /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "📖 Помощь по использованию:\n\n"
        "🔹 Добавить хотелку:\n"
        "   • Просто отправь ссылку на товар (Ozon, Wildberries) в чат\n"
        "   • Или используй команду /add и затем ссылку\n\n"
        "🔹 Посмотреть списки:\n"
        "   • /kot — твои хотелки\n"
        "   • /sun — хотелки Солнце\n\n"
        "🔹 Кнопки:\n"
        "   • После /start появляется меню с кнопками\n\n"
        "❓ Вопросы? Просто напиши!"
    )

# Команда /add
@dp.message(Command("add"))
async def add_command(message: types.Message):
    await message.answer(
        "📎 Отправь ссылку на товар.\n"
        "Можно добавить комментарий после ссылки."
    )

# Команда /kot (мои хотелки)
@dp.message(Command("kot"))
async def show_my_wishes(message: types.Message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect('wishes.db')
    cur = conn.cursor()
    cur.execute(
        "SELECT link, comment, date FROM wishes WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    )
    wishes = cur.fetchall()
    conn.close()
    
    if not wishes:
        await message.answer("🐱 У тебя пока нет хотелок. Отправь ссылку в чат, чтобы добавить!")
        return
    
    text = "🐱 *Твои хотелки:*\n\n"
    for i, (link, comment, date) in enumerate(wishes, 1):
        text += f"{i}. [Ссылка]({link})"
        if comment:
            text += f" — _{comment}_"
        text += "\n"
    
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

# Команда /sun (хотелки девушки)
@dp.message(Command("sun"))
async def show_her_wishes(message: types.Message):
    conn = sqlite3.connect('wishes.db')
    cur = conn.cursor()
    cur.execute(
        "SELECT link, comment, date FROM wishes WHERE user_id = ? ORDER BY date DESC",
        (HER_ID,)
    )
    wishes = cur.fetchall()
    conn.close()
    
    if not wishes:
        await message.answer("💖 У Солнце пока нет хотелок.")
        return
    
    text = "💖 *Хотелки Солнце:*\n\n"
    for i, (link, comment, date) in enumerate(wishes, 1):
        text += f"{i}. [Ссылка]({link})"
        if comment:
            text += f" — _{comment}_"
        text += "\n"
    
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

# Обработка inline-кнопок
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data
    
    if data == "show_kot":
        user_id = callback.from_user.id
        conn = sqlite3.connect('wishes.db')
        cur = conn.cursor()
        cur.execute(
            "SELECT link, comment FROM wishes WHERE user_id = ? ORDER BY date DESC",
            (user_id,)
        )
        wishes = cur.fetchall()
        conn.close()
        
        if not wishes:
            await callback.message.answer("🐱 У тебя пока нет хотелок.")
        else:
            text = "🐱 *Твои хотелки:*\n\n"
            for i, (link, comment) in enumerate(wishes, 1):
                text += f"{i}. [Ссылка]({link})"
                if comment:
                    text += f" — _{comment}_"
                text += "\n"
            await callback.message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
        
        await callback.answer()
    
    elif data == "show_sun":
        conn = sqlite3.connect('wishes.db')
        cur = conn.cursor()
        cur.execute(
            "SELECT link, comment FROM wishes WHERE user_id = ? ORDER BY date DESC",
            (HER_ID,)
        )
        wishes = cur.fetchall()
        conn.close()
        
        if not wishes:
            await callback.message.answer("💖 У Солнце пока нет хотелок.")
        else:
            text = "💖 *Хотелки Солнце:*\n\n"
            for i, (link, comment) in enumerate(wishes, 1):
                text += f"{i}. [Ссылка]({link})"
                if comment:
                    text += f" — _{comment}_"
                text += "\n"
            await callback.message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
        
        await callback.answer()
    
    elif data == "add_wish":
        await callback.message.answer("📎 Отправь ссылку на товар в этот чат!")
        await callback.answer()

# Автоматическое сохранение ссылок из сообщений
@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return
        
    text = message.text
    
    if "http" in text or "ozon" in text.lower() or "wildberries" in text.lower() or "wb" in text.lower():
        user_id = message.from_user.id
        username = message.from_user.full_name
        
        words = text.split()
        link = None
        comment = []
        
        for word in words:
            if word.startswith("http://") or word.startswith("https://"):
                link = word
            else:
                comment.append(word)
        
        if link:
            comment_text = " ".join(comment) if comment else ""
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect('wishes.db')
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO wishes (user_id, username, link, comment, date) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, link, comment_text, date)
            )
            conn.commit()
            conn.close()
            
            if user_id == MY_ID:
                owner = "🐱 в твои хотелки"
            elif user_id == HER_ID:
                owner = "💖 в хотелки Солнце"
            else:
                owner = "в хотелки"
            
            await message.reply(f"✅ Добавлено {owner}!")

# Автоматический пинг
async def keep_alive():
    while True:
        await asyncio.sleep(600)
        logging.info("Бот активен, пинг...")

# Запуск бота
async def main():
    asyncio.create_task(keep_alive())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())