import asyncio
import sqlite3
import os
import re
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
        [InlineKeyboardButton(text="🐱 хотелки Кота", callback_data="show_kot")],
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
        "• /kot — показать хотелки Кота\n"
        "• /sun — показать хотелки Солнце\n"
        "• /add — добавить хотелку\n"
        "• /del — удалить хотелку (перешли сообщение с ссылкой или напиши /del [ссылка])\n"
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
        "   • /kot — хотелки Кота\n"
        "   • /sun — хотелки Солнце\n\n"
        "🔹 Удалить хотелку (2 способа):\n"
        "   • Перешли сообщение с ссылкой в чат и напиши /del\n"
        "   • Или просто напиши: /del [ссылка]]n\n"
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

# Команда /del (удаление)
@dp.message(Command("del"))
async def delete_command(message: types.Message):
    user_id = message.from_user.id
    
    # Проверяем, есть ли ссылка в тексте команды
    text = message.text
    link_match = re.search(r'(https?://[^\s]+)', text)
    
    if link_match:
        # Способ 1: ссылка прямо в команде /del https://...
        link = link_match.group(1)
        await delete_wish_by_link(user_id, link, message)
    else:
        # Способ 2: ждем пересланное сообщение
        await message.answer(
            "🗑 Режим удаления\n\n"
            "Перешли сообщение с ссылкой, которую хочешь удалить.\n"
            "Или напиши /del [ссылка]"
        )
        # Сохраняем состояние ожидания пересылки
        # Для простоты, следующий пересланный ответ будет обработан в handle_message

# Функция удаления по ссылке
async def delete_wish_by_link(user_id, link, message):
    conn = sqlite3.connect('wishes.db')
    cur = conn.cursor()
    
    # Ищем хотелку с такой ссылкой у этого пользователя
    cur.execute(
        "SELECT id, link, comment FROM wishes WHERE user_id = ? AND link = ?",
        (user_id, link)
    )
    wish = cur.fetchone()
    
    if wish:
        cur.execute("DELETE FROM wishes WHERE id = ?", (wish[0],))
        conn.commit()
        
        # Определяем имя пользователя для ответа
        if user_id == MY_ID:
            name = "Кота 🐱"
        elif user_id == HER_ID:
            name = "Солнце 💖"
        else:
            name = "пользователя"
        
        await message.answer(f"✅ Удалено из хотелок {name}!")
    else:
        await message.answer("❌ Не найдена такая хотелка. Проверь ссылку.")
    
    conn.close()

# Команда /kot
@dp.message(Command("kot"))
async def show_my_wishes(message: types.Message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect('wishes.db')
    cur = conn.cursor()
    cur.execute(
        "SELECT id, link, comment, date FROM wishes WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    )
    wishes = cur.fetchall()
    conn.close()
    
    if not wishes:
        await message.answer("🐱 Пока нет хотелок. Отправь ссылку в чат, чтобы добавить!")
        return
    
    text = "🐱 *Твои хотелки:*\n\n"
    for i, (wish_id, link, comment, date) in enumerate(wishes, 1):
        text += f"{i}. [Ссылка]({link})"
        if comment:
            text += f" — _{comment}_"
        text += f"\n   🗑 Чтобы удалить: `/del {link}`\n\n"
    
    await message.answer(
        text, 
        parse_mode="Markdown", 
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Режим удаления", callback_data="delete_mode")]
        ])
    )

