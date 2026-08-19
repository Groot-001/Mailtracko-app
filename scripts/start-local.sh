#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
./scripts/validate-environment.sh
docker compose up -d --build
docker compose ps
echo "MailTracko is starting at http://127.0.0.1:3000"
