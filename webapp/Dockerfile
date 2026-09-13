FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[webapp]"

COPY webapp ./webapp
COPY examples ./examples

EXPOSE 8000
CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
