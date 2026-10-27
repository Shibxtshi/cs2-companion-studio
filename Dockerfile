FROM python:3.12-slim@sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY companion ./companion
COPY static ./static
COPY scripts/recover_profiles.py ./scripts/recover_profiles.py
RUN mkdir -p /app/data /app/logs && chown -R 10001:10001 /app/data /app/logs
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8080/health',timeout=2).close()" || exit 1
CMD ["uvicorn", "companion.server:app", "--host", "0.0.0.0", "--port", "8080", "--no-server-header", "--no-access-log", "--ws-max-size", "262144", "--ws-max-queue", "8"]
