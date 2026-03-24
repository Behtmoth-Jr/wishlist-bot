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
        [InlineKeyboardButton(text="🐱 хотелки Кота", callback_data="show_kot")],
        [InlineKeyboardButton(text="💖 Хотелки Солнце", callback_data="show_sun")],
        [InlineKeyboardButton(text="➕ Добавить хотелку", callback_data="add_wish")]
    ])
    return keyboard

# Клавиатура для удаления (динамическая)
def get_delete_keyboard(wish_id, wish_type):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{wish_type}_{wish_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_{wish_type}")]
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
        "• /del — режим удаления (нажми на любую хотелку)\n"
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
        "🔹 Удалить хотелку:\n"
        "   • /del — войти в режим удаления\n"
        "   • Нажми на кнопку с номером хотелки, которую хочешь удалить\n"
        "   • Подтверди удаление\n\n"
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

# Команда /del (режим удаления)
@dp.message(Command("del"))
async def delete_mode(message: types.Message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect('wishes.db')
    cur = conn.cursor()
    cur.execute(
        "SELECT id, link, comment FROM wishes WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    )
    wishes = cur.fetchall()
    conn.close()
    
    if not wishes:
        await message.answer("🐱 У тебя пока нет хотелок для удаления.")
        return
    
    # Создаем клавиатуру с кнопками для каждой хотелки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for wish_id, link, comment in wishes:
        # Обрезаем ссылку для отображения
        short_link = link[:40] + "..." if len(link) > 40 else link
        button_text = f"🗑 {short_link}"
        if comment:
            button_text += f" ({comment[:30]})"
        
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=button_text, callback_data=f"select_delete_{wish_id}")]
        )
    
    # Добавляем кнопку отмены
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_delete")])
    
    await message.answer(
        "🗑 Режим удаления\n\n"
        "Нажми на хотелку, которую хочешь удалить:",
        reply_markup=keyboard
    )

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
    
    # Отправляем каждую хотелку отдельным сообщением с кнопкой удаления
    for wish_id, link, comment, date in wishes:
        text = f"🐱 *Хотелка Кота:*\n\n"
        text += f"[Ссылка]({link})"
        if comment:
            text += f"\n📝 *Комментарий:* _{comment}_"
        text += f"\n📅 *Добавлено:* `{date}`"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_kot_{wish_id}")]
        ])
        
        await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=keyboard)

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
    
    for wish_id, link, comment, date in wishes:
        text = f"💖 *Хотелка Солнце:*\n\n"
        text += f"[Ссылка]({link})"
        if comment:
            text += f"\n📝 *Комментарий:* _{comment}_"
        text += f"\n📅 *Добавлено:* `{date}`"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_sun_{wish_id}")]
        ])
        
        await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=keyboard)

# Обработка inline-кнопок
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data
    
    # Обработка удаления из /kot
    if data.startswith("delete_kot_"):
        wish_id = int(data.split("_")[2])
        user_id = callback.from_user.id
        
        # Проверяем, что хотелка принадлежит пользователю
        conn = sqlite3.connect('wishes.db')
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM wishes WHERE id = ?", (wish_id,))
        result = cur.fetchone()
        
        if result and result[0] == user_id:
            cur.execute("DELETE FROM wishes WHERE id = ?", (wish_id,))
            conn.commit()
            await callback.message.edit_text("✅ Хотелка удалена!")
        else:
            await callback.answer("❌ Нельзя удалить чужую хотелку!", show_alert=True)
        
        conn.close()
        await callback.answer()
    
    # Обработка удаления из /sun
    elif data.startswith("delete_sun_"):
        wish_id = int(data.split("_")[2])
        user_id = callback.from_user.id
        
        conn = sqlite3.connect('wishes.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM wishes WHERE id = ?", (wish_id,))
        conn.commit()
        conn.close()
        
        await callback.message.edit_text("✅ Хотелка удалена!")
        await callback.answer()
    
    # Обработка выбора хотелки для удаления (из режима /del)
    elif data.startswith("select_delete_"):
        wish_id = int(data.split("_")[2])
        
        # Запрашиваем подтверждение
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{wish_id}")],
            [InlineKeyboardButton(text="🔙 Нет, отмена", callback_data="cancel_delete")]
        ])
        
        await callback.message.edit_text(
            f"⚠️ *Подтверждение удаления*\n\n"
            f"Вы уверены, что хотите удалить эту хотелку?\n"
            f"Это действие нельзя отменить.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await callback.answer()
    
    # Подтверждение удаления
    elif data.startswith("confirm_delete_"):
        wish_id = int(data.split("_")[2])
        user_id = callback.from_user.id
        
        conn = sqlite3.connect('wishes.db')
        cur = conn.cursor()
        
        # Проверяем, что хотелка принадлежит пользователю
        cur.execute("SELECT user_id FROM wishes WHERE id = ?", (wish_id,))
        result = cur.fetchone()
        
        if result and result[0] == user_id:
            cur.execute("DELETE FROM wishes WHERE id = ?", (wish_id,))
            conn.commit()
            await callback.message.edit_text("✅ Хотелка успешно удалена!")
        else:
            await callback.message.edit_text("❌ Ошибка: хотелка не найдена или принадлежит другому пользователю.")
        
        conn.close()
        await callback.answer()
    
    # Отмена удаления
    elif data == "cancel_delete":
        await callback.message.edit_text("🔙 Удаление отменено.")
        await callback.answer()
    
    # Обработка кнопок главного меню
    elif data == "show_kot":
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
            for wish_id, link, comment in wishes:
                text = f"🐱 *Хотелка Кота:*\n\n[Ссылка]({link})"
                if comment:
                    text += f"\n📝 *Комментарий:* _{comment}_"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_kot_{wish_id}")]
                ])
                await callback.message.answer(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=keyboard)
        
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
            for wish_id, link, comment in wishes:
                text = f"💖 *Хотелка Солнце:*\n\n[Ссылка]({link})"
                if comment:
                    text += f"\n📝 *Комментарий:* _{comment}_"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_sun_{wish_id}")]
                ])
                await callback.message.answer(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=keyboard)
        
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
                owner = "🐱 в хотелки Кота"
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