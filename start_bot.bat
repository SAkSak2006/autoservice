@echo off
title Telegram Bot
cd /d "C:\Users\allak\Desktop\Lerning\dIPLOM ilia\autoservice"
venv\Scripts\python manage.py run_telegram_bot --settings=autoservice.settings.dev
pause
