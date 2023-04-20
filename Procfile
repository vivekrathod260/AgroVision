web: gunicorn AuthenticationLogin.wsgi --timeout 60 --keep-alive 5 --log-level debug
python manage.py collectstatic --noinput
manage.py migrate