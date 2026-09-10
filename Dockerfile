FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir uv==0.5.11

WORKDIR /app

# Bağımlılıklar önce (katman önbelleği)
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system --no-cache .

RUN useradd --system --uid 10001 --create-home yusha
USER yusha

ENTRYPOINT ["python", "-m", "yusha"]
