# syntax=docker/dockerfile:1.2.1
FROM alpine:latest as dist

RUN apk add --no-cache --virtual build-deps gcc python3-dev musl-dev py3-pip py3-wheel postgresql-dev
RUN mkdir -p /build/dist
WORKDIR /build
RUN pip wheel --wheel-dir=dist psycopg[c]
ADD . /build
RUN python3 setup.py bdist_wheel

FROM alpine:latest
RUN apk add --no-cache py3-pip libpq
RUN --mount=type=bind,from=dist,src=/build/dist,target=/dist \
    pip install --break-system-packages /dist/*

ENTRYPOINT ["holdup"]
