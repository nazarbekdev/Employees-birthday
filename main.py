import os
import psycopg2
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from datetime import datetime
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from states import AddEmployee
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('BOT_TOKEN')

admins = os.getenv('ADMINS')
ADMINS = [int(admin_id) for admin_id in admins.split(',')]

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


def connect_to_database():
    try:
        connection = psycopg2.connect(host=os.getenv('DB_HOST'), dbname=os.getenv('DB_NAME'),
                                      user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'))
        return connection
    except psycopg2.Error as e:
        print("An error occurred: ", e)


@dp.message_handler(commands=['add_employee'], state="*")
async def add_employee(message: types.Message):
    await message.answer("Xodim haqida to'liq ma'lumot kiriting!")
    await message.answer("Xodimni ismini kiriting:")
    await AddEmployee.FirstName.set()


@dp.message_handler(state=AddEmployee.FirstName)
async def process_first_name(message: types.Message, state: FSMContext):
    try:
        first_name = message.text
        await state.update_data(first_name=first_name)
        await message.answer("Xodimni familiyasini kiriting:")
        await AddEmployee.next()
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")


@dp.message_handler(state=AddEmployee.LastName)
async def process_last_name(message: types.Message, state: FSMContext):
    try:
        last_name = message.text
        await state.update_data(last_name=last_name)
        await message.answer("Xodimni tug'ilgan kunini kiriting (masalan, 'Y-M-D' 2002-02-02):")
        await AddEmployee.next()
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")


@dp.message_handler(state=AddEmployee.Birthday)
async def process_birthday(message: types.Message, state: FSMContext):
    try:
        birthday = message.text
        datetime.strptime(birthday, '%Y-%m-%d')
        await state.update_data(birthday=birthday)
        await message.answer("Xodim lavozimini kiriting:")
        await AddEmployee.next()
    except ValueError:
        await message.answer("Tug'ilgan kunni sana formatida kiriting. Masalan, 2002-02-02")


@dp.message_handler(state=AddEmployee.Position)
async def process_position(message: types.Message, state: FSMContext):
    try:
        position = message.text
        await state.update_data(position=position)
        await message.answer("Xodimning rasmini yuboring:")
        await AddEmployee.next()
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")


@dp.message_handler(content_types=types.ContentType.PHOTO, state=AddEmployee.Photo)
async def process_image(message: types.Message, state: FSMContext):
    try:
        photo = message.photo[-1]
        photo_id = photo.file_id
        await state.update_data(photo_id=photo_id)

        data = await state.get_data()
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute('''INSERT INTO Employees (ism, familiya, tugilgan_kun, lavozim, rasm)
                          VALUES (%s, %s, %s, %s, %s)''',
                       (data['first_name'], data['last_name'], data['birthday'], data['position'], data['photo_id']))
        connection.commit()
        connection.close()

        await message.answer("Xodim muvaffaqiyatli qo'shildi!", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")


async def send_birthday_notification():
    today = datetime.now()
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM Employees WHERE EXTRACT(MONTH FROM DATE(tugilgan_kun)) = %s AND EXTRACT(DAY FROM DATE(tugilgan_kun)) = %s",
            (today.month, today.day)
        )
        employees = cursor.fetchall()
        connection.close()

        for employee in employees:
            first_name = employee[1]
            last_name = employee[2]
            birthday = employee[3]
            position = employee[4]
            image_data = employee[5]

            caption = f"Bugun {first_name} {last_name}ning tug'ilgan kuni!\nTug'ilgan kuningiz muborak bo'lsin! 🥳 🎉\n"
            caption += f"Ism: {first_name}\n"
            caption += f"Familiya: {last_name}\n"
            caption += f"Tug'ilgan sana: {birthday}\n"
            caption += f"Lavozim: {position}\n"
            for admin_id in ADMINS:
                await bot.send_photo(chat_id=admin_id, photo=image_data, caption=caption)

    except psycopg2.Error as e:
        print("An error occurred: ", e)


async def scheduler():
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(send_birthday_notification, 'cron', hour=21, minute=14)
    scheduler.start()
    await asyncio.sleep(5)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    executor.start_polling(dp, loop=loop, skip_updates=True)
