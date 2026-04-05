#!/usr/bin/env bash

html_output=false

if [ "${1:-}" = "html" ]; then
  if [ "${2:-}" = "true" ]; then
    html_output=true
  fi
  shift 2
fi

env PYTHONPATH="." python3 -m coverage run --branch -m pytest \
  CrunchyRest/test \
  CrunchyRest/*/tests.py \
  --ignore=CrunchyRest/test/test_Currency.py \
  "$@" && \
python3 -m coverage report -m

if [ "$html_output" = "true" ]; then
  python3 -m coverage html
fi
