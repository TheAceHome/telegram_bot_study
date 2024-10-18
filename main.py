import logging
import csv
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor


logging.basicConfig(level=logging.INFO)

API_TOKEN = '7922381649:AAFRc4QuL1vin8baSj0k1TS5L097ejZr6yE'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Определяем состояния
class Form(StatesGroup):
    waiting_for_count = State()
    waiting_for_date = State()
    waiting_for_task = State()
    waiting_for_delete = State()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я ваш Телеграмм бот.")


@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.reply("Напишите /calendar, чтобы добавить новую задачу.")


@dp.message_handler(commands=['calendar'])
async def cmd_calendar(message: types.Message):
    await Form.waiting_for_count.set()
    await message.reply("Сколько задач вы хотите добавить?")


@dp.message_handler(state=Form.waiting_for_count)
async def process_count(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        await state.update_data(count=count, tasks=[])
        await Form.waiting_for_date.set()

        await message.reply(f"Введите дату для задачи 1:")

    except ValueError:
        await message.reply("Пожалуйста, введите число.")


@dp.message_handler(state=Form.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    current = len(user_data['tasks']) + 1  # Текущий номер задачи
    date = message.text

    # Сохраняем дату и ожидаем ввод задачи
    await state.update_data(date=date)
    await Form.waiting_for_task.set()

    await message.reply("Введите задачу:")


@dp.message_handler(state=Form.waiting_for_task)
async def process_task(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    date = user_data['date']
    task = message.text

    # Сохраняем в CSV
    with open('tasks.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([date, task])

    # Добавляем задачу в список
    tasks = user_data['tasks']
    tasks.append(f"{date} - {task}")
    await state.update_data(tasks=tasks)

    # Проверяем количество задач
    count = user_data['count']
    if len(tasks) < count:
        await Form.waiting_for_date.set()
        await message.reply(f"Введите дату для задачи {len(tasks) + 1}:")
    else:
        await finalize_and_save(message, state)


async def finalize_and_save(message: types.Message, state: FSMContext):
    user_data = await state.get_data()

    if 'tasks' in user_data:
        tasks_list = "\n".join(user_data['tasks'])
        await message.reply("Ваши задачи:\n" + tasks_list)
    else:
        await message.reply("Нет задач для отображения.")

    await state.finish()  # Завершаем состояние

@dp.message_handler(commands=['show_tasks'])
async def show_tasks(message: types.Message):
    try:
        with open('tasks.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            tasks_message = "Ваши задачи:\n"
            for row in reader:
                if row:  # Проверяем, что строка не пустая
                    tasks_message += f"{row[0]} - {row[1]}\n"
            if tasks_message == "Ваши задачи:\n":
                tasks_message = "У вас нет задач."
            await message.reply(tasks_message)
    except FileNotFoundError:
        await message.reply("Файл с задачами не найден.")


@dp.message_handler(commands=['delete_task'])
async def cmd_delete_task(message: types.Message):
    try:
        with open('tasks.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            tasks = list(reader)

        if not tasks:
            await message.reply("Нет задач для удаления.")
            return

        tasks_list = "\n".join(f"{i + 1}. {date} - {task}" for i, (date, task) in enumerate(tasks))
        await message.reply("Список задач:\n" + tasks_list)

        await Form.waiting_for_delete.set()
        await message.reply("Какую задачу вы хотите удалить? Введите номер задачи.")

    except FileNotFoundError:
        await message.reply("Файл с задачами не найден.")


@dp.message_handler(state=Form.waiting_for_delete)
async def process_delete(message: types.Message):
    try:
        task_number = int(message.text) - 1  # Преобразуем номер в индекс

        with open('tasks.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            tasks = list(reader)

        if 0 <= task_number < len(tasks):
            # Удаляем задачу из списка
            removed_task = tasks.pop(task_number)

            # Сохраняем обновленный список в файл
            with open('tasks.csv', mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(tasks)

            await message.reply(f"Задача '{removed_task[1]}' удалена.")

            # Выводим обновленный список задач
            if tasks:
                updated_tasks_list = "\n".join(f"{i + 1}. {date} - {task}" for i, (date, task) in enumerate(tasks))
                await message.reply("Обновленный список задач:\n" + updated_tasks_list)
            else:
                await message.reply("Задачи больше нет.")
        else:
            await message.reply("Неверный номер задачи. Пожалуйста, попробуйте снова.")

    except ValueError:
        await message.reply("Пожалуйста, введите корректный номер задачи.")
    except FileNotFoundError:
        await message.reply("Файл с задачами не найден.")
    finally:
        pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)