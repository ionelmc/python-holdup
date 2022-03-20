#!/bin/bash -eux

docker-compose --ansi=never down || true
docker-compose --ansi=never build --pull

trap "docker-compose --ansi=never down" EXIT

for try in {1..10}; do
    echo "Trial #$try"
    docker-compose --ansi=never down || true
    docker-compose --ansi=never up test  # so networks are created without race condition
    (sleep 5; docker-compose --ansi=never up --detach pg) &  # start pg later than usual
    docker-compose --ansi=never run --entrypoint "$*" test /test_pg.py || exit 1
done
echo "success !"
