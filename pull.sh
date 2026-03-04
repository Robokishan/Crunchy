#!/bin/bash
if [ -n "$1" ]; then
  docker compose --env-file .env.prod -f docker-compose.prod.yml pull "$1"
else
  docker compose --env-file .env.prod -f docker-compose.prod.yml pull
fi
