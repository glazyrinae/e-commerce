FROM python:3.12
ENV DEBIAN_FRONTEND noninteractive

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get -yq update \
    && apt-get -yq install build-essential libffi-dev poppler-utils supervisor \
    && apt-get purge -y --auto-remove

COPY ./requirements.txt /requirements.txt

RUN pip install uv
RUN pip install --upgrade pip
RUN uv pip install --system --no-cache-dir -r /requirements.txt