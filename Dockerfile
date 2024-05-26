FROM python:3.10-alpine

LABEL org.opencontainers.image.source="https://github.com/felixschndr/mealie-bring-api"
LABEL org.opencontainers.image.description="The container image of the mealie bring api integration (https://github.com/felixschndr/mealie-bring-api)"

WORKDIR /app

EXPOSE 8742/tcp

COPY source/*.py .
COPY source/requirements.txt .

RUN pip install -r requirements.txt

CMD python main.py
