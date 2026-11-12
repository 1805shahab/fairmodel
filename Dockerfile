# Both build stages use Debian Bookworm so the Node binary's runtime ABI matches.
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
COPY postman/ /build/postman/
# This is a public deployment notice, never an API key or access password.
ENV NEXT_TELEMETRY_DISABLED=1 NEXT_PUBLIC_HOSTED_EPHEMERAL_DEMO=true FAIRMODEL_STANDALONE=true
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=frontend-build /usr/local/bin/node /usr/local/bin/node
WORKDIR /opt/fairmodel
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app/ ./backend/app/
COPY --from=frontend-build /build/frontend/.next/standalone/ ./frontend/
COPY --from=frontend-build /build/frontend/.next/static/ ./frontend/.next/static/
COPY --from=frontend-build /build/frontend/public/ ./frontend/public/
COPY postman/ ./postman/
COPY deploy/render_start.py ./deploy/render_start.py
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production HOSTED_DEMO=true BACKEND_URL=http://127.0.0.1:8000 \
    DATABASE_URL=sqlite:////tmp/fairmodel/fairmodel.db STORAGE_DIR=/tmp/fairmodel/storage \
    APP_ENV=development DEMO_MODE=true PAYMENT_PROVIDER=paypal_sandbox \
    PAYPAL_ENVIRONMENT=sandbox PAYPAL_ALLOW_DRAFTS=false PAYPAL_ALLOW_SENDING=false \
    ENABLE_SPEAKER_VERIFICATION=false ENABLE_VOICE_GENERATION=false ENABLE_FISH_GENERATION=false
EXPOSE 10000
CMD ["python", "/opt/fairmodel/deploy/render_start.py"]
