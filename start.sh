#!/bin/bash
set -e

PORT="${PORT:-8080}"
API_PORT="${API_PORT:-8005}"

echo "=== Starting Apexify ==="
echo "Main port: $PORT (Nginx → Frontend + API)"
echo "API internal port: $API_PORT"

# Start FastAPI backend (internal, not exposed directly)
uvicorn api.main:app \
  --host 127.0.0.1 \
  --port "$API_PORT" \
  --workers 2 \
  --log-level info &

API_PID=$!
echo "API started (PID: $API_PID)"

# Wait for API to be ready
for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:$API_PORT/api/health > /dev/null 2>&1; then
    echo "API is ready"
    break
  fi
  sleep 1
done

# Start Next.js frontend (exposed on $PORT)
cd /app/frontend
API_URL="http://127.0.0.1:$API_PORT" PORT="$PORT" node node_modules/.bin/next start &

NEXT_PID=$!
echo "Frontend started (PID: $NEXT_PID)"

# Health check endpoint for Railway
# Next.js handles all requests including /api/* (proxied to FastAPI)

# Wait for either process to exit
wait -n $API_PID $NEXT_PID
echo "A process exited, shutting down..."
kill $API_PID $NEXT_PID 2>/dev/null
exit 1
