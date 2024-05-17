FROM python:3.10-alpine

WORKDIR /app

EXPOSE 8742/tcp

COPY source/*.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD python main.py
