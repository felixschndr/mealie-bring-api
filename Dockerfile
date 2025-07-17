FROM python:3.12-alpine

LABEL org.opencontainers.image.source="https://github.com/felixschndr/mealie-bring-api"
LABEL org.opencontainers.image.description="The container image of the mealie bring api integration (https://github.com/felixschndr/mealie-bring-api)"

WORKDIR /app

EXPOSE 8742/tcp

COPY source/*.py .
COPY pyproject.toml .
COPY poetry.lock .

RUN pip install poetry && \
    POETRY_VIRTUALENVS_CREATE=false poetry install && \
    pip uninstall -y poetry

CMD python main.py
