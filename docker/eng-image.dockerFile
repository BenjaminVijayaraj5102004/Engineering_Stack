FROM python:3.12-slim


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


WORKDIR /app


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src" \
    UV_SYSTEM_PYTHON=1


COPY requirements.txt /app/requirements.txt

RUN uv pip install --system --no-cache -r requirements.txt


COPY pyproject.toml README.md /app/
COPY src/ /app/src/


RUN uv pip install --system --no-cache -e .


CMD ["python3"]