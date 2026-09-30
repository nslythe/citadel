FROM python:3.14

RUN mkdir /app

COPY citadel /app/citadel
COPY main.py /app
COPY requirements.txt /app

WORKDIR /app

RUN python -m pip install -r requirements.txt

CMD ["python", "-u", "main.py"]