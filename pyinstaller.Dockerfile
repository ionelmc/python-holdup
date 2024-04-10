FROM alpine:latest as build

RUN apk add --no-cache --virtual build-deps gcc python3-dev musl-dev py3-pip py3-wheel postgresql-dev scons patchelf
RUN mkdir -p /build/dist
WORKDIR /build
RUN pip install --break-system-packages pyinstaller psycopg[binary] staticx
ADD . /build
RUN python3 setup.py bdist_wheel
RUN pyinstaller holdup.spec
RUN staticx /build/dist/holdup /build/dist/holdup-static
RUN /build/dist/holdup --help
RUN /build/dist/holdup-static --help

FROM scratch
COPY --from=build /build/dist/holdup-static /holdup
