import random
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

"""
Load tasks from a JSON file.

The JSON file should contain a list of tasks, where each task includes:
- level: The difficulty level of the task (e.g., "easy", "medium", "hard").
- task: The description of the task to be sent to the user.
- function_name: The name of the function expected in the user code.
- test_cases: A list of test cases to validate the user function, where each test case has:
  - input: Input data for the function (as a string).
  - output: The expected output of the function.
"""
# The following code for loading tasks from a JSON file is a standard approach
# as described in the Python official documentation.
# Source: https://docs.python.org/3/library/json.html
with open("tasks.json", "r", encoding="utf-8") as file:
    tasks = json.load(file)

"""
Initialize variables to store unique tasks.

- `unique_tasks`: A list to store tasks without duplicates.
- `seen_tasks`: A set to track already seen tasks, identified by their unique combination of level, task, and function name.
"""
unique_tasks = []  # List to store tasks without duplicates
seen_tasks = set()  # Set to track already seen tasks

"""
Iterate over all tasks and filter out duplicates.

For each task:
1. Create a unique identifier (`task_tuple`) based on:
   - level: The difficulty level of the task.
   - task: The description of the task.
   - function_name: The name of the function expected in the user code.
2. If the task is not already in `seen_tasks`:
   - Add it to the `unique_tasks` list.
   - Mark it as seen by adding `task_tuple` to the `seen_tasks` set.
"""
# The following code for filtering unique tasks is inspired by common practices
# in Python tutorials and educational materials.
for task in tasks:
    task_tuple = (task["level"], task["task"], task["function_name"])

    if task_tuple not in seen_tasks:
        unique_tasks.append(task)  # Add the task to the list
        seen_tasks.add(task_tuple)  # Mark the task as seen

"""
Save the unique tasks back to the JSON file.

The `tasks.json` file will be overwritten with the filtered list of unique tasks.
The JSON file will:
- Exclude duplicate tasks.
- Preserve proper formatting with an indentation of 4 spaces.
"""
with open("tasks.json", "w", encoding="utf-8") as file:
    json.dump(unique_tasks, file, ensure_ascii=False, indent=4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Sends a greeting message and instructions on how to use the bot.

    Args:
        update (Update): The incoming update containing information about the user and the chat.
        context (ContextTypes.DEFAULT_TYPE): The context of the current conversation.

    Returns:
        None
    """
    await update.message.reply_text(
        "Привет! Я бот для задач по программированию.\n"
        "Выберите уровень сложности:\n"
        "/easy - Лёгкий уровень\n"
        "/medium - Средний уровень\n"
        "/hard - Сложный уровень"
    )

async def get_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Retrieves a random task based on the selected difficulty level and sends it to the user.

    Args:
        update (Update): The incoming update containing the user's command.
        context (ContextTypes.DEFAULT_TYPE): The context of the current conversation.

    Returns:
        None
    """
    command = update.message.text[1:]  # Remove the "/" from the command
    level_map = {"easy": "легкий", "medium": "средний", "hard": "сложный"}
    selected_level = level_map.get(command)

    if not selected_level:
        await update.message.reply_text("Неверная команда. Используйте /easy, /medium или /hard.")
        return

    filtered_tasks = [task for task in tasks if task["level"] == selected_level]
    if not filtered_tasks:
        await update.message.reply_text(f"Для уровня {selected_level} пока нет задач.")
        return

    task = random.choice(filtered_tasks)
    context.user_data["current_task"] = task

    await update.message.reply_text(
        f"Задача ({selected_level} уровень):\n{task['task']}\n\n"
        f"После написания решения отправьте его кодом. Ожидается функция с именем: {task['function_name']}."
    )

async def solve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Evaluates the user's submitted code against the current task's test cases.

    Args:
        update (Update): The incoming update containing the user's code.
        context (ContextTypes.DEFAULT_TYPE): The context of the current conversation, including task details.

    Returns:
        None
    """
    user_code = update.message.text
    task = context.user_data.get("current_task")

    if not task:
        await update.message.reply_text("Сначала выберите задачу: /easy, /medium или /hard.")
        return

    function_name = task.get("function_name")
    if not function_name:
        await update.message.reply_text("Ошибка: задача не содержит ожидаемого имени функции.")
        return

    try:
        local_vars = {}
        exec(user_code, {}, local_vars)

        if function_name not in local_vars:
            await update.message.reply_text(f"Ошибка: функция '{function_name}' не найдена в вашем коде.")
            return

        user_function = local_vars[function_name]

        for i, test_case in enumerate(task["test_cases"]):
            input_data = eval(test_case["input"])
            expected_output = test_case["output"]

            if isinstance(input_data, tuple):
                result = user_function(*input_data)
            else:
                result = user_function(input_data)

            if result != expected_output:
                await update.message.reply_text(
                    f"Тест {i + 1} не пройден:\n"
                    f"Входные данные: {test_case['input']}\n"
                    f"Ожидалось: {expected_output}\n"
                    f"Получено: {result}"
                )
                return

        await update.message.reply_text("Поздравляю! Все тесты пройдены!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка выполнения вашего кода: {e}")

def main():
    """
    Initializes and runs the bot application.

    Registers command handlers and starts polling for updates.

    Returns:
        None
    """
    token = "7645253860:AAGVEd0XvBWVChNpX4sH1A2Mmtg1C51KLKk"

    application = Application.builder().token(token).build()

    # The following setup for the Telegram bot, including CommandHandler and MessageHandler,
    # is inspired by the official python-telegram-bot documentation.
    # Source: https://python-telegram-bot.readthedocs.io/
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("easy", get_task))
    application.add_handler(CommandHandler("medium", get_task))
    application.add_handler(CommandHandler("hard", get_task))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, solve))

    application.run_polling()

if __name__ == "__main__":
    main()