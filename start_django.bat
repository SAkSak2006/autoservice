@echo off
title Django Server
cd /d "C:\Users\allak\Desktop\Lerning\dIPLOM ilia\autoservice"
venv\Scripts\python manage.py runserver 0.0.0.0:8000 --settings=autoservice.settings.dev
pause
