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

# System deps needed by Playwright/Chromium
RUN apt-get update && apt-get install -y \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 \
    libpango-1.0-0 libcairo2 libx11-6 libx11-xcb1 \
    libxcb1 libxext6 fonts-liberation wget \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright's Chromium browser
RUN python -m playwright install chromium

COPY app.py scraper.py notifier.py ./
COPY --from=frontend-build /build/static ./static/

EXPOSE 5050

CMD ["python", "app.py"]
