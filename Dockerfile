# ══════════════════════════════════════════════════════════════
# GrowthCRO Pipeline — Docker image (Python + Playwright)
#
# Build :
#   docker build -t growthcro .
#
# Run (mode local — navigateur Chromium embarqué dans le container) :
#   docker run --rm growthcro python3 capture_full.py https://japhy.fr japhy ecommerce
#
# Run (mode cloud — navigateur distant via Browserless.io) :
#   docker run --rm -e BROWSER_WS_ENDPOINT="wss://chrome.browserless.io?token=XXX" \
#     growthcro python3 capture_full.py https://japhy.fr japhy ecommerce --cloud
#
# Run (API server) :
#   docker run --rm -p 8000:8000 \
#     -e BROWSER_WS_ENDPOINT="wss://chrome.browserless.io?token=XXX" \
#     -e ANTHROPIC_API_KEY="sk-ant-..." \
#     growthcro python3 api_server.py
#
# ══════════════════════════════════════════════════════════════

FROM python:3.12-slim

# System deps for Playwright (Chromium) — needed only for local mode
# In cloud mode, only the Python library is needed (no browser binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser (for local mode)
# Skip this if you'll ONLY use cloud mode (reduces image size by ~400MB)
RUN playwright install chromium

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/captures data/golden

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python3 -c "import playwright; print('ok')" || exit 1

# Default: API server on port 8000
EXPOSE 8000
CMD ["python3", "api_server.py"]
