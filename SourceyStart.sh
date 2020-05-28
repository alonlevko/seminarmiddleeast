#!/bin/sh
gunicorn --env DJANGO_SETTINGS_MODULE=pythondjangoapp.settings.development pythondjangoapp.wsgi -b 0.0.0.0:$PORT --timeout 0