FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    NLTK_DATA=/usr/local/nltk_data

RUN apt-get update \
  && apt-get install -y --no-install-recommends bash ca-certificates curl build-essential gcc \
  && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash bot \
  && mkdir -p /app \
  && chown -R bot:bot /app

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
  && pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN sed -i '1s/^\xEF\xBB\xBF//' /app/entrypoint.sh \
 && sed -i 's/\r$//' /app/entrypoint.sh \
 && chmod +x /app/entrypoint.sh \
 && chown -R bot:bot /app

RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

USER bot

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
