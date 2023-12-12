FROM python:3.10-slim

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y libpq-dev python3-dev
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN alembic upgrade head

CMD [ "python", "__main__.py"]