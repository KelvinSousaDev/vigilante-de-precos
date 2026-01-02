FROM python:3.12-slim
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "dashboard.py", "server.port=8501", "server.address=0.0.0.0"] 