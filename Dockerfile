FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY configuration ./configuration
COPY src ./src

RUN pip install --no-cache-dir . \
    && useradd --create-home --shell /usr/sbin/nologin myvcs \
    && chown -R myvcs:myvcs /app

USER myvcs

ENTRYPOINT ["myvcs"]
