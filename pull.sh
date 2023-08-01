#!/bin/bash
docker compose --env-file .env.prod -f docker-compose.prod.yml pull
