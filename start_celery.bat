@echo off
title Celery Worker
cd /d "C:\Users\allak\Desktop\Lerning\dIPLOM ilia\autoservice"
venv\Scripts\celery -A autoservice worker --loglevel=info
pause
