#!/usr/bin/env bash
set -e

HOST="$1"
PORT="$2"
shift 2
CMD="$@"

# Check arguments
if [ -z "$HOST" ] || [ -z "$PORT" ]; then
  echo "Usage: wait-for.sh <host> <port> [command to run]"
  exit 1
fi

echo "Waiting for $HOST:$PORT to be available..."

until nc -z "$HOST" "$PORT"; do
  sleep 1
done

echo "$HOST:$PORT is up!"

exec $CMD
