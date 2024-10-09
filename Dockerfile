# Базовый образ
FROM python:3.12
# Устанавливаем рабочий каталог
WORKDIR /app
# Устанавливаем poetry и uvicorn
RUN python -m pip install poetry uvicorn
# Копируем файлы с зависимостями
COPY pyproject.toml poetry.lock ./
# Устанавливаем зависимости
RUN poetry install
# Копируем shop_api
COPY ./ ./
# Вытаскиваем наружу 8000 порт
EXPOSE 8000
# Запускаем сервер
CMD [ "poetry", "run", "uvicorn", "lecture_2.hw.shop_api.main:app" ]
