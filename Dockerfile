FROM python:3.14-alpine AS builder

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --only main --no-root


FROM python:3.14-alpine

LABEL org.opencontainers.image.source="https://github.com/felixschndr/mealie-bring-api"
LABEL org.opencontainers.image.description="The container image of the mealie bring api integration (https://github.com/felixschndr/mealie-bring-api)"

WORKDIR /app

EXPOSE 8742/tcp

COPY --from=builder /app/.venv/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY source/ source/

CMD ["python", "-m", "source.mealie_bring_api"]
