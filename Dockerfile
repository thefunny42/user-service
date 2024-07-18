# syntax=docker/dockerfile:1

FROM python:3.12-alpine AS base

WORKDIR /app

RUN mkdir /app/conf

FROM base AS dev

RUN apk add --no-cache zsh pipx gcc linux-headers musl-dev shadow
RUN addgroup --system --gid 1000 python
RUN adduser --system --uid 1000 -G python python
RUN chsh -s /bin/zsh python

USER 1000:1000
RUN PIPX_DEFAULT_PYTHON=/usr/local/bin/python3 pipx install hatch coverage

EXPOSE 8000

FROM base AS final

RUN /usr/local/bin/python3 -m venv /app
RUN --mount=type=bind,source=.,target=src,rw  \
    --mount=type=cache,target=/root/.cache \
    cd src && /app/bin/pip install -r requirements.txt .

RUN addgroup --system --gid 1000 python
RUN adduser --system --uid 1000 -G python -H python

USER 1000:1000

EXPOSE  8000

CMD ["/app/bin/user-service"]
