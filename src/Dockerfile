# pull official base image
FROM python:3.11.4-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .

ARG options
ENV OPTIONS $options
#ENV DJANGO_SETTINGS_MODULE=simple.settings
CMD exec gunicorn $OPTIONS --bind :8000 --workers 1 --threads 8 --timeout 0 ecommerce.wsgi:application