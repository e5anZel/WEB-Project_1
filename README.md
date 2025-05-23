![image](https://github.com/user-attachments/assets/f8d99fe0-9c9b-4caa-bf07-bc1e547f88b3)![image](https://github.com/user-attachments/assets/e2345d91-464e-4b8d-95d6-43dab599fe10)![image](https://github.com/user-attachments/assets/371213b7-607c-4748-9c77-8ac0d54ed8c6)![image](https://github.com/user-attachments/assets/c0444b22-f4ed-47e3-889f-f54e22722040)♟ Chess Telegram Bot

Умный шахматный бот для Telegram с поддержкой игры против ИИ и реальных игроков. 
Интеграция с Stockfish для профессионального анализа позиций.

=== Возможности ===

- Режимы игры: против бота или другого игрока
- ИИ на базе Stockfish (глубина анализа до 14 полуходов)
- Интерактивная доска с кнопочным управлением
- Подсказки лучших ходов в реальном времени
- Система статистики (победы/поражения/ничьи)
- Генерация графического представления доски
- Валидация ходов и обработка всех шахматных правил
- Поддержка текстового ввода ходов (например, e2e4)

=== Технологический стек ===

• Python 3.10+ - основной язык разработки
• Aiogram 3.x - фреймворк для Telegram ботов
• chess.py - обработка шахматной логики
• Stockfish - движок для анализа позиций
• SQLAlchemy - работа с базой данных
• Pillow - генерация изображений доски

=== Установка и настройка ===

1. Установить зависимости:
pip install -r requirements.txt

2. Создать config.ini со следующим содержанием:
[Settings]
API_TOKEN = ваш_токен_бота
STOCKFISH_PATH = путь_к_stockfish
DATABASE_URL = sqlite:///database.db

3. Запустить бота:
python main.py

=== Примеры использования ===

Главное меню:
- Кнопки выбора режима игры
- Доступ к статистике и правилам

Игровой процесс:
- Интерактивная шахматная доска
- Подсветка последнего хода
- Кнопки сдачи и подсказок

Статистика:
- Таблица с результатами игр
- Процентное соотношение побед/поражений
=== Примеры использования ===
![image](https://github.com/user-attachments/assets/916aaf72-b7c3-4b61-ac13-df219e32af68)
![image](https://github.com/user-attachments/assets/12ff51b1-ed0a-49e2-b169-051e84df1fe3)
![image](https://github.com/user-attachments/assets/ff7592c7-e574-499f-9cc6-31e3e9a00fb6)
![image](https://github.com/user-attachments/assets/f22fb2b9-a93a-4b95-b21d-362b616725de)
![image](https://github.com/user-attachments/assets/c391869e-423a-4ef4-bd66-d0ac19490cda)
![image](https://github.com/user-attachments/assets/742a071e-6d5b-4940-bf6b-06c91693db0c)
![image](https://github.com/user-attachments/assets/67f8daf2-0f4b-4858-a33e-ffee627020f5)
![image](https://github.com/user-attachments/assets/c4c11f78-0288-4cea-b6fd-6cbd98fcbbb0)
![image](https://github.com/user-attachments/assets/16922723-e786-4388-8840-c3025ec6478d)
![image](https://github.com/user-attachments/assets/fec5fa75-ed0c-4928-8328-92fedfdaa0c7)

=== Контакты ===
Автор: Зеливан