# Команда /sun
@dp.message(Command("sun"))
async def show_her_wishes(message: types.Message):
    conn = sqlite3.connect('wishes.db')
    cur = conn.cursor()
    cur.execute(
        "SELECT id, link, comment, date FROM wishes WHERE user_id = ? ORDER BY date DESC",
        (HER_ID,)
    )
    wishes = cur.fetchall()
    conn.close()
    
    if not wishes:
        await message.answer("💖 У Солнце пока нет хотелок.")
        return
    
    text = "💖 *Хотелки Солнце:*\n\n"
    for i, (wish_id, link, comment, date) in enumerate(wishes, 1):
        text += f"{i}. [Ссылка]({link})"
        if comment:
            text += f" — _{comment}_"
        text += f"\n   🗑 Чтобы удалить: `/del {link}`\n\n"
    
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
            "SELECT id, link, comment FROM wishes WHERE user_id = ? ORDER BY date DESC",
            (user_id,)
        )
        wishes = cur.fetchall()
        conn.close()
        
        if not wishes:
            await callback.message.answer("🐱 Пока нет хотелок.")
        else:
            text = "🐱 *Твои хотелки:*\n\n"
            for i, (wish_id, link, comment) in enumerate(wishes, 1):
                text += f"{i}. [Ссылка]({link})"
                if comment:
                    text += f" — _{comment}_"
                text += f"\n   🗑 Чтобы удалить: `/del {link}`\n\n"
            
            await callback.message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
        
        await callback.answer()
    
    elif data == "show_sun":
        conn = sqlite3.connect('wishes.db')
        cur = conn.cursor()
        cur.execute(
            "SELECT id, link, comment FROM wishes WHERE user_id = ? ORDER BY date DESC",
            (HER_ID,)
        )
        wishes = cur.fetchall()
        conn.close()
        
        if not wishes:
            await callback.message.answer("💖 У Солнце пока нет хотелок.")
        else:
            text = "💖 *Хотелки Солнце:*\n\n"
            for i, (wish_id, link, comment) in enumerate(wishes, 1):
                text += f"{i}. [Ссылка]({link})"
                if comment:
                    text += f" — _{comment}_"
                text += f"\n   🗑 Чтобы удалить: `/del {link}`\n\n"
            
            await callback.message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
        
        await callback.answer()
    
    elif data == "delete_mode":
        await callback.message.answer(
            "🗑 Режим удаления\n\n"
            "**Способ 1:** Перешли сообщение с ссылкой и напиши `/del`\n"
            "**Способ 2:** Напиши `/del [ссылка]`\n\n"
            "Пример: `/del [ссылка]`",
            parse_mode="Markdown"
        )
        await callback.answer()
    
    elif data == "add_wish":
        await callback.message.answer("📎 Отправь ссылку на товар в этот чат!")
        await callback.answer()

# Обработка обычных сообщений (сохранение ссылок + удаление через пересылку)
@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    
    # Проверка на удаление через пересылку
    if message.reply_to_message and message.text and "/del" in message.text:
        # Пользователь ответил на сообщение с /del
        original_msg = message.reply_to_message
        
        # Ищем ссылку в оригинальном сообщении
        if original_msg.text and "http" in original_msg.text:
            link_match = re.search(r'(https?://[^\s]+)', original_msg.text)
            if link_match:
                link = link_match.group(1)
                await delete_wish_by_link(user_id, link, message)
                return
    
    # Обычное сохранение ссылок
    if not message.text:
        return
        
    text = message.text
    
    # Если команда /del уже обработана выше, пропускаем
    if text.startswith("/del"):
        return
    
    if "http" in text or "ozon" in text.lower() or "wildberries" in text.lower() or "wb" in text.lower():
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
            
            # Проверяем, нет ли уже такой ссылки у пользователя
            cur.execute(
                "SELECT id FROM wishes WHERE user_id = ? AND link = ?",
                (user_id, link)
            )
            existing = cur.fetchone()
            
            if existing:
                await message.reply("⚠️ Эта ссылка уже есть в твоих хотелках!")
            else:
                cur.execute(
                    "INSERT INTO wishes (user_id, username, link, comment, date) VALUES (?, ?, ?, ?, ?)",
                    (user_id, username, link, comment_text, date)
                )
                conn.commit()
                
                if user_id == MY_ID:
                    owner = "🐱 в хотелки Кота"
                elif user_id == HER_ID:
                    owner = "💖 в хотелки Солнце"
                else:
                    owner = "в хотелки"
                
                await message.reply(f"✅ Добавлено {owner}!")
            
            conn.close()

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