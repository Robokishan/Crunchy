#!/bin/bash
set -e
if [ -n "$1" ]; then
  bash pull.sh "$1"
  bash up.sh "$1"
else
  bash pull.sh
  bash up.sh
fi
docker image prune -a -f
