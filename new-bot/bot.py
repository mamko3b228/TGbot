import logging
from settings import API_TOKEN, ADMIN_ID_DESIGNER, ADMIN_ID_PHILIPP, ADMIN_ID_ALEX
import sqlite3
import emoji
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ParseMode
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram import filters
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery
from aiogram.utils.callback_data import CallbackData

# Логинг
logging.basicConfig(level=logging.INFO)

# Create table in db
def create_table():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS requests 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT NOT NULL, 
                       phone TEXT NOT NULL, 
                       description TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Объекта бота 
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Определение состояния для получения имени пользователя
class Form(StatesGroup):
    name = State()
    phone = State()
    description = State()

# Knopka 
markup = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Оставить заявку ✅"))

# Определение команды start
@dp.message_handler(commands=['start'])
async def start_cmd_handler(message: types.Message):
    user = message.from_user
    await message.reply(f"Здравствуйте, {user.first_name}! Оставьте заявку и мы Вам перезвоним.\n\nДля начала работы нажмите на кнопку 'Оставить заявку✅'", reply_markup=markup)

# хендлер на кнопку "Оставить заявку"
@dp.message_handler(text="Оставить заявку ✅")
async def process_request_command(message: types.Message):
    await message.answer("Как Вас зовут?", reply_markup=types.ReplyKeyboardRemove())
    await Form.name.set()

# Обработка имени пользователя
@dp.message_handler(state=Form.name)
async def process_name_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    # await message.reply("Введите Ваш номер телефона (начиная с +7 или 7/8):")
    await message.answer("Введите Ваш номер телефона:")
    await Form.phone.set()

# Обработка номера телефона
@dp.message_handler(filters.Text(contains='8' ) | filters.Text(contains='7'), state=Form.phone)
async def process_phone_step(message: types.Message, state: FSMContext):
    if (len(message.text) == 11 and ('+' not in message.text)) or (len(message.text) == 12 and ('+' in message.text)):
        
        # сохраняем номер телефона в состоянии
        await state.update_data(phone_number=message.text)
        
        # переходим к следующему шагу
        async with state.proxy() as data:
            data['phone'] = message.text
        await Form.next()
        await Form.description.set()
        await message.answer("Напишите описание работ:", reply_markup=types.ReplyKeyboardRemove())
    
    else:
        await message.reply('Неверный формат номера телефона. Пожалуйста, введите 11 или 12 знаков')
        
        # await state.reset_state()  # сброс состояния формы
        
        await Form.phone.set()  # возврат к первому шагу формы

# хендлер на ввод описания заявки
@dp.message_handler(state=Form.description)
async def process_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
        await Form.description.set()

        # Сохранение данных в базе данных SQLite
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO requests (name, phone, description) VALUES (?, ?, ?)",
                        (data['name'], data['phone'], data['description']))            
        conn.commit()
        conn.close()

        await bot.send_message(chat_id=ADMIN_ID_DESIGNER, text= f"✅✅✅Новая заявка✅✅✅\n\nИмя: {data['name']}\n\nНомер телефона: {data['phone']}\n\nОписание: {data['description']}")
        await bot.send_message(chat_id=ADMIN_ID_PHILIPP, text= f"✅✅✅Новая заявка✅✅✅\n\nИмя: {data['name']}\n\nНомер телефона: {data['phone']}\n\nОписание: {data['description']}")
        await bot.send_message(chat_id=ADMIN_ID_ALEX, text= f"✅✅✅Новая заявка✅✅✅\n\nИмя: {data['name']}\n\nНомер телефона: {data['phone']}\n\nОписание: {data['description']}")
        
        #Send message to user
        user_data = f"{data['name']}, Ваша заявка оформлена!\n\nИмя: {data['name']}\n\nНомер телефона: {data['phone']}\n\nОписание: {data['description']}\n\nМы Вам перезвоним!Для оформления новой заявки нажмите /start"           
        await message.reply(user_data)
        await state.finish()
        
    # Launch Bot
if __name__ == '__main__':
    create_table()
    executor.start_polling(dp, skip_updates=True)



