#!/usr/bin/env bash

env PYTHONPATH="." python3 -m pytest \
  CrunchyRest/test \
  CrunchyRest/*/tests.py \
  --ignore=CrunchyRest/test/test_Currency.py \
  "$@"
