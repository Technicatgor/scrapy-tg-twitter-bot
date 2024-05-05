FROM python:3.9-slim

WORKDIR /app

RUN apt update && apt install cron -y

COPY requirements.txt .

RUN pip install -r requirements.txt


COPY . .

COPY --chmod=0644 ./crontab /etc/cron.d/server-cron

RUN crontab /etc/cron.d/server-cron

CMD ["cron", "-f", "/etc/cron.d/server-cron"]
