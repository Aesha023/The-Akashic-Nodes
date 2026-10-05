FROM python:3.11-slim AS base

# Non-root user (Section 13.7)
RUN groupadd -r pravahx && useradd -r -g pravahx -m pravahx

WORKDIR /app

# Install system dependencies for geospatial libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps
COPY pyproject.toml ./
COPY core/ ./core/
COPY backend/ ./backend/

RUN pip install --no-cache-dir -e ".[backend]"

# Switch to non-root
USER pravahx

# Read-only root filesystem compatible
EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
