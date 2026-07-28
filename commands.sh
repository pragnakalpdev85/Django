# Apply migrations
cd Book_Library_System/library
python manage.py migrate --noinput 

gunicorn --bind 0.0.0.0:8000 --workers 3 library.wsgi:application --access-logfile - --error-logfile - &

wait