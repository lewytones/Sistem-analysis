# Multi-stage build для оптимизации размера образа

# Стадия 1: Сборка зависимостей
FROM python:3.11-slim as builder

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Создание виртуального окружения и установка зависимостей
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Стадия 2: Рабочий образ
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование виртуального окружения из стадии сборки
COPY --from=builder /opt/venv /opt/venv

# Активация виртуального окружения
ENV PATH="/opt/venv/bin:$PATH"

# Копирование приложения
COPY . .

# Создание пользователя для безопасности
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]