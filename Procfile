release: cd backend && python manage.py collectstatic --no-input && python manage.py migrate
web: cd backend && gunicorn devpro.wsgi --log-file -
