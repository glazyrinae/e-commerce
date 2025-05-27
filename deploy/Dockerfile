FROM python:3.12
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -yq update \
    && apt-get -yq install build-essential libffi-dev poppler-utils supervisor \
    && apt-get purge -y --auto-remove

COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir --upgrade -r /requirements.txt