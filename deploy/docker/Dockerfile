FROM node:20-bookworm-slim AS web-builder

WORKDIR /build/web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    STATIC_DIR=/app/static \
    DATA_DIR=/app/data

WORKDIR /app

COPY requirements/runtime.txt ./requirements/runtime.txt
RUN pip install --no-cache-dir -r requirements/runtime.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY backend/ ./backend/
RUN pip install --no-cache-dir --no-deps --no-build-isolation ./backend

COPY alembic.ini ./alembic.ini
COPY backend/alembic/ ./backend/alembic/

COPY --from=web-builder /build/web/dist ./static/
RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /app/data \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn docnexus.main:app --host 0.0.0.0 --port 8000"]
