FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 for Next.js frontend
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements-api.txt .
RUN pip install --upgrade pip && pip install -r requirements-api.txt

# Copy backend code
COPY core/ core/
COPY services/ services/
COPY api/ api/
COPY web/ web/
COPY run_api.py .
COPY app.py .
COPY static/ static/

# Build Next.js frontend
COPY frontend/ frontend/
WORKDIR /app/frontend
RUN npm ci && npm run build
WORKDIR /app

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8080

CMD ["./start.sh"]
