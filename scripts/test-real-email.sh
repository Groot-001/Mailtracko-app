#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

./scripts/validate-environment.sh
read -r -p "Enter the REAL email inbox that should receive the MailTracko test email: " recipient
if [[ ! "$recipient" =~ ^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$ ]]; then
  echo "Recipient email format is invalid." >&2
  exit 1
fi

echo "Ensuring the MailTracko API is running..."
docker compose up -d --build api

echo "Sending one real transactional email through MailTracko's transactional email adapter..."
docker compose exec -T api python -m scripts.test_transactional_email --recipient "$recipient"
echo "Check the real inbox (and Spam/Promotions if needed). No local SMTP catcher is used."
