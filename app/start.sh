set -e

sanic app.main:app \
    --host=0.0.0.0 \
    --port=80 \
    --workers=4 \
    --reload \
    --reload-dir=./app \
    --dev
