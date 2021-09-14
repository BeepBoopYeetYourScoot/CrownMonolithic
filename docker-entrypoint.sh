#!/bin/sh
pip install djangorestframework drf-yasg django-cors-headers channels

pip install -r requirements.txt

python3 manage.py collectstatic --no-input && python3 manage.py makemigrations authorization game websockets && python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000