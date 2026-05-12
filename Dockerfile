FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install pipenv

WORKDIR /app

COPY . .

RUN pipenv install --system --deploy

ENV PYTHONPATH=/app

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "-c"]

CMD ["alembic upgrade head && hypercorn src.main:app --bind 0.0.0.0:8000"]
