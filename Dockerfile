FROM python:3.13.2

RUN python3 -m pip install --upgrade pip

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY . .