#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install django celery redis djangorestframework

echo "Pornim Redis, Celery si Django..."
sudo systemctl start redis-server

echo "Aplicam migratiile bazei de date..."
python3 manage.py makemigrations
python3 manage.py migrate

celery -A core worker --loglevel=warning &

python3 manage.py runserver
