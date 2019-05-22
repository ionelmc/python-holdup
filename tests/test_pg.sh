#!/bin/bash -eux

cd tests

docker-compose build

trap "docker-compose down" EXIT

while docker-compose run test; do
    docker-compose down
done
