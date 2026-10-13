FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
COPY agents/ ./agents/
COPY polypharmacy_deprescribing_agent/ ./polypharmacy_deprescribing_agent/
RUN python -m pip install --no-cache-dir '.[api]'
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["python", "cli.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
