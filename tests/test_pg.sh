#!/bin/bash -eux

docker-compose --no-ansi down || true
docker-compose --no-ansi build

trap "docker-compose --no-ansi down" EXIT

for try in {1..10}; do
    echo $try
    docker-compose --no-ansi down || true
    docker-compose --no-ansi up test  # so networks are created without race condition
    (sleep 5; docker-compose --no-ansi up --detach pg) &  # start pg later than usual
    docker-compose --no-ansi run --entrypoint "$*" test /test_pg.py || exit 1
done
echo "success !"
