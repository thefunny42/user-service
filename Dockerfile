# syntax=docker/dockerfile:1

FROM python:3.12-alpine as base

WORKDIR /app

FROM base as dev

RUN apk add zsh pipx gcc linux-headers musl-dev shadow
RUN addgroup --system --gid 1000 python
RUN adduser --system --uid 1000 -G python python
RUN chsh -s /bin/zsh python

USER 1000:1000
RUN PIPX_DEFAULT_PYTHON=/usr/local/bin/python3 pipx install hatch coverage

EXPOSE 8000

FROM base as final

RUN /usr/local/bin/python3 -m venv /app
RUN --mount=type=bind,source=.,target=src,rw  \
    --mount=type=cache,target=/root/.cache \
    cd src && pip install -r requirements.txt .

RUN addgroup --system --gid 1000 python
RUN adduser --system --uid 1000 -G python -H python
COPY logging.yaml .

ENV USER_SERVICE_LOG "logging.yaml"
USER 1000:1000

EXPOSE  8000

CMD ["/app/bin/user-service"]
