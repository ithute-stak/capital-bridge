#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -f .env ]]; then
  echo "Missing deploy/docker/.env; copy .env.example and set private credentials." >&2
  exit 2
fi
set -a
# Read only the image tag without executing untrusted .env shell contents.
CB_IMAGE_TAG="$(sed -n 's/^CB_IMAGE_TAG=//p' .env | tail -n 1)"
set +a
if [[ ! "${CB_IMAGE_TAG}" =~ ^sha-[0-9a-f]{40}$ ]]; then
  echo "CB_IMAGE_TAG must be a published sha- followed by 40 lowercase hex characters." >&2
  exit 2
fi
export CB_IMAGE_TAG
docker compose --env-file .env -f compose.yaml config --quiet
docker compose --env-file .env -f compose.yaml pull
docker compose --env-file .env -f compose.yaml up -d --remove-orphans
docker compose --env-file .env -f compose.yaml ps
echo "Checking CapitalBridge public API health on loopback..."
curl --fail --silent --show-error --max-time 15 http://127.0.0.1:8204/health
echo
echo "Checking CapitalBridge static site on loopback..."
curl --fail --silent --show-error --max-time 15 -o /dev/null http://127.0.0.1:3204/
echo "Containers refreshed. Configure TLS and test public origin before claiming launch."
