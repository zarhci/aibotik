# Используем стабильный и лёгкий Python
FROM python:3.11-slim

# Отключаем лишнее
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости (минимум)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Запуск бота
CMD ["sh", "-c", "python bot.py & python watchdog.py"]

