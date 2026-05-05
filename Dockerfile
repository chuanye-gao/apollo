FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY apollo/__init__.py apollo/

RUN pip install --no-cache-dir -e ".[serve]"

COPY . .

ENV APOLLO_EMBEDDING=hash
ENV APOLLO_LLM_MODE=dry-run

EXPOSE 8000

CMD ["uvicorn", "apollo.server:app", "--host", "0.0.0.0", "--port", "8000"]
