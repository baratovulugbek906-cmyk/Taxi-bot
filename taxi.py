import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
API_TOKEN = '8614946744:AAE5qZoysF7tQywxXlcuYdjvW96Mc9fcoIU' # BotFather'dan olingan tokenni yozing
ADMIN_ID = 8214179886  # O'zingizning Telegram ID raqamingizni yozing

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- MA'LUMOTLAR BAZASI ---
def init_db():
    conn = sqlite3.connect('taxi_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            car_name TEXT,
            car_number TEXT,
            car_color TEXT,
            full_name TEXT,
            phone TEXT,
            username TEXT,
            photo_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_driver_to_db(user_id, car, number, color, name, phone, username, photo_id):
    conn = sqlite3.connect('taxi_bot.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO drivers 
        (user_id, car_name, car_number, car_color, full_name, phone, username, photo_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, car, number, color, name, phone, username, photo_id))
    conn.commit()
    conn.close()

def delete_driver_from_db(driver_id):
    conn = sqlite3.connect('taxi_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM drivers WHERE id = ?', (driver_id,))
    conn.commit()
    conn.close()

def get_all_drivers():
    conn = sqlite3.connect('taxi_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, car_name, car_number, car_color, full_name, phone, username, photo_id FROM drivers')
    drivers = cursor.fetchall()
    conn.close()
    return drivers

# --- STATES (HOLATLAR) ---
class DriverReg(StatesGroup):
    car_name = State()
    car_number = State()
    car_color = State()
    photo = State()
    full_name = State()
    phone = State()

# --- KLAVIATURALAR ---
def get_main_menu(user_id):
    buttons = [
        [KeyboardButton(text="🚖 Taksiga qo'shilish")],
        [KeyboardButton(text="🚕 Taksi bo'limi")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="⚙️ Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- START ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(f"Assalomu alaykum! Termez-Sariosiyo taksi botiga xush kelibsiz.", 
                         reply_markup=get_main_menu(message.from_user.id))

# --- RO'YXATDAN O'TISH ---
@dp.message(F.text == "🚖 Taksiga qo'shilish")
async def start_reg(message: types.Message, state: FSMContext):
    await message.answer("Mashinangiz rusumini kiriting (masalan: Nexia 3):")
    await state.set_state(DriverReg.car_name)

@dp.message(DriverReg.car_name)
async def process_car(message: types.Message, state: FSMContext):
    await state.update_data(car_name=message.text)
    await message.answer("Mashina raqamini kiriting:")
    await state.set_state(DriverReg.car_number)

@dp.message(DriverReg.car_number)
async def process_num(message: types.Message, state: FSMContext):
    await state.update_data(car_number=message.text)
    await message.answer("Mashina rangini kiriting:")
    await state.set_state(DriverReg.car_color)

@dp.message(DriverReg.car_color)
async def process_color(message: types.Message, state: FSMContext):
    await state.update_data(car_color=message.text)
    await message.answer("Mashinangiz rasmini yuboring (bitta rasm):")
    await state.set_state(DriverReg.photo)

@dp.message(DriverReg.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await message.answer("Ism va familiyangizni kiriting:")
    await state.set_state(DriverReg.full_name)

@dp.message(DriverReg.full_name)
async def process_fn(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Telefon raqamingizni kiriting:")
    await state.set_state(DriverReg.phone)

@dp.message(DriverReg.phone)
async def process_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    user_username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    info = (f"🆕 Yangi haydovchi:\n\n"
            f"🚘 Mashina: {data['car_name']}\n"
            f"🔢 Raqam: {data['car_number']}\n"
            f"🎨 Rang: {data['car_color']}\n"
            f"👤 Ism: {data['full_name']}\n"
            f"📞 Tel: {message.text}\n"
            f"✈️ TG: {user_username}")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"accept_{user_id}")],
        [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")]
    ])
    
    # Adminga rasm bilan yuborish
    await bot.send_photo(ADMIN_ID, data['photo_id'], caption=info, reply_markup=kb)
    await message.answer("Ma'lumotlar adminga yuborildi. Tasdiqlanishini kuting.", reply_markup=get_main_menu(user_id))
    await state.clear()

# --- ADMIN TASDIQLASHI ---
@dp.callback_query(F.data.startswith("accept_"))
async def admin_accept(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    caption = call.message.caption
    lines = caption.split('\n')
    
    car = lines[2].split(': ')[1]
    num = lines[3].split(': ')[1]
    col = lines[4].split(': ')[1]
    name = lines[5].split(': ')[1]
    phone = lines[6].split(': ')[1]
    username = lines[7].split(': ')[1]
    photo_id = call.message.photo[-1].file_id

    add_driver_to_db(user_id, car, num, col, name, phone, username, photo_id)
    
    await bot.send_message(user_id, "✅ Sizning so'rovingiz tasdiqlandi!")
    await call.message.edit_caption(caption=caption + "\n\n✅ TASDIQLANDI")

# --- TAKSI BO'LIMI ---
@dp.message(F.text == "🚕 Taksi bo'limi")
async def taxi_list(message: types.Message):
    drivers = get_all_drivers()
    if not drivers:
        await message.answer("Hozircha haydovchilar yo'q.")
        return

    for d in drivers:
        text = (f"🚕 **Haydovchi:** {d[4]}\n"
                f"🚘 Mashina: {d[1]} ({d[3]})\n"
                f"🔢 Raqam: {d[2]}\n"
                f"📞 Tel: {d[5]}\n"
                f"✈️ TG: {d[6]}")
        await bot.send_photo(message.chat.id, d[7], caption=text, parse_mode="Markdown")

# --- ADMIN PANEL ---
@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    drivers = get_all_drivers()
    if not drivers:
        await message.answer("Bazada haydovchilar yo'q.")
        return

    for d in drivers:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_{d[0]}")]
        ])
        await message.answer(f"👤 {d[4]} | {d[1]}", reply_markup=kb)

@dp.callback_query(F.data.startswith("del_"))
async def delete_driver(call: types.CallbackQuery):
    driver_id = int(call.data.split("_")[1])
    delete_driver_from_db(driver_id)
    await call.message.edit_text("🗑 Haydovchi o'chirildi.")

# --- ISHGA TUSHIRISH ---
async def main():
    init_db()
    print("Bot ishlamoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
