# syntax=docker/dockerfile:1
FROM buildpack-deps:20.04-scm AS deps

ENV TZ=UTC
# DEBIAN_FRONTEND=noninteractive exists to prevent tzdata going nuts.
# Maybe dpkg incorrectly detects interactive on buildkit containers?
RUN echo "deb http://apt.postgresql.org/pub/repos/apt focal-pgdg main 10" > /etc/apt/sources.list.d/pgdg.list \
 && curl -fsSL11 'https://www.postgresql.org/media/keys/ACCC4CF8.asc' | apt-key add - \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3-dev python3-distutils-extra \
        libpq-dev=10.* libpq5=10.* \
        build-essential git sudo ca-certificates
# Avoid having to use python3 all over the place.
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1

RUN bash -o pipefail -c "curl -fsSL 'https://bootstrap.pypa.io/get-pip.py' | \
    python - --no-cache --disable-pip-version-check --upgrade pip setuptools"

RUN mkdir /wheels \
 && pip wheel --no-cache --wheel-dir=/wheels psycopg2

#################
#################
FROM ubuntu:20.04
#################
RUN test -e /etc/apt/apt.conf.d/docker-clean # sanity check

ENV TZ=UTC
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl software-properties-common gpg-agent \
 && echo "deb http://apt.postgresql.org/pub/repos/apt focal-pgdg main 10" > /etc/apt/sources.list.d/pgdg.list \
 && curl -fsSL11 'https://www.postgresql.org/media/keys/ACCC4CF8.asc' | apt-key add - \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        strace gdb lsof locate net-tools htop iputils-ping dnsutils \
        nano vim tree less telnet \
        redis-tools \
        socat \
        graphviz \
        dumb-init \
        libpq5=10.* postgresql-client-10 \
        python3-dbg python3-distutils python3-distutils-extra \
        libmemcached11 \
        sudo ca-certificates \
        gdal-bin python3-gdal
# Avoid having to use python3 all over the place.
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Adds a new user named python and add it to the list of sudoers. Will be able to call sudo without the password.
# This is more geared to development (eg: match user's UID) than production (where you shouln't need any sudo/home).
RUN bash -o pipefail -c "curl -fsSL 'https://bootstrap.pypa.io/get-pip.py' | \
    python - --no-cache --disable-pip-version-check --upgrade pip==22.0.3 setuptools==60.9.3"

RUN mkdir /deps
COPY --from=deps /wheels/* /deps/
RUN pip install --force-reinstall --ignore-installed --upgrade --no-index --no-deps /deps/* \
 && rm -rf /deps \
 && mkdir /app /var/app

# Create django user, will own the Django app
RUN adduser --no-create-home --disabled-login --group --system app
RUN chown -R app:app /app /var/app

ENV PYTHONUNBUFFERED=1
RUN mkdir /project
COPY setup.* *.rst MANIFEST.in /project/
COPY src /project/src
RUN pip install /project
COPY tests/test_pg.py /

CMD ["true"]
