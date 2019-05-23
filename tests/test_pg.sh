#!/bin/bash -eux

docker-compose down || true
docker-compose build

trap "docker-compose down" EXIT

for try in {1..10}; do
    echo $try
    docker-compose down || true
    docker-compose up test  # so networks are created without race condition
    (sleep 1; docker-compose up --detach pg) &
    docker-compose run --entrypoint "$*" test /test_pg.py || exit 1
done
echo "success !"
