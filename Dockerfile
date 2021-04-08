# syntax=docker/dockerfile:1.2.1

FROM alpine:latest as dist
RUN apk add --no-cache py3-pip py3-wheel
ADD . /build
WORKDIR /build
RUN python3 setup.py bdist_wheel

FROM alpine:latest
RUN apk add --no-cache py3-pip
RUN --mount=type=bind,from=dist,src=/build/dist,target=/dist \
    pip install /dist/*

ENTRYPOINT ["holdup"]
