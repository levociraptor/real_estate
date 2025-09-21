Для запуска приложения нужно:
1. Заполнить .env файл про примеру .env.example файла
2. Запустить контейнеры командой docker compose up --build
3. Запустить миграции командой docker-compose exec web alembic upgrade head