#!/bin/bash -eux

docker-compose build

trap "docker-compose down" EXIT

for try in {1..10}; do
    docker-compose down || true
    docker-compose run --entrypoint "$*" test /test_pg.py || exit 1
done
echo "success !"
