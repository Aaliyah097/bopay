FROM python:3.11-alpine

RUN pip install pipenv

WORKDIR /app

COPY . .

RUN pipenv install --system --deploy

ENV PYTHONPATH=/app

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "-c"]

CMD ["alembic upgrade head && hypercorn src.main:app --bind 0.0.0.0:8000"]
