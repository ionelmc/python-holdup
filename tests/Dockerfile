FROM buildpack-deps:bionic AS deps

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
                    python3-dev curl wget ca-certificates \
 && echo 'deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main 10' > /etc/apt/sources.list.d/pgdg.list \
 && curl -fsSL 'https://www.postgresql.org/media/keys/ACCC4CF8.asc' | apt-key add - \
 && apt-get update \
 && apt-get install -y --no-install-recommends 'libpq-dev' \
 && rm -rf /var/lib/apt/lists/*

RUN bash -o pipefail -c "curl -fsSL 'https://bootstrap.pypa.io/get-pip.py' | python3 - --no-cache-dir --upgrade pip==19.1.1"

RUN mkdir /wheels \
 && pip wheel --no-cache --wheel-dir=/wheels psycopg2==2.8.2


########################################################################################################################
FROM ubuntu:bionic
########################################################################################################################

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
                    locales software-properties-common \
                    curl wget ca-certificates gpg-agent \
                    strace gdb lsof locate net-tools htop iputils-ping dnsutils \
                    python3 python3-distutils \
                    python3-dbg libpython3-dbg \
                    nano vim tree less telnet socat \
 && echo 'deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main 10' > /etc/apt/sources.list.d/pgdg.list \
 && curl -fsSL 'https://www.postgresql.org/media/keys/ACCC4CF8.asc' | apt-key add - \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
                    libpq5 postgresql-client-10 \
 && rm -rf /var/lib/apt/lists/*

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
RUN locale-gen en_US.UTF-8

ENV TERM=xterm
RUN bash -o pipefail -c "curl -fsSL 'https://bootstrap.pypa.io/get-pip.py' | python3 - --no-cache-dir --upgrade pip==19.1.1"

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
