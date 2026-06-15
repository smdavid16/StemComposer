#!/bin/bash

echo "Cream mediul virtual..."
python3 -m venv venv
if [ ! -d "venv" ]; then
    echo "Eroare: Mediul virtual (venv) nu a putut fi creat."
    echo "Te rog instaleaza python3-venv in WSL ruland:"
    echo "sudo apt update && sudo apt install -y python3-pip python3-venv redis-server"
    exit 1
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install python-dotenv google-genai django celery redis djangorestframework

echo "Pornim Redis..."
if command -v service >/dev/null 2>&1; then
    sudo service redis-server start
else
    sudo systemctl start redis-server
fi

echo "Aplicam migratiile bazei de date..."
python3 manage.py makemigrations
python3 manage.py migrate

echo "Verificam si construim imaginea Docker 'stemcomposer' (daca au aparut modificari)..."
docker build -t stemcomposer -f dockerfile .

echo "Pornim Celery worker..."
celery -A core worker --loglevel=warning &

echo "Pornim serverul Django..."
python3 manage.py runserver

