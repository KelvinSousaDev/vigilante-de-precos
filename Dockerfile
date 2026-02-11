FROM python:3.12-slim AS builder
RUN apt-get update && apt-get install -y \
    gcc
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN playwright install chromium --with-deps
COPY src/ .
CMD ["python", "main.py"]