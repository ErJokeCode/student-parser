# Student-Voice-Backend
Backend of student voice of the pairs evaluation project


## Содержание
- [Технологии](#Технологии)
- [Начало работы](#Начало-работы)

## Технологии
- [FAST API](https://fastapi.tiangolo.com/)
- [MongoDB]()

## Начало работы

### Первая сборка и запуск
Для запустка потребуется [Docker](https://www.docker.com/) 

Склонируйте репозиторий себе на ПК с помощью команды: 
```sh
$ git clone ...
```

Создать файл .env по примеру 

```sh
CORS=<*, http://localhost, http://127.0.0.1> 

MY_URL=<http://localhost:8000>

URL_CORE_SERVER=<http://core:5000>
CORE_SERVER_SECRET_TOKEN=<123>

MGO_HOST=<parserdb>
MGO_PORT=<27017>
MGO_NAME_DB=<personal-mailing>

MINIO_ROOT_USER=<minioadmin>
MINIO_ROOT_PASSWORD=<minioadmin>
MINIO_URL=<http://minio:9000>
MINIO_BUCKET_NAME=<test>
```


Соберите и запустите проект с помощью docker:
```sh
$ docker-compose up --build -d
```

Для первого запуска необходимо создать бакет в minio
```sh
$ docker exec ... make first-start #где ... название контейнера с парсером (student-parser-parser-1)
```

### API

Проверить работу api можно на http://localhost:8000/docs#
