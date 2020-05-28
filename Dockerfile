FROM python:3.7.7-alpine3.10

RUN apk update
RUN apk add make automake gcc g++ subversion python3-dev

WORKDIR /app

COPY Pipfile* /app/

RUN pip install --upgrade pip \
  && pip install --upgrade pipenv \
  && pipenv install --system --deploy

COPY . /app

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--env", "DJANGO_SETTINGS_MODULE=pythondjangoapp.settings.development", "pythondjangoapp.wsgi", "--timeout 120"]
