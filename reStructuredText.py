import unittest
import json
from unittest.mock import AsyncMock, MagicMock
from telegram import Update
from telegram.ext import ContextTypes

from bot import start, get_task, solve


class TestTelegramBotFunctions(unittest.IsolatedAsyncioTestCase):
    """
    Класс для тестирования функций Telegram-бота.

    Содержит тесты для функций: start, get_task, solve.
    """

    async def test_start(self):
        """
        Тесты для функции start.

        Положительные:
        - Отправляется приветственное сообщение.
        - Текст сообщения содержит список команд.

        Отрицательные:
        - Объект Update не содержит сообщения.
        - Context не имеет метода `reply_text`.
        """
        # Положительный тест: корректное приветствие
        mock_update = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        mock_context = AsyncMock()
        await start(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with(
            "Привет! Я бот для задач по программированию.\n"
            "Выберите уровень сложности:\n"
            "/easy - Лёгкий уровень\n"
            "/medium - Средний уровень\n"
            "/hard - Сложный уровень"
        )

        # Положительный тест: текст содержит команды
        called_text = mock_update.message.reply_text.call_args[0][0]
        self.assertIn("/easy", called_text)
        self.assertIn("/medium", called_text)

        # Отрицательный тест: Update без message
        mock_update.message = None
        with self.assertRaises(AttributeError):
            await start(mock_update, mock_context)

        # Отрицательный тест: Context без метода reply_text
        mock_update.message = MagicMock()
        mock_update.message.reply_text = None
        with self.assertRaises(TypeError):
            await start(mock_update, mock_context)

    async def test_get_task(self):
        """
        Тесты для функции get_task.

        Положительные:
        - Задача отправляется корректно.
        - Уровень сложности соответствует выбранному.

        Отрицательные:
        - Команда содержит неверный уровень сложности.
        - JSON-файл задач пуст.
        """
        mock_update = MagicMock()
        mock_update.message.text = "/easy"
        mock_update.message.reply_text = AsyncMock()
        mock_context = AsyncMock()
        mock_context.user_data = {}

        # Положительный тест: корректная задача для уровня easy
        tasks = [{"level": "легкий", "task": "Напишите функцию.", "function_name": "test_func", "test_cases": []}]
        with unittest.mock.patch("your_module.tasks", tasks):
            await get_task(mock_update, mock_context)
            mock_update.message.reply_text.assert_called_once_with(
                "Задача (легкий уровень):\nНапишите функцию.\n\n"
                "После написания решения отправьте его кодом. Ожидается функция с именем: test_func."
            )

        # Положительный тест: пользовательский контекст сохраняет задачу
        self.assertIn("current_task", mock_context.user_data)

        # Отрицательный тест: неверный уровень сложности
        mock_update.message.text = "/invalid"
        await get_task(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_with("Неверная команда. Используйте /easy, /medium или /hard.")

        # Отрицательный тест: задачи отсутствуют
        with unittest.mock.patch("your_module.tasks", []):
            await get_task(mock_update, mock_context)
            mock_update.message.reply_text.assert_called_with("Для уровня лёгкий пока нет задач.")

    async def test_solve(self):
        """
        Тесты для функции solve.

        Положительные:
        - Код пользователя проходит все тесты.
        - Сообщение об успешной проверке отправляется.

        Отрицательные:
        - Код пользователя не проходит тесты.
        - Код содержит синтаксическую ошибку.
        """
        mock_update = MagicMock()
        mock_update.message.text = "def test_func(a, b): return a + b"
        mock_update.message.reply_text = AsyncMock()
        mock_context = AsyncMock()
        mock_context.user_data = {
            "current_task": {
                "function_name": "test_func",
                "test_cases": [
                    {"input": "(1, 2)", "output": 3},
                    {"input": "(3, 5)", "output": 8}
                ]
            }
        }

        # Положительный тест: успешное выполнение тестов
        await solve(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with("Поздравляю! Все тесты пройдены!")

        # Отрицательный тест: код не проходит тесты
        mock_update.message.text = "def test_func(a, b): return a - b"
        await solve(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_with(
            "Тест 1 не пройден:\nВходные данные: (1, 2)\nОжидалось: 3\nПолучено: -1"
        )

        # Отрицательный тест: синтаксическая ошибка в коде
        mock_update.message.text = "def test_func(a, b): return a +"
        await solve(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_with("Ошибка выполнения вашего кода:")

class TestJsonLoading(unittest.TestCase):
    """
    Класс для тестирования загрузки JSON-файла задач.
    """
    def test_valid_json_file(self):
        """Положительный тест: корректный JSON-файл."""
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data='[{"level": "easy"}]')):
            with unittest.mock.patch("json.load", return_value=[{"level": "easy"}]):
                tasks = json.load(open("tasks.json", "r"))
                self.assertEqual(len(tasks), 1)

    def test_missing_file(self):
        """Отрицательный тест: файл отсутствует."""
        with self.assertRaises(FileNotFoundError):
            with open("missing.json", "r"):
                pass

    def test_invalid_json(self):
        """Отрицательный тест: некорректный JSON."""
        with unittest.mock.patch("builtins.open", unittest.mock.mock_open(read_data="invalid json")):
            with self.assertRaises(json.JSONDecodeError):
                json.load(open("tasks.json", "r"))

if __name__ == "__main__":
    unittest.main()
