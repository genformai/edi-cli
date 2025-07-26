FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY . .

CMD ["poetry", "run", "uvicorn", "packages.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
