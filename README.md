# 🥗Foodgram — веб-сервис для обмена рецептами

[![Python](https://img.shields.io/badge/Python-blue?logo=python&logoColor=yellow)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-009639?logo=drf&logoColor=white)](https://www.django-rest-framework.org/)
[![Docker](https://img.shields.io/badge/Docker-blue?logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-gray?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)](https://nginx.org/)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-black?logo=gunicorn&logoColor=white)](https://gunicorn.org/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-blue?logo=github-actions&logoColor=white)](https://docs.github.com/en/actions)

**FoodGram** — это веб-приложение, где пользователи могут публиковать рецепты,  
добавлять их в избранное, формировать список покупок и искать по ингредиентам.  
Фронт и бэк собраны на Docker, запуск осуществляется в прод-окружении с Nginx и Gunicorn.

---

## 🌐 Демо-версия

Проект доступен по адресу:  
**https://foodgrammy.hopto.org**

---

## 🛠️ Стек технологий

- Python + Django + Django REST Framework
- Djoser — для регистрации и авторизации пользователей
- PostgreSQL — основная база данных
- Docker — контейнеризация
- Gunicorn + Nginx — прод-обёртка
- GitHub Actions — CI/CD

---

## ⚙️ Основной функционал

- Авторизация и регистрация через Djoser (token-based)
- Публикация рецептов с изображениями
- Добавление рецептов в избранное
- Подписка на авторов
- Формирование списка покупок и скачивание в txt
- Поиск рецептов по названию и ингредиентам
- Панель администратора Django

---

## 📦 Установка и запуск проекта

### 🔧 Клонирование

```bash
git clone git@github.com:revoltkir/foodgram.git
```
создайте .env
```commandline
пример заполнения .env
POSTGRES_DB=postgres
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=postgres_password
DB_HOST=db
DB_PORT=1111

SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

```

```bash
docker-compose -f docker-compose.production.yml up -d
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
docker-compose -f docker-compose.production.yml exec backend python manage.py load_ingredients
```

##### 🧑‍Автор проекта Кирилл Тикач 
###### 🔗 DockerHub: docker.io/revoltkir 
