# Bot-notifier in Telegram

Telegram-бот, рассылающий уведомления о статусе домашней работы в Яндекс.Практикуме.

Уведомления приходят только при изменении статуса домашней работы.
Период опроса API Практикума 60 секунд.
Работа бота логгируется. О критических сбоях бот также сообщает в чате.  

Быстрый старт:

Создать и активировать виртуальное окружение:
> $ python -m venv venv \
> $ source venv/Scripts/activate 

Установить зависимости из файла requirements.txt:
> $ pip install -r requirements.txt
   
В файл .env Добавить токен для API Практикум Домашка, токен Telegram-бота и ID Telegram чата. 

Запустить бота: 
> $ python homework.py

Готово!

---
Telegram bot that notifies you about your homework status.

Quick start:
Create and activate virtual environment:
> $ python -m venv venv \
> $ source venv/Scripts/activate

Install required packages from requirements.txt: 
> $ pip install -r requirements.txt
   
Add your tokens in .env: Practicum token, Telegram Bot token, Telegram Chat ID.

Enjoy!
