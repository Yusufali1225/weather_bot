# ==== Base image ====
FROM python:3.11-slim

# ==== Working directory ====
WORKDIR /app

# ==== Copy project files ====
COPY . /app

# ==== Install dependencies ====
RUN pip install --no-cache-dir -r requirements.txt

# ==== Environment variables ====
ENV PYTHONUNBUFFERED=1

# ==== Run bot ====
CMD ["python3", "bot.py"]
