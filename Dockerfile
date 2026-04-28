# Stage 1: Build React frontend
FROM node:22-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# Build output goes to /build/static (because outDir is ../static)

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium + ALL system dependencies automatically
RUN python -m playwright install --with-deps chromium

COPY app.py scraper.py notifier.py ./
COPY --from=frontend-build /build/static ./static/

EXPOSE 5050

CMD ["python", "app.py"]
