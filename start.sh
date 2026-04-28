#!/bin/bash
echo "Pornim Redis, Celery si Django..."
sudo systemctl start redis-server
source venv/bin/activate

celery -A core worker --loglevel=warning &

python3 manage.py runserver