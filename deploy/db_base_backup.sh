#!/bin/bash
set -e

# Файл для сравления с файлами логов
touch /backup/backup_start_trigger

mv /backup/base_backup.tar.gz /backup/base_backup.tar.gz_bk

# Делаем базовый бэкап
pg_basebackup --pgdata=- \
    --format=tar --gzip \
    --wal-method=none --progress \
    --username=postgres > /backup/base_backup.tar.gz

# Удалим не нужные wal-файлы, более старые чем запуск бэкапа
find /backup/wal/ \
    -type f -not -newer /backup/backup_start_trigger \
    -delete

# Подчищаем за собой
rm /backup/base_backup.tar.gz_bk
rm /backup/backup_start_trigger