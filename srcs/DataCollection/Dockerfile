FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install runtime packages with cache mount
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
	iputils-ping \
    openssh-client \
    sshpass \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Disable OpenSSL security level restrictions for legacy compatibility
ENV OPENSSL_CONF="~/openssl_legacy.conf"

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Copy application files
COPY BashGetInfo.sh TopUsers.sh start-cron.sh ./
COPY *.py ./
COPY crontab /etc/cron.d/datacollection-crontab

# Set permissions and configure cron in one layer
RUN chmod +x BashGetInfo.sh TopUsers.sh start-cron.sh && \
    mkdir -p /var/log && \
    chmod 0644 /etc/cron.d/datacollection-crontab && \
    crontab /etc/cron.d/datacollection-crontab

CMD ["./start-cron.sh"]